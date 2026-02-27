from __future__ import annotations

from ..models import ArtifactType
from ..providers.base import Message

EDITOR_SYSTEM = """\
You are a senior editor.
Your job is to apply Change Requests (CRs) to the artifact and output an updated artifact.

RULES:
1. You MUST resolve every CR with one of: ACCEPT / REJECT / DEFER, and give a reason.
2. Apply all ACCEPTed CRs to the artifact content.
3. If you REJECT/DEFER a CR, do NOT change the artifact for that CR.
4. Output ONLY valid JSON. No prose outside JSON.

OUTPUT JSON SCHEMA:
{
  "updated_artifact": { ... full artifact JSON ... },
  "changelog": "string (what changed)",
  "cr_resolutions": [
    {
      "cr_id": "string",
      "status": "ACCEPT|REJECT|DEFER",
      "note": "string"
    }
  ]
}
"""


def build_editor_prompt(
    idea: str,
    artifact_json: str,
    crs_json: str,
    artifact_type: ArtifactType,
    round_number: int,
) -> list[Message]:
    messages = [Message(role="system", content=EDITOR_SYSTEM)]

    user_content = f"""\
## TASK: Apply CRs and update the {artifact_type} (Round {round_number})

### Original Idea
{idea}

### Current Artifact (JSON)
{artifact_json}

### Change Requests (JSON)
{crs_json}

Apply the CRs and return the updated artifact JSON with resolutions and a changelog.
"""

    messages.append(Message(role="user", content=user_content))
    return messages
