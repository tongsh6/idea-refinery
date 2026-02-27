from __future__ import annotations

from typing import Any

TECH_SPEC_REQUIRED_SECTIONS: list[str] = [
    "overview",
    "architecture",
    "components",
    "api_contracts",
    "data_model",
    "non_functional_requirements",
    "risks",
    "milestones",
    "open_questions",
]


def validate_tech_spec_coverage(content: dict[str, Any]) -> tuple[float, list[str]]:
    missing: list[str] = []
    for section in TECH_SPEC_REQUIRED_SECTIONS:
        val = content.get(section)
        if not val or (isinstance(val, list) and len(val) == 0) or val == "":
            missing.append(section)
    present = len(TECH_SPEC_REQUIRED_SECTIONS) - len(missing)
    coverage = present / len(TECH_SPEC_REQUIRED_SECTIONS)
    return coverage, missing
