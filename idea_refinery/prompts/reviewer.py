"""Reviewer prompt: produces structured CRs from a specific hat/perspective."""

from __future__ import annotations

from ..models import ArtifactType
from ..providers.base import Message

HAT_DESCRIPTIONS = {
    "value": "Evaluator of business value, user impact, and strategic alignment. Focus: Is this worth building? Will users pay/use it? Is it differentiated?",
    "feasibility": "Technical feasibility expert. Focus: Can this be built with available resources? Are timelines realistic? Are technical risks identified?",
    "risk": "Risk analyst. Focus: What could go wrong? What's missing from the risk register? Are mitigations adequate?",
    "execution": "Execution and delivery expert. Focus: Are milestones concrete? Are DoD items testable? Is the team capable?",
    "devil": "Devil's advocate. Focus: Challenge every assumption. What would kill this product? What's the most likely failure mode?",
}

REVIEWER_SYSTEM = """\
You are a senior expert conducting a structured PRD review.

CRITICAL RULES:
1. You MUST produce structured Change Requests (CRs) — no free-form critique.
2. Each CR must have ALL fields: problem, rationale, change, acceptance, severity, dimension.
3. Severity levels: "blocking" (must fix before next stage), "major" (important), "minor" (nice-to-have), "suggestion".
4. Only mark CRs as "blocking" if the PRD cannot proceed without the fix.
5. Output ONLY valid JSON. No prose outside JSON.
6. If the PRD is good enough to proceed (no blocking issues), set verdict to "PASS".

OUTPUT JSON SCHEMA:
{
  "hat": "string (your reviewer perspective)",
  "verdict": "PASS|FAIL",
  "scores": {
    "value": 1-10,
    "feasibility": 1-10,
    "risk": 1-10,
    "execution": 1-10,
    "clarity": 1-10
  },
  "summary": "string (1-2 sentence overall assessment)",
  "crs": [
    {
      "problem": "string (what is wrong)",
      "rationale": "string (why it matters)",
      "change": "string (specific change to make)",
      "acceptance": "string (how to verify fix)",
      "severity": "blocking|major|minor|suggestion",
      "dimension": "string (value|feasibility|risk|execution|clarity)"
    }
  ]
}
"""


def build_reviewer_prompt(
    idea: str,
    artifact_json: str,
    artifact_type: ArtifactType,
    hat: str,
    round_number: int,
    previous_crs_summary: str | None = None,
) -> list[Message]:
    """Build the message list for the Reviewer role."""
    hat_desc = HAT_DESCRIPTIONS.get(hat, hat)

    messages = [Message(role="system", content=REVIEWER_SYSTEM)]

    previous_context = ""
    if previous_crs_summary:
        previous_context = f"""
### Previous Round CRs (for context — do NOT re-raise already-fixed issues)
{previous_crs_summary}
"""

    user_content = f"""\
## TASK: Review this {artifact_type} from the **{hat.upper()}** perspective

### Your Reviewer Role
{hat_desc}

### Original Idea
{idea}

### Artifact to Review (JSON, Round {round_number})
{artifact_json}
{previous_context}
Review the artifact from your assigned perspective.
Produce CRs for every issue you find — no free-form commentary.
Use severity "blocking" sparingly and only for genuine blockers.
Output your full review as JSON.
"""

    messages.append(Message(role="user", content=user_content))
    return messages
