"""Safety validation utilities for Penny's controlled testing workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class PennySafetyValidator:
    def __init__(self) -> None:
        self.dangerous_operations = [
            "os.system",
            "subprocess.call",
            "exec",
            "eval",
            "open(",
            "__import__",
            "file.write",
            "shutil.rmtree",
        ]
        self.max_complexity_score = 10
        self.max_function_lines = 50

    def validate_generated_code(self, code: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "safe": True,
            "warnings": [],
            "errors": [],
            "risk_level": "low",
        }

        for pattern in self.dangerous_operations:
            if pattern in code:
                result["errors"].append(f"Dangerous operation detected: {pattern}")
                result["safe"] = False
                result["risk_level"] = "high"

        lines = [line.rstrip() for line in code.splitlines() if line.strip()]
        if len(lines) > self.max_function_lines:
            result["warnings"].append(f"Code too long: {len(lines)} lines")
            result["risk_level"] = "medium"

        import_statements = [line for line in lines if line.startswith("import ") or line.startswith("from ")]
        if import_statements:
            result["warnings"].append(f"Imports detected: {import_statements}")
            if result["risk_level"] == "low":
                result["risk_level"] = "medium"

        return result

    def require_human_approval(self, operation: str, code: str | None = None) -> bool:
        high_risk = {
            "code_generation",
            "file_modification",
            "system_interaction",
            "external_api_calls",
        }
        if operation in high_risk:
            return True
        if code and not self.validate_generated_code(code).get("safe", False):
            return True
        return False

    def serialize_profile(self, destination: Path) -> None:
        profile = {
            "dangerous_operations": self.dangerous_operations,
            "max_complexity_score": self.max_complexity_score,
            "max_function_lines": self.max_function_lines,
        }
        destination.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safety validations for generated code")
    parser.add_argument("--init", action="store_true", help="Write default safety profile next to validator")
    parser.add_argument("--validate", type=Path, help="Validate the specified code file")
    parser.add_argument(
        "--output", type=Path, help="Optional path to store validation results as JSON"
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    validator = PennySafetyValidator()

    if args.init:
        profile_path = Path("penny_code_testing") / "safety_profile.json"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        validator.serialize_profile(profile_path)
        print(f"Wrote safety profile to {profile_path}")

    validation_result: Dict[str, Any] | None = None
    if args.validate:
        if not args.validate.exists():
            print(f"File not found: {args.validate}")
            return 2
        validation_result = validator.validate_generated_code(
            args.validate.read_text(encoding="utf-8")
        )
        print(json.dumps(validation_result, indent=2))

    if args.output and validation_result is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(validation_result, indent=2), encoding="utf-8")

    if not any((args.init, args.validate)):
        print("No action requested. Use --help for available commands.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
