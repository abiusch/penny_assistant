"""Focused tests for the code generation tool server with Docker sandbox integration."""

import asyncio
from datetime import datetime

import pytest

from code_generation_tool_server import (
    CodeExecutionSandbox,
    CodeGenerationEngine,
    CodeGenerationToolServer,
    create_code_generation_server,
)


class MockSecurityComponent:
    """Simple mock for security components."""

    def __init__(self, allow_all: bool = True, emergency_active: bool = False):
        self.allow_all = allow_all
        self.emergency_active = emergency_active
        self.events = []

    async def is_command_allowed(self, command):
        return self.allow_all

    def is_emergency_active(self):
        return self.emergency_active

    async def log_security_event(self, event_type, details):
        self.events.append({"event": event_type, "details": details})

    async def create_checkpoint(self, checkpoint_id):
        return f"checkpoint_{checkpoint_id}"

    async def check_rate_limit(self, user_id, operation):
        return self.allow_all


class StubContainerManager:
    """Deterministic stand-in for DockerSecurityContainerManager."""

    def __init__(self):
        self.security_components = {}
        self.last_execution = None

    async def containerized_code_execution(self, code_content, **kwargs):
        self.last_execution = {"code": code_content, **kwargs}

        if "while True" in code_content:
            return {
                "success": False,
                "stdout": "",
                "stderr": "timeout exceeded",
                "return_code": 1,
                "execution_time": kwargs.get("timeout", 1),
            }

        return {
            "success": True,
            "stdout": "Result: 5\n",
            "stderr": "",
            "return_code": 0,
            "execution_time": 0.05,
        }


def run_async(coro):
    return asyncio.run(coro)


def test_code_execution_sandbox_safe_run():
    sandbox = CodeExecutionSandbox(StubContainerManager(), max_execution_time=5.0)

    async def runner():
        async with sandbox:
            result = await sandbox.execute_code("print('hi')")
            assert result["success"] is True
            assert result["output"].strip()

    run_async(runner())


def test_code_execution_sandbox_security_validation():
    sandbox = CodeExecutionSandbox(StubContainerManager())

    async def runner():
        async with sandbox:
            issues = await sandbox.validate_code_security("import os\nos.system('echo hi')")
            assert issues["valid"] is False
            assert any("Dangerous import" in issue for issue in issues["issues"])

    run_async(runner())


def test_code_generation_engine_templates():
    engine = CodeGenerationEngine()

    async def runner():
        result = await engine.generate_code(
            "Create a helper function",
            code_type="function",
            style_preferences={"function_name": "helper"},
        )
        assert result["success"] is True
        assert "def helper" in result["code"]

        analysis = await engine.analyze_existing_code(result["code"], "structure")
        assert analysis["success"] is True
        assert analysis["analysis"]["functions"]

    run_async(runner())


def test_server_executes_code_with_stub_manager():
    security_components = {
        "whitelist": MockSecurityComponent(),
        "emergency": MockSecurityComponent(),
        "logger": MockSecurityComponent(),
        "rollback": MockSecurityComponent(),
        "rate_limiter": MockSecurityComponent(),
    }

    stub_manager = StubContainerManager()

    async def runner():
        server = await create_code_generation_server(
            security_components,
            container_manager=stub_manager,
        )

        try:
            result = await server.execute_code_sandboxed(
                "print('sandbox test')",
                timeout=5,
                user_id="tester",
            )

            assert result.success is True
            assert result.data["output"].strip()
            assert stub_manager.last_execution is not None
            assert stub_manager.last_execution["timeout"] == 5

        finally:
            await server.stop()

    run_async(runner())


def test_container_manager_receives_security_components():
    security_components = {
        "whitelist": MockSecurityComponent(),
        "emergency": MockSecurityComponent(),
        "logger": MockSecurityComponent(),
        "rollback": MockSecurityComponent(),
        "rate_limiter": MockSecurityComponent(),
        "A1_command_whitelist": MockSecurityComponent(),
    }

    stub_manager = StubContainerManager()

    async def runner():
        server = CodeGenerationToolServer(container_manager=stub_manager)
        await server.initialize_security_components(
            whitelist_system=security_components["whitelist"],
            emergency_system=security_components["emergency"],
            security_logger=security_components["logger"],
            rollback_system=security_components["rollback"],
            rate_limiter=security_components["rate_limiter"],
            additional_components=security_components,
        )

        assert "whitelist" in stub_manager.security_components
        assert "A1_command_whitelist" in stub_manager.security_components

    run_async(runner())
