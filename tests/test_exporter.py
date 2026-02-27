from typing import cast

from idea_refinery.exporter import prd_to_markdown


def test_prd_to_markdown_contains_key_sections() -> None:
    prd = {
        "version": "0.1",
        "tldr": "demo",
        "problem_statement": "problem",
        "target_users": ["u1"],
        "goals": ["g1"],
        "non_goals": ["ng1"],
        "user_stories": [],
        "functional_requirements": [],
        "acceptance_criteria": ["ac1"],
        "milestones": [],
        "risks": [],
        "open_questions": ["oq1"],
    }
    md = prd_to_markdown(cast(dict[str, object], prd))
    assert "# PRD v0.1" in md
    assert "## TL;DR" in md
    assert "## 验收标准" in md
    assert "ac1" in md
