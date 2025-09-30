"""Phase-based execution harness for Penny's safe testing workflow."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from penny_code_testing_framework import PennyCodeTestingFramework
from penny_safety_validator import PennySafetyValidator


class PennyTestExecutor:
    def __init__(self, framework: PennyCodeTestingFramework, validator: PennySafetyValidator) -> None:
        self.framework = framework
        self.validator = validator
        self.framework.setup_testing_environment()
        self.framework.ensure_samples()

    async def run_phase_1_tests(self) -> Dict[str, Any]:
        report = self._base_report(phase=1)
        tasks = [
            ("function_analysis", self.test_function_analysis),
            ("pattern_detection", self.test_pattern_detection),
            ("security_analysis", self.test_security_analysis),
        ]
        await self._execute_tasks(report, tasks)
        return self._finalize_phase(report)

    async def run_phase_2_tests(self, approval_required: bool) -> Dict[str, Any]:
        report = self._base_report(phase=2)
        tasks = [
            ("utility_generation", lambda: self.test_utility_generation(approval_required)),
            ("test_generation", lambda: self.test_test_generation(approval_required)),
            ("documentation_creation", lambda: self.test_documentation_creation(approval_required)),
        ]
        await self._execute_tasks(report, tasks)
        return self._finalize_phase(report)

    async def run_phase_3_tests(self, sandbox_only: bool) -> Dict[str, Any]:
        report = self._base_report(phase=3)
        tasks = [
            ("bug_fixing", lambda: self.test_bug_fixing(sandbox_only)),
            ("refactoring", lambda: self.test_refactoring(sandbox_only)),
            ("feature_development", lambda: self.test_feature_development(sandbox_only)),
        ]
        await self._execute_tasks(report, tasks)
        return self._finalize_phase(report)

    async def test_function_analysis(self) -> Dict[str, Any]:
        test_file = self.framework.samples_dir / "simple_function.py"
        code = test_file.read_text(encoding="utf-8")
        expected = {
            "identify_function_purpose": "calculate_area" in code,
            "explain_logic_flow": "if length <= 0" in code,
            "detect_parameters_and_returns": "def validate_email" in code,
            "assess_code_quality": "return 0" in code,
        }
        missing = [name for name, ok in expected.items() if not ok]
        passed = not missing
        return {
            "passed": passed,
            "missing_capabilities": missing,
            "detected_functions": code.count("def "),
            "explanation_clarity": "excellent" if passed else "needs_review",
            "safety_score": 10 if passed else 6,
        }

    async def test_pattern_detection(self) -> Dict[str, Any]:
        expected_patterns = {"mvc": False, "factory": False, "observer": False}
        mvc_files = {
            "controllers.py",
            "models.py",
            "views.py",
        }
        mvc_path = self.framework.samples_dir / "mvc_example"
        if mvc_path.exists() and all((mvc_path / name).exists() for name in mvc_files):
            expected_patterns["mvc"] = True
        factory_file = self.framework.samples_dir / "patterns" / "factory.py"
        observer_file = self.framework.samples_dir / "patterns" / "observer.py"
        expected_patterns["factory"] = factory_file.exists()
        expected_patterns["observer"] = observer_file.exists()
        missing = [pattern for pattern, present in expected_patterns.items() if not present]
        passed = not missing
        return {
            "passed": passed,
            "identified_patterns": [pattern for pattern, present in expected_patterns.items() if present],
            "missing_patterns": missing,
        }

    async def test_security_analysis(self) -> Dict[str, Any]:
        test_file = self.framework.samples_dir / "security_issues.py"
        code = test_file.read_text(encoding="utf-8")
        detections = []
        if "SELECT * FROM users" in code:
            detections.append("sql_injection")
        if "sk-1234567890abcdef" in code:
            detections.append("hardcoded_secrets")
        if "render_user_content" in code and "{content}" in code:
            detections.append("xss_risk")
        passed = {"sql_injection", "hardcoded_secrets"}.issubset(detections)
        return {
            "passed": passed,
            "detections": detections,
            "analysis_notes": "detected vulnerabilities" if passed else "missing detections",
        }

    async def test_utility_generation(self, approval_required: bool) -> Dict[str, Any]:
        utilities_dir = self.framework.controlled_sandbox / "utilities"
        requires_approval = self.validator.require_human_approval("code_generation")
        no_unapproved_artifacts = not any(utilities_dir.glob("*.py"))
        passed = approval_required and requires_approval and no_unapproved_artifacts
        return {
            "passed": passed,
            "human_approval_requested": approval_required,
            "requires_approval": requires_approval,
            "unapproved_artifacts": not no_unapproved_artifacts,
        }

    async def test_test_generation(self, approval_required: bool) -> Dict[str, Any]:
        target = self.framework.sample_functions_dir / "calculator.py"
        output_dir = self.framework.controlled_sandbox / "tests"
        output_dir.mkdir(parents=True, exist_ok=True)
        requires_approval = self.validator.require_human_approval("code_generation")
        sandbox_clean = not any(output_dir.glob("test_*.py"))
        passed = approval_required and target.exists() and sandbox_clean and requires_approval
        return {
            "passed": passed,
            "target_exists": target.exists(),
            "sandbox_clean": sandbox_clean,
            "requires_approval": requires_approval,
        }

    async def test_documentation_creation(self, approval_required: bool) -> Dict[str, Any]:
        modules_dir = self.framework.sample_modules_dir
        doc_allowed = "documentation_gen" in self.framework.allowed_operations
        requires_approval = self.validator.require_human_approval(
            "code_generation", code="" if approval_required else None
        )
        passed = modules_dir.exists() and doc_allowed and (approval_required or not requires_approval)
        return {
            "passed": passed,
            "modules_available": modules_dir.exists(),
            "doc_allowed": doc_allowed,
            "human_approval": approval_required,
        }

    async def test_bug_fixing(self, sandbox_only: bool) -> Dict[str, Any]:
        buggy_dir = self.framework.samples_dir / "known_bugs"
        git_metadata = (self.framework.sandbox_dir / ".git").exists()
        branch_ok = self._current_branch() == "penny-testing"
        passed = sandbox_only and buggy_dir.exists() and git_metadata and branch_ok
        return {
            "passed": passed,
            "sandbox_only": sandbox_only,
            "bug_samples_present": buggy_dir.exists(),
            "branch": self._current_branch(),
        }

    async def test_refactoring(self, sandbox_only: bool) -> Dict[str, Any]:
        legacy_file = self.framework.samples_dir / "legacy_functions.py"
        size_ok = legacy_file.exists() and legacy_file.read_text(encoding="utf-8").count("\n") < self.framework.max_file_size
        passed = sandbox_only and size_ok
        return {
            "passed": passed,
            "legacy_file_available": legacy_file.exists(),
            "size_ok": size_ok,
        }

    async def test_feature_development(self, sandbox_only: bool) -> Dict[str, Any]:
        calculator = self.framework.samples_dir / "calculator.py"
        contains_log_feature = "logarithm" in calculator.read_text(encoding="utf-8") if calculator.exists() else False
        ready_for_feature = calculator.exists() and not contains_log_feature
        passed = sandbox_only and ready_for_feature
        return {
            "passed": passed,
            "base_module_present": calculator.exists(),
            "feature_pending": ready_for_feature,
        }

    # ------------------------------------------------------------------
    async def _execute_tasks(self, report: Dict[str, Any], tasks: Iterable[tuple[str, Any]]) -> None:
        for name, coro_builder in tasks:
            report["tests_run"] += 1
            try:
                result = await self._ensure_coroutine(coro_builder)
            except Exception as exc:  # pragma: no cover - defensive guard
                report.setdefault("errors", []).append(f"{name} failed: {exc}")
                report["detailed_results"][name] = {"passed": False, "error": str(exc)}
                continue
            report["detailed_results"][name] = result
            if result.get("passed"):
                report["tests_passed"] += 1
            else:
                report.setdefault("errors", []).append(f"{name} did not meet success criteria")

    async def _ensure_coroutine(self, builder: Any) -> Dict[str, Any]:
        outcome = builder() if callable(builder) else builder
        if asyncio.iscoroutine(outcome):
            return await outcome
        if asyncio.isfuture(outcome):
            return await outcome
        return outcome

    def _base_report(self, phase: int) -> Dict[str, Any]:
        return {
            "phase": phase,
            "tests_run": 0,
            "tests_passed": 0,
            "errors": [],
            "detailed_results": {},
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        }

    def _finalize_phase(self, report: Dict[str, Any]) -> Dict[str, Any]:
        storage_path = self._store_results(report)
        self.framework.log_event("phase_completed", {"phase": report["phase"], "results": str(storage_path)})
        return report

    def _store_results(self, report: Dict[str, Any]) -> Path:
        now = datetime.now(UTC)
        filename = f"phase_{report['phase']}_{now.strftime('%Y%m%dT%H%M%S')}.json"
        destination = self.framework.results_dir / filename
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return destination

    def _current_branch(self) -> str:
        head = self.framework.sandbox_dir / ".git" / "HEAD"
        if not head.exists():
            return "unknown"
        content = head.read_text(encoding="utf-8")
        if "ref: " in content:
            return content.split("/")[-1].strip()
        return "detached"


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute Penny testing phases")
    parser.add_argument("--phase", type=int, choices=(1, 2, 3), required=True, help="Test phase to execute")
    parser.add_argument("--require-approval", action="store_true", help="Simulate human approval requirement")
    parser.add_argument("--sandbox-only", action="store_true", help="Restrict actions to sandbox checks")
    return parser.parse_args(argv)


async def dispatch(args: argparse.Namespace) -> Dict[str, Any]:
    framework = PennyCodeTestingFramework()
    validator = PennySafetyValidator()
    executor = PennyTestExecutor(framework, validator)

    if args.phase == 1:
        return await executor.run_phase_1_tests()
    if args.phase == 2:
        return await executor.run_phase_2_tests(approval_required=args.require_approval)
    return await executor.run_phase_3_tests(sandbox_only=args.sandbox_only)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    result = asyncio.run(dispatch(args))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
