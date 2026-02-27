from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from ..models import ArtifactType


def _list(items: list[str]) -> str:
    if not items:
        return "- (empty)"
    return "\n".join([f"- {item}" for item in items])


def _to_list_str(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _to_dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(item)
    return out


def prd_to_markdown(prd: Mapping[str, object]) -> str:
    sections: list[str] = []
    sections.append(f"# PRD v{prd.get('version', '0.1')}")
    sections.append("## TL;DR\n" + str(prd.get("tldr", "")))
    sections.append("## 问题陈述\n" + str(prd.get("problem_statement", "")))
    sections.append("## 目标用户\n" + _list(_to_list_str(prd.get("target_users"))))
    sections.append("## 目标\n" + _list(_to_list_str(prd.get("goals"))))
    sections.append("## 非目标\n" + _list(_to_list_str(prd.get("non_goals"))))

    stories = _to_dict_list(prd.get("user_stories"))
    if stories:
        story_lines: list[str] = []
        for s in stories:
            story_lines.append(
                f"- 作为 {s.get('as_a')}，我想要 {s.get('i_want')}，以便 {s.get('so_that')}"
            )
            for a in _to_list_str(s.get("acceptance")):
                story_lines.append(f"  - 验收：{a}")
        sections.append("## 用户故事\n" + "\n".join(story_lines))
    else:
        sections.append("## 用户故事\n- (empty)")

    frs = _to_dict_list(prd.get("functional_requirements"))
    if frs:
        fr_lines: list[str] = []
        for fr in frs:
            fr_lines.append(f"- {fr.get('id')} {fr.get('title')} ({fr.get('priority')})")
            fr_lines.append(f"  - {fr.get('description')}")
        sections.append("## 功能需求\n" + "\n".join(fr_lines))
    else:
        sections.append("## 功能需求\n- (empty)")

    sections.append("## 验收标准\n" + _list(_to_list_str(prd.get("acceptance_criteria"))))

    milestones = _to_dict_list(prd.get("milestones"))
    if milestones:
        ms_lines: list[str] = []
        for m in milestones:
            ms_lines.append(f"- {m.get('name')} ({m.get('target_date')})")
            ms_lines.append(f"  - {m.get('description')}")
            for d in _to_list_str(m.get("dod")):
                ms_lines.append(f"  - DoD: {d}")
        sections.append("## 里程碑\n" + "\n".join(ms_lines))
    else:
        sections.append("## 里程碑\n- (empty)")

    risks = _to_dict_list(prd.get("risks"))
    if risks:
        risk_lines: list[str] = []
        for r in risks:
            risk_lines.append(
                f"- {r.get('description')} (L:{r.get('likelihood')} I:{r.get('impact')})"
            )
            risk_lines.append(f"  - 缓解：{r.get('mitigation')}")
        sections.append("## 风险\n" + "\n".join(risk_lines))
    else:
        sections.append("## 风险\n- (empty)")

    sections.append("## 未决问题\n" + _list(_to_list_str(prd.get("open_questions"))))
    metadata = {"author": prd.get("author"), "date": prd.get("date")}
    sections.append("## 元信息\n" + json.dumps(metadata, ensure_ascii=False))
    return "\n\n".join(sections).strip() + "\n"


def tech_spec_to_markdown(spec: Mapping[str, object]) -> str:
    sections: list[str] = []
    sections.append(f"# TECH_SPEC v{spec.get('version', '0.1')}")
    sections.append("## 概览\n" + str(spec.get("overview", "")))
    sections.append("## 架构\n" + str(spec.get("architecture", "")))
    sections.append("## 组件\n" + _list(_to_list_str(spec.get("components"))))
    sections.append("## API 合约\n" + _list(_to_list_str(spec.get("api_contracts"))))
    sections.append("## 数据模型\n" + _list(_to_list_str(spec.get("data_model"))))
    sections.append(
        "## 非功能需求\n" + _list(_to_list_str(spec.get("non_functional_requirements")))
    )
    sections.append("## 风险\n" + _list(_to_list_str(spec.get("risks"))))
    sections.append("## 里程碑\n" + _list(_to_list_str(spec.get("milestones"))))
    sections.append("## 未决问题\n" + _list(_to_list_str(spec.get("open_questions"))))
    return "\n\n".join(sections).strip() + "\n"


def exec_plan_to_markdown(plan: Mapping[str, object]) -> str:
    sections: list[str] = []
    sections.append(f"# EXEC_PLAN v{plan.get('version', '0.1')}")
    sections.append("## 目标\n" + str(plan.get("objective", "")))
    sections.append("## 范围\n" + _list(_to_list_str(plan.get("scope"))))
    sections.append("## 里程碑\n" + _list(_to_list_str(plan.get("milestones"))))
    sections.append("## 任务\n" + _list(_to_list_str(plan.get("tasks"))))
    sections.append("## 负责人\n" + _list(_to_list_str(plan.get("owners"))))
    sections.append("## 时间线\n" + _list(_to_list_str(plan.get("timeline"))))
    sections.append("## 依赖\n" + _list(_to_list_str(plan.get("dependencies"))))
    sections.append("## 风险\n" + _list(_to_list_str(plan.get("risks"))))
    sections.append("## 验收标准\n" + _list(_to_list_str(plan.get("acceptance_criteria"))))
    return "\n\n".join(sections).strip() + "\n"


def artifact_to_markdown(artifact_type: ArtifactType, content: Mapping[str, object]) -> str:
    if artifact_type == "PRD":
        return prd_to_markdown(content)
    if artifact_type == "TECH_SPEC":
        return tech_spec_to_markdown(content)
    return exec_plan_to_markdown(content)


def default_filename(artifact_type: ArtifactType) -> str:
    if artifact_type == "PRD":
        return "PRD.md"
    if artifact_type == "TECH_SPEC":
        return "TECH_SPEC.md"
    return "EXEC_PLAN.md"


def write_markdown(content: str, output_dir: str, filename: str) -> str:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(content, encoding="utf-8")
    return str(path)
