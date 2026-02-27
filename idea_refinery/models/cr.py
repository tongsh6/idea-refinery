"""Change Request (CR) and Review domain models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

CRSeverity = Literal["blocking", "major", "minor", "suggestion"]
CRStatus = Literal["open", "accepted", "rejected", "deferred"]


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class CR(BaseModel):
    """
    A structured change request produced by a Reviewer.
    Reviewers MUST produce CRs — no free-form critique allowed.
    """

    id: str = Field(default_factory=_uid)
    artifact_id: str
    round_id: str
    # CR fields (must-fill)
    problem: str  # What is wrong
    rationale: str  # Why it matters
    change: str  # Concrete change to make
    acceptance: str  # How to verify the change was applied
    severity: CRSeverity
    dimension: str = ""  # e.g. "value", "feasibility", "risk", "execution", "clarity"
    # Editor resolution
    status: CRStatus = "open"
    resolution_note: str = ""
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


class ReviewScores(BaseModel):
    """Dimensional scores (1-10) from a Reviewer."""

    value: float = 0.0
    feasibility: float = 0.0
    risk: float = 0.0
    execution: float = 0.0
    clarity: float = 0.0

    @property
    def average(self) -> float:
        vals = [self.value, self.feasibility, self.risk, self.execution, self.clarity]
        active = [v for v in vals if v > 0]
        return sum(active) / len(active) if active else 0.0


class Review(BaseModel):
    """Full review output from a Reviewer for one round."""

    id: str = Field(default_factory=_uid)
    round_id: str
    artifact_id: str
    hat: str  # Reviewer hat / perspective
    verdict: Literal["PASS", "FAIL"] = "FAIL"
    scores: ReviewScores = Field(default_factory=ReviewScores)
    blocking_count: int = 0
    crs: list[CR] = Field(default_factory=list)
    summary: str = ""
    created_at: datetime = Field(default_factory=_now)
