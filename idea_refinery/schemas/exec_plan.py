from __future__ import annotations

from typing import Any

EXEC_PLAN_REQUIRED_SECTIONS: list[str] = [
    "objective",
    "scope",
    "milestones",
    "tasks",
    "owners",
    "timeline",
    "dependencies",
    "risks",
    "acceptance_criteria",
]


def validate_exec_plan_coverage(content: dict[str, Any]) -> tuple[float, list[str]]:
    missing: list[str] = []
    for section in EXEC_PLAN_REQUIRED_SECTIONS:
        val = content.get(section)
        if not val or (isinstance(val, list) and len(val) == 0) or val == "":
            missing.append(section)
    present = len(EXEC_PLAN_REQUIRED_SECTIONS) - len(missing)
    coverage = present / len(EXEC_PLAN_REQUIRED_SECTIONS)
    return coverage, missing
