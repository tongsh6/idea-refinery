"""PRD (Product Requirements Document) schema definition."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Required top-level sections in a valid PRD
PRD_REQUIRED_SECTIONS: list[str] = [
    "tldr",
    "problem_statement",
    "target_users",
    "goals",
    "non_goals",
    "user_stories",
    "functional_requirements",
    "acceptance_criteria",
    "milestones",
    "risks",
    "open_questions",
]


class Milestone(BaseModel):
    name: str
    description: str
    target_date: str = ""  # ISO 8601 or descriptive (e.g. "Week 2")
    dod: list[str] = Field(default_factory=list)  # Definition of Done checklist


class Risk(BaseModel):
    description: str
    likelihood: str = ""  # high / medium / low
    impact: str = ""
    mitigation: str = ""


class UserStory(BaseModel):
    as_a: str
    i_want: str
    so_that: str
    acceptance: list[str] = Field(default_factory=list)


class PRDSection(BaseModel):
    """Full structured PRD."""

    # 1. TL;DR
    tldr: str = ""

    # 2. Problem
    problem_statement: str = ""

    # 3. Users
    target_users: list[str] = Field(default_factory=list)

    # 4. Goals (measurable)
    goals: list[str] = Field(default_factory=list)

    # 5. Non-goals
    non_goals: list[str] = Field(default_factory=list)

    # 6. User stories
    user_stories: list[UserStory] = Field(default_factory=list)

    # 7. Functional requirements
    functional_requirements: list[dict[str, Any]] = Field(default_factory=list)

    # 8. Acceptance criteria
    acceptance_criteria: list[str] = Field(default_factory=list)

    # 9. Milestones
    milestones: list[Milestone] = Field(default_factory=list)

    # 10. Risks
    risks: list[Risk] = Field(default_factory=list)

    # 11. Open questions
    open_questions: list[str] = Field(default_factory=list)

    # Optional metadata
    version: str = "0.1"
    author: str = ""
    date: str = ""

    model_config = ConfigDict(extra="allow")


def validate_prd_coverage(content: dict[str, Any]) -> tuple[float, list[str]]:
    """
    Return (coverage_ratio, missing_sections).
    coverage_ratio is 0.0-1.0.
    """
    missing = []
    for section in PRD_REQUIRED_SECTIONS:
        val = content.get(section)
        if not val or (isinstance(val, list) and len(val) == 0) or val == "":
            missing.append(section)
    present = len(PRD_REQUIRED_SECTIONS) - len(missing)
    coverage = present / len(PRD_REQUIRED_SECTIONS)
    return coverage, missing
