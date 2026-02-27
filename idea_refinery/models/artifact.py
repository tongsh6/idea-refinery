"""Artifact domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ArtifactType = Literal["PRD", "TECH_SPEC", "EXEC_PLAN"]


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Artifact(BaseModel):
    """Versioned document produced by the pipeline."""

    id: str = Field(default_factory=_uid)
    run_id: str
    artifact_type: ArtifactType
    version: int = 1
    content: dict[str, Any] = Field(default_factory=dict)  # Structured sections
    raw_text: str = ""  # Markdown / raw text representation
    summary: str = ""  # Auto-generated summary (populated after edit)
    diff_summary: str = ""  # What changed from previous version
    previous_artifact_id: str | None = None
    schema_coverage: float = 0.0  # 0-1, fraction of required sections present
    created_at: datetime = Field(default_factory=_now)
