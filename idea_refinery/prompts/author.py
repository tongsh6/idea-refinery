from __future__ import annotations

from ..models import ArtifactType
from ..providers.base import Message

PRD_SYSTEM = """\
You are an expert product manager and technical writer.
Your job is to produce a structured, actionable Product Requirements Document (PRD).

RULES:
1. Every section must be filled with concrete, specific content.
2. Goals must be measurable.
3. Milestones must each have a Definition of Done checklist.
4. Risks must include mitigation strategies.
5. Output ONLY valid JSON.

REQUIRED JSON KEYS:
tldr, problem_statement, target_users, goals, non_goals,
user_stories, functional_requirements, acceptance_criteria,
milestones, risks, open_questions, version
"""

TECH_SPEC_SYSTEM = """\
You are a senior software architect.
Your job is to produce a structured TECH_SPEC in JSON.

RULES:
1. Be specific and implementation-oriented.
2. Include architecture choices and API/data contracts.
3. Include non-functional requirements and risks.
4. Output ONLY valid JSON.

REQUIRED JSON KEYS:
overview, architecture, components, api_contracts,
data_model, non_functional_requirements, risks,
milestones, open_questions, version
"""

EXEC_PLAN_SYSTEM = """\
You are a delivery manager.
Your job is to produce a structured EXEC_PLAN in JSON.

RULES:
1. Break work into milestones and concrete tasks.
2. Include owners, timeline, dependencies and risks.
3. Include clear acceptance criteria.
4. Output ONLY valid JSON.

REQUIRED JSON KEYS:
objective, scope, milestones, tasks, owners,
timeline, dependencies, risks, acceptance_criteria, version
"""


def _system_prompt(artifact_type: ArtifactType) -> str:
    if artifact_type == "PRD":
        return PRD_SYSTEM
    if artifact_type == "TECH_SPEC":
        return TECH_SPEC_SYSTEM
    return EXEC_PLAN_SYSTEM


def build_author_prompt(
    idea: str,
    artifact_type: ArtifactType,
    previous_artifact: str | None = None,
    editor_changelog: str | None = None,
) -> list[Message]:
    messages = [Message(role="system", content=_system_prompt(artifact_type))]

    if previous_artifact and editor_changelog:
        user_content = f"""\
## TASK: Produce an improved {artifact_type}

### Original Idea
{idea}

### Previous Artifact (JSON)
{previous_artifact}

### Editor Changelog
{editor_changelog}

Incorporate accepted changes and output full updated JSON.
"""
    else:
        user_content = f"""\
## TASK: Draft a {artifact_type} for the following idea

### Idea
{idea}

Output complete JSON for {artifact_type}. No prose outside JSON.
"""

    messages.append(Message(role="user", content=user_content))
    return messages
