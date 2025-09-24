"""Docker-backed secure container management for Penny's code execution."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

try:  # pragma: no cover - docker may be unavailable in test environments
    import docker
    from docker.errors import APIError, DockerException, ImageNotFound, NotFound
except Exception:  # pragma: no cover - fall back if docker SDK missing
    docker = None  # type: ignore
    APIError = DockerException = ImageNotFound = NotFound = Exception  # type: ignore


LOGGER = logging.getLogger("docker_security_container")


class DockerSecurityError(RuntimeError):
    """Raised when a security policy violation occurs."""


class DockerRuntimeError(RuntimeError):
    """Raised when container lifecycle management fails."""


DEFAULT_MEMORY_LIMIT = "128m"
DEFAULT_CPU_PERIOD = 100_000
DEFAULT_CPU_QUOTA = 50_000
DEFAULT_TIMEOUT = 30
DEFAULT_TMPFS_SIZE = "size=10m"
DEFAULT_IMAGE = "penny-code-runner:latest"
DEFAULT_LABEL_KEY = "penny_code_execution"

DEFAULT_ULIMITS: List[Dict[str, int | str]] = [
    {"name": "nofile", "soft": 64, "hard": 64},
    {"name": "nproc", "soft": 16, "hard": 16},
]

DEFAULT_SECURITY_POLICIES: Dict[str, Any] = {
    "max_memory_bytes": 256 * 1024 * 1024,
    "max_cpu_quota": 80_000,
    "max_cpu_period": 100_000,
    "max_timeout_seconds": 60,
    "max_processes": 16,
    "allow_read_only": True,
    "allow_network": False,
    "allowed_tmpfs_paths": {"/tmp"},
    "require_labels": True,
}


@dataclass
class ContainerMetadata:
    """Tracks container lifecycle metadata for auditing and cleanup."""

    container_id: str
    created_at: float = field(default_factory=time.time)
    timeout: int = DEFAULT_TIMEOUT
    parameters: Dict[str, Any] = field(default_factory=dict)


def _memory_to_bytes(value: Any) -> int:
    """Convert docker-style memory limit strings into bytes."""

    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        raise DockerSecurityError(f"Unsupported memory limit format: {value!r}")

    stripped = value.strip().lower()
    multiplier = 1
    if stripped.endswith("k"):
        multiplier = 1024
        stripped = stripped[:-1]
    elif stripped.endswith("m"):
        multiplier = 1024 ** 2
        stripped = stripped[:-1]
    elif stripped.endswith("g"):
        multiplier = 1024 ** 3
        stripped = stripped[:-1]

    try:
        numeric = float(stripped)
    except ValueError as exc:  # pragma: no cover - defensive
        raise DockerSecurityError(f"Invalid memory value: {value}") from exc

    return int(numeric * multiplier)


class DockerSecurityContainerManager:
    """Manages secure Docker containers for executing generated code."""

    def __init__(
        self,
        base_image: str = DEFAULT_IMAGE,
        dockerfile_path: Optional[Path] = None,
        docker_context_path: Optional[Path] = None,
        security_components: Optional[Dict[str, Any]] = None,
        resource_defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.base_image = base_image
        self.dockerfile_path = Path(dockerfile_path) if dockerfile_path else None
        self.docker_context_path = Path(docker_context_path) if docker_context_path else (
            self.dockerfile_path.parent if self.dockerfile_path else None
        )
        self.security_components = security_components or {}
        self.resource_defaults = resource_defaults or {}
        self.active_containers: Dict[str, ContainerMetadata] = {}
        self._security_policies = DEFAULT_SECURITY_POLICIES.copy()
        self._resource_template = self._build_resource_template()

        self._client = None
        if docker is not None:
            try:
                self._client = docker.from_env()  # type: ignore[attr-defined]
            except DockerException as exc:  # pragma: no cover - depends on environment
                LOGGER.warning("Docker client unavailable: %s", exc)
                self._client = None

        self._register_emergency_listener()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def create_code_container(
        self,
        code_content: str,
        timeout: int = DEFAULT_TIMEOUT,
        resource_limits: Optional[Dict[str, Any]] = None,
        network_enabled: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a container primed with the supplied code."""

        await self._validate_operation("create", {
            "timeout": timeout,
            "network_enabled": network_enabled,
            "metadata": metadata or {},
        })

        config = self._prepare_container_config(resource_limits, network_enabled, timeout)
        await self.validate_container_config(config, self._security_policies)

        client = self._require_client()
        await self._ensure_image(client)

        container = await self._run_in_executor(
            client.containers.create,
            self.base_image,
            command=["python", "/workspace/run_code.py"],
            detach=True,
            labels={DEFAULT_LABEL_KEY: "true"},
            **config,
        )

        container_id: str = container.id
        await self._inject_code(container, code_content)
        self.active_containers[container_id] = ContainerMetadata(
            container_id=container_id,
            timeout=timeout,
            parameters={"metadata": metadata or {}, "network_enabled": network_enabled},
        )

        await self.audit_container_operation(container_id, "create", {"timeout": timeout})
        return container_id

    async def execute_in_container(
        self,
        container_id: str,
        execution_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the prepared container and collect results."""

        execution_params = execution_params or {}
        await self._validate_operation("execute", {"container_id": container_id})

        container = await self._get_container(container_id)
        metadata = self.active_containers.get(container_id)
        timeout = metadata.timeout if metadata else DEFAULT_TIMEOUT

        start_time = time.time()
        await self._run_in_executor(container.start)

        try:
            exit_status = await asyncio.wait_for(
                self._run_in_executor(container.wait),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            await self._force_terminate(container)
            raise DockerRuntimeError(f"Container {container_id} timed out after {timeout}s")

        execution_time = time.time() - start_time
        logs = await self._run_in_executor(container.logs, stdout=True, stderr=True)

        stdout, stderr = self._split_logs(logs)
        status_code = exit_status.get("StatusCode", 1) if isinstance(exit_status, dict) else exit_status

        result = {
            "success": status_code == 0,
            "stdout": stdout,
            "stderr": stderr or None,
            "return_code": status_code,
            "execution_time": execution_time,
        }

        await self.audit_container_operation(container_id, "execute", result)
        return result

    async def cleanup_container(self, container_id: str, force: bool = False) -> bool:
        """Remove the specified container."""

        try:
            container = await self._get_container(container_id)
        except DockerRuntimeError:
            return False

        try:
            if force:
                await self._run_in_executor(container.remove, force=True)
            else:
                await self._run_in_executor(container.remove)
        finally:
            self.active_containers.pop(container_id, None)

        await self.audit_container_operation(container_id, "cleanup", {"force": force})
        return True

    async def monitor_container_resources(self, container_id: str) -> Dict[str, Any]:
        """Return a snapshot of container resource usage."""

        container = await self._get_container(container_id)
        stats = await self._run_in_executor(container.stats, stream=False)

        mem_usage = stats.get("memory_stats", {}).get("usage", 0)
        cpu_total = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)

        snapshot = {
            "memory_usage": mem_usage,
            "cpu_usage": cpu_total,
            "pids": stats.get("pids_stats", {}).get("current", 0),
            "timestamp": stats.get("read"),
        }

        await self.audit_container_operation(container_id, "monitor", snapshot)
        return snapshot

    async def enforce_resource_limits(self, container_id: str, limits: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Terminate container if it exceeds configured resource ceilings."""

        limits = limits or {}
        container = await self._get_container(container_id)
        stats = await self._run_in_executor(container.stats, stream=False)

        mem_usage = stats.get("memory_stats", {}).get("usage", 0)
        mem_limit = _memory_to_bytes(limits.get("mem_limit", self._resource_template["mem_limit"]))
        if mem_limit and mem_usage > mem_limit:
            await self._force_terminate(container)
            return f"memory usage {mem_usage} exceeded limit {mem_limit}"

        pids_limit = limits.get("pids_limit", self._resource_template.get("pids_limit"))
        current_pids = stats.get("pids_stats", {}).get("current", 0)
        if isinstance(pids_limit, int) and current_pids > pids_limit:
            await self._force_terminate(container)
            return f"process count {current_pids} exceeded limit {pids_limit}"

        return None

    async def audit_container_operation(self, container_id: str, operation_type: str, result: Dict[str, Any]) -> None:
        """Record container operations with the security logger if present."""

        logger_component = self._get_security_component("logger", "security_logger", "A2_enhanced_logging")
        if not logger_component:
            return

        payload = {
            "container_id": container_id,
            "operation": operation_type,
            "result": result,
            "timestamp": time.time(),
        }

        log_fn = getattr(logger_component, "log_security_event", None) or getattr(logger_component, "log_tool_operation", None)
        if log_fn:
            if asyncio.iscoroutinefunction(log_fn):
                await log_fn(f"container_{operation_type}", payload)
            else:
                maybe_coro = log_fn(f"container_{operation_type}", payload)
                if asyncio.iscoroutine(maybe_coro):
                    await maybe_coro

    async def containerized_code_execution(
        self,
        code_content: str,
        timeout: int = DEFAULT_TIMEOUT,
        resource_limits: Optional[Dict[str, Any]] = None,
        network_enabled: bool = False,
        approval_required: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convenience helper that creates, runs, and cleans up a container."""

        await self._validate_operation("containerized_execution", {
            "approval_required": approval_required,
            "timeout": timeout,
            "metadata": metadata or {},
        })

        container_id = await self.create_code_container(
            code_content,
            timeout=timeout,
            resource_limits=resource_limits,
            network_enabled=network_enabled,
            metadata=metadata,
        )

        try:
            result = await self.execute_in_container(container_id)
            return result
        finally:
            await self.cleanup_container(container_id, force=True)

    async def batch_container_cleanup(self, max_age_minutes: int = 30) -> int:
        """Remove stale containers created by this manager."""

        cutoff = time.time() - (max_age_minutes * 60)
        client = self._require_client()
        containers = await self._run_in_executor(
            client.containers.list,
            all=True,
            filters={"label": DEFAULT_LABEL_KEY},
        )

        removed = 0
        for container in containers:
            metadata = self.active_containers.get(container.id)
            created_at = metadata.created_at if metadata else time.time()
            if created_at <= cutoff:
                await self._run_in_executor(container.remove, force=True)
                self.active_containers.pop(container.id, None)
                removed += 1

        return removed

    async def emergency_stop_all_containers(self) -> None:
        """Terminate all running code execution containers immediately."""

        client = self._require_client()
        containers = await self._run_in_executor(
            client.containers.list,
            filters={"label": DEFAULT_LABEL_KEY},
        )

        for container in containers:
            try:
                await self._force_terminate(container)
                await self._run_in_executor(container.remove, force=True)
            finally:
                self.active_containers.pop(container.id, None)

    async def validate_container_config(self, config: Dict[str, Any], security_policies: Dict[str, Any]) -> None:
        """Ensure container configuration obeys security policies."""

        mem_limit = _memory_to_bytes(config.get("mem_limit"))
        if mem_limit > security_policies["max_memory_bytes"]:
            raise DockerSecurityError("Memory limit exceeds permitted maximum")

        cpu_quota = config.get("cpu_quota", DEFAULT_CPU_QUOTA)
        if cpu_quota and cpu_quota > security_policies["max_cpu_quota"]:
            raise DockerSecurityError("CPU quota exceeds permitted maximum")

        cpu_period = config.get("cpu_period", DEFAULT_CPU_PERIOD)
        if cpu_period and cpu_period > security_policies["max_cpu_period"]:
            raise DockerSecurityError("CPU period exceeds permitted maximum")

        if security_policies.get("allow_read_only") and not config.get("read_only", False):
            raise DockerSecurityError("Container must run with read-only filesystem")

        tmpfs = config.get("tmpfs", {})
        disallowed_tmpfs = set(tmpfs.keys()) - security_policies.get("allowed_tmpfs_paths", set())
        if disallowed_tmpfs:
            raise DockerSecurityError(f"Unauthorized tmpfs mount(s): {', '.join(disallowed_tmpfs)}")

        if security_policies.get("require_labels"):
            labels = config.get("labels", {})
            if DEFAULT_LABEL_KEY not in labels:
                raise DockerSecurityError("Security label missing from container configuration")

        if not security_policies.get("allow_network") and config.get("network_mode") != "none":
            raise DockerSecurityError("Network access is disabled for execution containers")

    async def validate_container_operation(self, operation_type: str, parameters: Dict[str, Any]) -> None:
        """External security validation entry point."""

        await self._validate_operation(operation_type, parameters)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_resource_template(self) -> Dict[str, Any]:
        template = {
            "mem_limit": self.resource_defaults.get("mem_limit", DEFAULT_MEMORY_LIMIT),
            "cpu_period": self.resource_defaults.get("cpu_period", DEFAULT_CPU_PERIOD),
            "cpu_quota": self.resource_defaults.get("cpu_quota", DEFAULT_CPU_QUOTA),
            "network_mode": self.resource_defaults.get("network_mode", "none"),
            "pids_limit": self.resource_defaults.get("pids_limit", 10),
            "read_only": self.resource_defaults.get("read_only", True),
            "tmpfs": self.resource_defaults.get("tmpfs", {"/tmp": DEFAULT_TMPFS_SIZE}),
        }
        template["ulimits"] = self.resource_defaults.get("ulimits", DEFAULT_ULIMITS)
        return template

    def _require_client(self):
        if not self._client:
            raise DockerRuntimeError("Docker client unavailable. Ensure Docker Desktop is running and the python 'docker' package is installed.")
        return self._client

    async def _ensure_image(self, client) -> None:
        try:
            await self._run_in_executor(client.images.get, self.base_image)
        except ImageNotFound:
            if not self.dockerfile_path:
                raise DockerRuntimeError(f"Base image {self.base_image} not found and no Dockerfile provided")
            build_context = self.docker_context_path or self.dockerfile_path.parent
            build_path = str(build_context)
            dockerfile = self.dockerfile_path.name
            LOGGER.info("Building Docker image %s from %s", self.base_image, self.dockerfile_path)
            await self._run_in_executor(
                client.images.build,
                path=build_path,
                dockerfile=dockerfile,
                tag=self.base_image,
                rm=True,
            )

    def _prepare_container_config(self, resource_limits: Optional[Dict[str, Any]], network_enabled: bool, timeout: int) -> Dict[str, Any]:
        config = dict(self._resource_template)
        if resource_limits:
            config.update(resource_limits)

        config.setdefault("network_mode", "bridge" if network_enabled else "none")
        config.setdefault("mem_limit", DEFAULT_MEMORY_LIMIT)
        config.setdefault("cpu_period", DEFAULT_CPU_PERIOD)
        config.setdefault("cpu_quota", DEFAULT_CPU_QUOTA)
        config.setdefault("read_only", True)
        config.setdefault("pids_limit", 10)
        config.setdefault("tmpfs", {"/tmp": DEFAULT_TMPFS_SIZE})

        config["labels"] = {DEFAULT_LABEL_KEY: "true"}

        config["ulimits"] = self._convert_ulimits(config.get("ulimits", DEFAULT_ULIMITS))
        return config

    def _convert_ulimits(self, ulimits: Any) -> List[Any]:  # type: ignore[override]
        if docker is None:
            return ulimits  # pragma: no cover - offline environments
        converted: List[Any] = []
        for limit in ulimits:
            if isinstance(limit, dict):
                converted.append(docker.types.Ulimit(**limit))  # type: ignore[attr-defined]
            else:
                converted.append(limit)
        return converted

    async def _inject_code(self, container, code_content: str) -> None:
        archive_stream = io.BytesIO()
        with tarfile.open(fileobj=archive_stream, mode="w") as tar:
            encoded = code_content.encode("utf-8")
            run_script = tarfile.TarInfo(name="run_code.py")
            run_script.size = len(encoded)
            run_script.mode = 0o640
            tar.addfile(run_script, io.BytesIO(encoded))
        archive_stream.seek(0)
        await self._run_in_executor(container.put_archive, "/workspace", archive_stream.getvalue())

    async def _get_container(self, container_id: str):
        client = self._require_client()
        try:
            return await self._run_in_executor(client.containers.get, container_id)
        except NotFound as exc:
            raise DockerRuntimeError(f"Container {container_id} not found") from exc

    async def _force_terminate(self, container) -> None:
        try:
            await self._run_in_executor(container.stop, timeout=2)
        except APIError:
            await self._run_in_executor(container.kill)

    async def _run_in_executor(self, func: Callable, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def _split_logs(self, logs: bytes) -> Tuple[str, str]:
        text = logs.decode("utf-8", errors="replace") if isinstance(logs, (bytes, bytearray)) else str(logs)
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []
        for line in text.splitlines():
            if line.startswith("STDERR:"):
                stderr_lines.append(line[len("STDERR:"):].lstrip())
            else:
                stdout_lines.append(line)
        return "\n".join(stdout_lines), "\n".join(stderr_lines)

    async def _validate_operation(self, operation_type: str, parameters: Dict[str, Any]) -> None:
        emergency_stop = self._get_security_component("emergency", "emergency_system", "emergency_stop", "A3_emergency_stop")
        if emergency_stop and getattr(emergency_stop, "is_emergency_active", None):
            if emergency_stop.is_emergency_active():
                raise DockerSecurityError("Emergency stop active - container operations blocked")

        whitelist = self._get_security_component("whitelist", "command_whitelist", "A1_command_whitelist")
        if whitelist:
            checker = getattr(whitelist, "is_command_allowed", None) or getattr(whitelist, "check_operation_permission", None)
            if checker:
                allowed = await self._maybe_await(checker, f"container_{operation_type}")
                if not allowed:
                    raise DockerSecurityError("Command whitelist blocked container operation")

        rate_limiter = self._get_security_component("rate_limiter", "resource_control", "B1_process_isolation")
        if rate_limiter and getattr(rate_limiter, "check_rate_limit", None):
            allowed = await self._maybe_await(rate_limiter.check_rate_limit, parameters.get("user_id", "anonymous"), f"container_{operation_type}")
            if not allowed:
                raise DockerSecurityError("Rate limiter blocked container operation")

        risk_assessor = self._get_security_component("risk_assessor", "C2_risk_assessment")
        if risk_assessor and getattr(risk_assessor, "assess_risk", None):
            assessment = await self._maybe_await(risk_assessor.assess_risk, operation_type, parameters)
            if assessment and isinstance(assessment, dict) and assessment.get("blocked"):
                raise DockerSecurityError("Risk assessment blocked container operation")

        await self.audit_container_operation("manager", operation_type, parameters)

    async def _maybe_await(self, func: Callable, *args, **kwargs):
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _get_security_component(self, *names: str) -> Any:
        for name in names:
            if name in self.security_components and self.security_components[name]:
                return self.security_components[name]
        return None

    def _register_emergency_listener(self) -> None:
        emergency = self._get_security_component("emergency", "emergency_system", "emergency_stop", "A3_emergency_stop")
        if not emergency:
            return

        callback = getattr(emergency, "register_emergency_callback", None)
        if not callback:
            return

        async def handle_emergency(*_args, **_kwargs):
            try:
                await self.emergency_stop_all_containers()
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.error("Failed to handle emergency stop for containers: %s", exc)

        def sync_wrapper(*_args, **_kwargs):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(handle_emergency())
            else:
                loop.create_task(handle_emergency())

        try:
            result = callback(sync_wrapper)
            if asyncio.iscoroutine(result):  # pragma: no cover - depends on implementation
                asyncio.create_task(result)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to register emergency callback: %s", exc)


__all__ = [
    "DockerSecurityContainerManager",
    "DockerSecurityError",
    "DockerRuntimeError",
]
