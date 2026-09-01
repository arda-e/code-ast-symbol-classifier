"""Show how far the staged work has got, and what to do next.

    make progress

A wall of 34 failures says nothing about where to start. This runs each stage on
its own and prints them in order, so there is always exactly one obvious next
command.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = PROJECT_ROOT / "tests" / "spec"

STAGES = [
    ("1", "test_stage1_split.py", "split identifiers into words", "features/lexical.py"),
    ("2", "test_stage2_lexical.py", "label words with their source", "features/lexical.py"),
    ("3", "test_stage3_numeric.py", "lay facts out in contract order", "features/numeric.py"),
    ("4", "test_stage4_build.py", "join and scale the two blocks", "features/build.py"),
    ("5", "test_stage5_train.py", "fit the classifier", "model/train.py"),
]

BAR_WIDTH = 12


@dataclass(frozen=True)
class StageResult:
    number: str
    title: str
    module: str
    filename: str
    passed: int
    total: int

    @property
    def complete(self) -> bool:
        return self.total > 0 and self.passed == self.total

    @property
    def bar(self) -> str:
        if self.total == 0:
            return "?" * BAR_WIDTH
        filled = round(BAR_WIDTH * self.passed / self.total)
        return "█" * filled + "·" * (BAR_WIDTH - filled)


def run_stage(number: str, filename: str, title: str, module: str) -> StageResult:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(SPEC_DIR / filename),
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    passed = _count(completed.stdout, "passed")
    failed = _count(completed.stdout, "failed")
    return StageResult(number, title, module, filename, passed, passed + failed)


def _count(output: str, word: str) -> int:
    match = re.search(rf"(\d+) {word}", output)
    return int(match.group(1)) if match else 0


def main() -> int:
    results = [
        run_stage(number, filename, title, module) for number, filename, title, module in STAGES
    ]

    print()
    for stage in results:
        mark = "done" if stage.complete else "    "
        print(
            f"  stage {stage.number}  {stage.bar}  {stage.passed:>2}/{stage.total:<2} {mark}  "
            f"{stage.title:<34} {stage.module}"
        )

    passed = sum(stage.passed for stage in results)
    total = sum(stage.total for stage in results)
    print(f"\n  {passed}/{total} specifications met")

    remaining = next((stage for stage in results if not stage.complete), None)
    if remaining is None:
        print(
            "\n  Every stage is complete. Run `make evaluate` and `make ablate` for real numbers.\n"
        )
        return 0

    print(
        f"\n  Next: uv run pytest tests/spec/{remaining.filename}\n"
        f"        The file starts with what you are building and why. "
        f"Write it in {remaining.module}.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
