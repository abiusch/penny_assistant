#!/usr/bin/env python3
"""Safe testing framework bootstrap for Penny's Jedi-level capabilities."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class PennyCodeTestingFramework:
    """Provisioner for the isolated testing environment and support assets."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.test_root = (root or Path.cwd()) / "penny_code_testing"
        self.sandbox_dir = self.test_root / "sandbox"
        self.samples_dir = self.test_root / "test_samples"
        self.sample_functions_dir = self.test_root / "sample_functions"
        self.sample_modules_dir = self.test_root / "sample_modules"
        self.controlled_sandbox = self.test_root / "testing_sandbox"
        self.results_dir = self.test_root / "results"
        self.audit_log = self.test_root / "audit.log"

        self.human_approval_required = True
        self.max_file_size = 1000
        self.allowed_operations = [
            "read_analysis",
            "pattern_detection",
            "security_scan",
            "documentation_gen",
        ]

    # ------------------------------------------------------------------
    # Public API
    def setup_testing_environment(self) -> None:
        self._create_directories()
        self._initialize_git_repo()
        self._ensure_test_branch()
        self.log_event("testing_environment_initialized")

    def ensure_samples(self, overwrite: bool = False) -> List[Path]:
        self._create_directories()
        created_files: List[Path] = []
        for destination, content in self._sample_payloads().items():
            if destination.exists() and not overwrite:
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            created_files.append(destination)
        if created_files:
            self.log_event(
                "test_samples_updated",
                {"files": [str(f.relative_to(self.test_root)) for f in created_files]},
            )
        return created_files

    def status(self) -> Dict[str, bool]:
        snapshot = {
            "test_root": self.test_root.exists(),
            "sandbox_git": (self.sandbox_dir / ".git").exists(),
            "results_dir": self.results_dir.exists(),
            "audit_log": self.audit_log.exists(),
            "sample_files": any(self.samples_dir.glob("**/*.py")),
        }
        self.log_event("status_requested", snapshot)
        return snapshot

    def log_event(self, event: str, details: Optional[Dict[str, object]] = None) -> None:
        self.test_root.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "event": event,
            "details": details or {},
        }
        with self.audit_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    # ------------------------------------------------------------------
    # Internal helpers
    def _create_directories(self) -> None:
        folders = (
            self.test_root,
            self.sandbox_dir,
            self.samples_dir,
            self.sample_functions_dir,
            self.sample_modules_dir,
            self.controlled_sandbox,
            self.results_dir,
        )
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    def _initialize_git_repo(self) -> None:
        git_dir = self.sandbox_dir / ".git"
        if git_dir.exists():
            return
        self._run_git(["init"])
        self._run_git(["config", "user.email", "penny-testing@local"])
        self._run_git(["config", "user.name", "Penny Testing"])
        (self.sandbox_dir / ".gitignore").write_text("*.log\n__pycache__/\n", encoding="utf-8")
        self._run_git(["add", ".gitignore"])
        self._run_git(["commit", "-m", "Initial sandbox setup"])

    def _ensure_test_branch(self) -> None:
        branches = self._run_git(["branch"], capture=True)
        existing = branches.decode().split()
        if "penny-testing" in existing:
            self._run_git(["checkout", "penny-testing"])
        else:
            self._run_git(["checkout", "-b", "penny-testing"])

    def _run_git(self, args: Iterable[str], capture: bool = False) -> bytes:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.sandbox_dir,
            check=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
        return completed.stdout if capture else b""

    def _sample_payloads(self) -> Dict[Path, str]:
        return {
            self.samples_dir / "simple_function.py": (
                "def calculate_area(length, width):\n"
                "    \"\"\"Calculate the area of a rectangle.\"\"\"\n"
                "    if length <= 0 or width <= 0:\n"
                "        return 0\n"
                "    return length * width\n\n"
                "def validate_email(email):\n"
                "    \"\"\"Basic email validation.\"\"\"\n"
                "    return '@' in email and '.' in email\n"
            ),
            self.samples_dir / "security_issues.py": (
                "import sqlite3\n\n"
                "def unsafe_query(user_input):\n"
                "    \"\"\"Vulnerable to SQL injection.\"\"\"\n"
                "    conn = sqlite3.connect('test.db')\n"
                "    query = f\"SELECT * FROM users WHERE name = '{user_input}'\"\n"
                "    return conn.execute(query).fetchall()\n\n"
                "def hardcoded_secret():\n"
                "    return 'sk-1234567890abcdef'\n\n"
                "def render_user_content(content):\n"
                "    \"\"\"Return html without sanitising user input.\"\"\"\n"
                "    return f'<div>{content}</div>'\n"
            ),
            self.samples_dir / "mvc_example" / "controllers.py": (
                "class BaseController:\n"
                "    def handle(self, request):\n"
                "        raise NotImplementedError\n\n"
                "class UserController(BaseController):\n"
                "    def handle(self, request):\n"
                "        return {'view': 'user.html', 'data': request}\n"
            ),
            self.samples_dir / "mvc_example" / "models.py": (
                "class UserModel:\n"
                "    def find_by_id(self, user_id):\n"
                "        return {'id': user_id, 'name': 'Test User'}\n"
            ),
            self.samples_dir / "mvc_example" / "views.py": (
                "def render(template, context):\n"
                "    return template.format(**context)\n"
            ),
            self.samples_dir / "patterns" / "factory.py": (
                "class ShapeFactory:\n"
                "    @staticmethod\n"
                "    def create_shape(shape_type):\n"
                "        if shape_type == 'circle':\n"
                "            return Circle()\n"
                "        if shape_type == 'square':\n"
                "            return Square()\n"
                "        return None\n\n"
                "class Circle:\n"
                "    def draw(self):\n"
                "        return 'circle'\n\n"
                "class Square:\n"
                "    def draw(self):\n"
                "        return 'square'\n"
            ),
            self.samples_dir / "patterns" / "observer.py": (
                "class Observer:\n"
                "    def update(self, value):\n"
                "        self.value = value\n\n"
                "class Subject:\n"
                "    def __init__(self):\n"
                "        self._observers = []\n\n"
                "    def attach(self, observer):\n"
                "        self._observers.append(observer)\n\n"
                "    def notify(self, value):\n"
                "        for observer in self._observers:\n"
                "            observer.update(value)\n"
            ),
            self.samples_dir / "known_bugs" / "off_by_one.py": (
                "def sum_first_n(values, count):\n"
                "    total = 0\n"
                "    for idx in range(count + 1):\n"
                "        total += values[idx]\n"
                "    return total\n"
            ),
            self.samples_dir / "legacy_functions.py": (
                "def legacy_calculation(a, b, c):\n"
                "    result = 0\n"
                "    for value in (a, b, c):\n"
                "        if value:\n"
                "            result += value * 2\n"
                "        else:\n"
                "            result += 1\n"
                "    return result\n"
            ),
            self.samples_dir / "calculator.py": (
                "import math\n\n"
                "def add(a, b):\n"
                "    return a + b\n\n"
                "def subtract(a, b):\n"
                "    return a - b\n\n"
                "def multiply(a, b):\n"
                "    return a * b\n\n"
                "def divide(a, b):\n"
                "    if b == 0:\n"
                "        raise ValueError('division by zero')\n"
                "    return a / b\n"
            ),
            self.sample_functions_dir / "calculator.py": (
                "def add(a, b):\n"
                "    return a + b\n\n"
                "def subtract(a, b):\n"
                "    return a - b\n\n"
                "def multiply(a, b):\n"
                "    return a * b\n\n"
                "def divide(a, b):\n"
                "    if b == 0:\n"
                "        raise ValueError('division by zero')\n"
                "    return a / b\n"
            ),
            self.sample_modules_dir / "__init__.py": "",
            self.sample_modules_dir / "reporting.py": (
                "def build_summary(stats):\n"
                "    return f\"Summary: {stats}\"\n\n"
                "def describe_limits():\n"
                "    return 'All operations remain read-only.'\n"
            ),
            self.controlled_sandbox / "utilities" / "README.md": (
                "# Utilities Sandbox\n\n"
                "Human approval required before adding new utilities.\n"
            ),
            self.controlled_sandbox / "tests" / "README.md": (
                "# Generated Tests\n\n"
                "This directory stores generated test cases after approval.\n"
            ),
        }


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Penny code testing framework helper")
    parser.add_argument("--setup", action="store_true", help="Initialize sandbox and logging")
    parser.add_argument("--create-samples", action="store_true", help="Create safe test samples")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing samples when recreating")
    parser.add_argument("--status", action="store_true", help="Print current framework status")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    framework = PennyCodeTestingFramework()

    if args.setup:
        framework.setup_testing_environment()

    if args.create_samples:
        created = framework.ensure_samples(overwrite=args.overwrite)
        if created:
            print("Created sample files:")
            for path in created:
                print(f" - {path}")
        else:
            print("Sample files already present. Use --overwrite to regenerate.")

    if args.status:
        status = framework.status()
        for key, value in status.items():
            print(f"{key}: {'yes' if value else 'no'}")

    if not any((args.setup, args.create_samples, args.status)):
        print("No action requested. Use --help for available commands.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
