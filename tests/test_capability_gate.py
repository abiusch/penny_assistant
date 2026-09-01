"""Capability-gate baseline for Week 15 (Risk 5: Capability Bypass).

Two halves:

* ``TestExistingGate`` — characterizes what ALREADY works and should pass today:
  registered tools execute through the safety wrappers, unknown tools are refused
  at the orchestrator, and the manifest declares the registered tools.

* ``TestCapabilityInvariant`` — the NEW invariant we have NOT built yet. These are
  ``xfail(strict=True)``: they FAIL today (the drift/bypass genuinely exist) so the
  suite stays green while recording a RED baseline, and they will auto-flip to a
  hard failure the moment the invariant is satisfied — forcing the marker's removal.

Agreed definitions:
  capability   = a discrete action the orchestrator can execute via a registered,
                 safety-wrapped tool in tool_registry.
  enforced set = tools registered (and safety-wrapped) in tool_registry.
  declared set = the tools the manifest presents to the LLM as usable.
  bypass       = declared set != enforced set (over/under-claiming), OR any code
                 path that reaches tool execution without the safety wrapper.

Import via ``src.tools.*`` to match tool_registry's own internal imports, so the
ToolValidationError / ToolRateLimitError classes are the SAME objects it raises
(a different import path would create a second module + different classes).
"""
import asyncio

import pytest

from src.tools.tool_registry import ToolRegistry
from src.tools.tool_orchestrator import ToolOrchestrator, ToolCall
from src.tools.tool_safety import (
    get_safe_tool_wrapper,
    ToolValidationError,
    ToolRateLimitError,
)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    # The safety wrapper is a global singleton with a shared RateLimiter; reset it
    # around every test so rate-limit state can't leak between tests.
    get_safe_tool_wrapper().reset_rate_limits()
    yield
    get_safe_tool_wrapper().reset_rate_limits()


class TestExistingGate:
    """Step 1 — should all PASS today (characterizing the current gate)."""

    def test_registered_tools_are_safety_wrapped(self):
        # Every executable tool in the registry is the WRAPPED function, not the
        # raw ToolImplementations function (proves the validation/rate-limit/
        # timeout wrap chain was applied).
        reg = ToolRegistry(enable_safety=True)
        assert reg.tools, "registry has no tools"
        for name, func in reg.tools.items():
            assert func is not reg._raw_tools[name], (
                f"{name} is the RAW function — not safety-wrapped"
            )

    def test_registered_tool_enforces_input_validation(self):
        # math.calc is sync; a dangerous expression must be rejected by the
        # validation wrapper (the raw function would not raise ToolValidationError).
        reg = ToolRegistry(enable_safety=True)
        with pytest.raises(ToolValidationError):
            reg.tools["math.calc"]({"expression": "import os"})

    def test_registered_tool_enforces_rate_limit(self):
        # Exceeding the per-tool call budget must raise ToolRateLimitError.
        reg = ToolRegistry(enable_safety=True)
        limiter = get_safe_tool_wrapper().rate_limiter
        for _ in range(limiter.max_calls):
            reg.tools["math.calc"]({"expression": "2+2"})
        with pytest.raises(ToolRateLimitError):
            reg.tools["math.calc"]({"expression": "2+2"})

    def test_unknown_tool_is_refused_at_orchestrator(self):
        # An unregistered tool name must be refused at _execute_tool, never run.
        reg = ToolRegistry(enable_safety=True)
        orch = ToolOrchestrator(max_iterations=3)
        reg.register_with_orchestrator(orch)
        call = ToolCall(tool_name="nonexistent.tool", arguments={}, raw_output="")
        result = asyncio.run(orch._execute_tool(call))
        assert "not found in registry" in result

    def test_manifest_declares_the_registered_tools(self):
        # The manifest (what the LLM is shown) must mention each registered tool.
        reg = ToolRegistry(enable_safety=True)
        manifest = reg.get_tool_manifest()
        assert "AVAILABLE TOOLS" in manifest
        for name in reg._raw_tools:
            assert name in manifest, f"{name} missing from the manifest"


def _declared_available(manifest: str, candidate_names) -> set:
    """Tools the manifest presents as USABLE (mentioned and not flagged unavailable)."""
    available = set()
    for name in candidate_names:
        if name not in manifest:
            continue
        idx = manifest.index(name)
        block = manifest[idx: idx + 200].lower()  # the tool's description block
        if "coming soon" in block or "not yet implemented" in block:
            continue
        available.add(name)
    return available


class TestCapabilityInvariant:
    """Step 2 — the NEW invariant (NOT built yet). xfail(strict=True) = RED today."""

    @pytest.mark.xfail(
        strict=True,
        reason="Known drift: code.execute is registered+wrapped (enforced) but the "
               "manifest presents it as 'coming soon' (not declared available). "
               "declared set != enforced set. Not fixed in this PR.",
    )
    def test_declared_available_set_matches_enforced_set(self):
        reg = ToolRegistry(enable_safety=True)
        enforced = set(reg._raw_tools.keys())
        declared = _declared_available(reg.get_tool_manifest(), enforced)
        assert declared == enforced, (
            f"capability drift on {declared ^ enforced}: "
            f"declared(available)={declared} != enforced(registered)={enforced}"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="Bypass path: ToolRegistry(enable_safety=False) exposes the RAW, "
               "unwrapped tools — a code path to tool execution without the safety "
               "wrapper. Safety should be mandatory. Not fixed in this PR.",
    )
    def test_no_unwrapped_tool_execution_path(self):
        # There must be no supported way to obtain executable tools that bypass
        # the safety wrapper. Today enable_safety=False returns the raw functions.
        reg = ToolRegistry(enable_safety=False)
        unwrapped = [n for n, f in reg.tools.items() if f is reg._raw_tools[n]]
        assert not unwrapped, (
            f"safety bypass path: {unwrapped} are raw/unwrapped when "
            f"enable_safety=False"
        )
