"""Tests for the Docker security container manager."""

import asyncio
import pytest

import docker_security_container as dsc


@pytest.fixture(autouse=True)
def disable_real_docker(monkeypatch):
    """Ensure tests do not require a real Docker engine."""
    monkeypatch.setattr(dsc, "docker", None)


def test_validate_container_config_rejects_high_memory():
    manager = dsc.DockerSecurityContainerManager()
    config = {
        "mem_limit": "512m",
        "cpu_quota": 50_000,
        "cpu_period": 100_000,
        "read_only": True,
        "tmpfs": {"/tmp": "size=10m"},
        "network_mode": "none",
        "labels": {dsc.DEFAULT_LABEL_KEY: "true"},
    }

    async def operation():
        await manager.validate_container_config(config, manager._security_policies)

    with pytest.raises(dsc.DockerSecurityError):
        asyncio.run(operation())


def test_validate_container_config_enforces_read_only_and_network():
    manager = dsc.DockerSecurityContainerManager()

    config = {
        "mem_limit": "64m",
        "cpu_quota": 40_000,
        "cpu_period": 100_000,
        "read_only": False,
        "tmpfs": {"/tmp": "size=10m"},
        "network_mode": "bridge",
        "labels": {dsc.DEFAULT_LABEL_KEY: "true"},
    }

    async def operation():
        await manager.validate_container_config(config, manager._security_policies)

    with pytest.raises(dsc.DockerSecurityError):
        asyncio.run(operation())


class StubSecurityLogger:
    def __init__(self):
        self.calls = []

    async def log_security_event(self, event_type, details):
        self.calls.append((event_type, details))


def test_audit_container_operation_uses_security_logger():
    logger = StubSecurityLogger()
    manager = dsc.DockerSecurityContainerManager()
    manager.security_components = {"logger": logger}

    async def operation():
        await manager.audit_container_operation("abc", "execute", {"success": True})

    asyncio.run(operation())

    assert logger.calls, "Expected security logger to receive audit event"
    event_type, payload = logger.calls[0]
    assert event_type == "container_execute"
    assert payload["container_id"] == "abc"
