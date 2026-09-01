"""Rendering the ablation table.

Markdown because it lands in a GitHub job summary as often as in a terminal.
"""

from __future__ import annotations

from .row import AblationRow

HEADERS = ("variant", "macro-F1", "coverage", "precision@covered", "samples")


def render(rows: list[AblationRow]) -> str:
    lines = [
        "| " + " | ".join(HEADERS) + " |",
        "|---|---:|---:|---:|---:|",
    ]
    lines += ["| " + " | ".join(row.cells) + " |" for row in rows]
    return "\n".join(lines)
