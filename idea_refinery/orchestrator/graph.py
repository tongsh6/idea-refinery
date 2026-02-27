from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from collections.abc import Iterable
from typing import Literal, Protocol, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from ..config import RunConfig
from ..exporter import artifact_to_markdown, default_filename, write_markdown
from ..gate import evaluate_gate
from ..models import Artifact, ArtifactType, CR, Decision, Review, Round, Run
from ..models.run import StopReason
from ..models.cr import CRSeverity, ReviewScores
from ..prompts import build_author_prompt, build_editor_prompt, build_reviewer_prompt
from ..providers import ProviderRegistry
from ..providers.base import BaseProvider, CompletionRequest, CompletionResult
from ..schemas.prd import validate_prd_coverage
from ..store import SqliteStore
from ..utils import JSONParseError, parse_json


class RefineryState(TypedDict, total=True):
    idea: str
    artifact_json: str
    crs_json: str
    round_number: int
    avg_score: float
    blocking_count: int
    total_cost_usd: float
    run_start: float
    decision: str
    stop_reason: str | None
    gate_reason: str
    changelog: str


class _InvokableGraph(Protocol):
    def invoke(self, input: RefineryState) -> object: ...


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


def _mock_prd(idea: str) -> dict[str, object]:
    return {
        "tldr": f"{idea} 的最小可行 PRD",
        "problem_statement": "需要将想法收敛为可执行方案",
        "target_users": ["个人", "团队"],
        "goals": ["在预算内收敛输出三件套"],
        "non_goals": ["不构建全功能 RAG"],
        "user_stories": [
            {
                "as_a": "产品负责人",
                "i_want": "用一次运行得到可执行方案",
                "so_that": "减少评审返工",
                "acceptance": ["输出包含 DoD 与里程碑"],
            }
        ],
        "functional_requirements": [
            {
                "id": "FR-001",
                "title": "PRD 生成",
                "description": "生成结构化 PRD JSON",
                "priority": "P0",
            }
        ],
        "acceptance_criteria": ["输出为有效 JSON"],
        "milestones": [
            {
                "name": "M1",
                "description": "完成 PRD 闭环",
                "target_date": "Week 1",
                "dod": ["PRD 输出", "Gate 可判定"],
            }
        ],
        "risks": [
            {
                "description": "输出不收敛",
                "likelihood": "medium",
                "impact": "high",
                "mitigation": "设置最大轮次与 Gate",
            }
        ],
        "open_questions": ["默认 Gate 阈值是否足够"],
        "version": "0.1",
    }


def _mock_tech_spec(idea: str) -> dict[str, object]:
    return {
        "overview": f"{idea} 的技术规格说明",
        "architecture": "分层架构：API/Orchestrator/Store/Exporter",
        "components": ["Orchestrator", "Provider Router", "Store", "Gate"],
        "api_contracts": ["CLI run", "POST /runs", "GET /runs/{id}"],
        "data_model": ["Run", "Round", "Artifact", "Review", "CR", "Decision"],
        "non_functional_requirements": ["可回放", "预算可控", "失败可回退"],
        "risks": ["模型输出不稳定", "成本抖动"],
        "milestones": ["M1 单文档闭环", "M2 三件套流水线"],
        "open_questions": ["多租户阶段何时引入"],
        "version": "0.1",
    }


def _mock_exec_plan(idea: str) -> dict[str, object]:
    return {
        "objective": f"交付 {idea} 的可执行方案",
        "scope": ["闭环编排", "CR 门禁", "导出与回放"],
        "milestones": ["Week1 M1", "Week2 M2", "Week3 M3"],
        "tasks": ["实现编排", "实现 gate", "联调 provider", "验收"],
        "owners": ["PM", "Tech Lead", "Backend"],
        "timeline": ["Day1-Day3", "Day4-Day7"],
        "dependencies": ["模型 API 可用", "数据库可用"],
        "risks": ["不收敛", "预算超限"],
        "acceptance_criteria": ["三份文档产出", "Gate 通过", "日志可回放"],
        "version": "0.1",
    }


def _mock_artifact(artifact_type: ArtifactType, idea: str) -> dict[str, object]:
    if artifact_type == "PRD":
        return _mock_prd(idea)
    if artifact_type == "TECH_SPEC":
        return _mock_tech_spec(idea)
    return _mock_exec_plan(idea)


def _coverage_for_artifact(
    artifact_type: ArtifactType,
    content: dict[str, object],
) -> tuple[float, list[str]]:
    if artifact_type == "PRD":
        return validate_prd_coverage(content)
    if artifact_type == "TECH_SPEC":
        return _validate_coverage(content, TECH_SPEC_REQUIRED_SECTIONS)
    return _validate_coverage(content, EXEC_PLAN_REQUIRED_SECTIONS)


def _validate_coverage(content: dict[str, object], sections: list[str]) -> tuple[float, list[str]]:
    missing: list[str] = []
    for section in sections:
        val = content.get(section)
        if not val or (isinstance(val, list) and len(val) == 0) or val == "":
            missing.append(section)
    present = len(sections) - len(missing)
    coverage = present / len(sections)
    return coverage, missing


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    raise JSONParseError("Expected JSON object", str(value))


def _to_float(value: object) -> float:
    if isinstance(value, (int, float, str)):
        try:
            return float(cast(int | float | str, value))
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _normalize_severity(value: object) -> CRSeverity:
    text = str(value).lower()
    if text == "blocking":
        return cast(CRSeverity, "blocking")
    if text == "major":
        return cast(CRSeverity, "major")
    if text == "minor":
        return cast(CRSeverity, "minor")
    if text == "suggestion":
        return cast(CRSeverity, "suggestion")
    return cast(CRSeverity, "minor")


def _normalize_verdict(value: object) -> Literal["PASS", "FAIL"]:
    text = str(value).upper()
    if text == "PASS":
        return "PASS"
    return "FAIL"


def _normalize_decision(value: object) -> Literal["PASS", "FAIL", "STOP"]:
    text = str(value).upper()
    if text == "PASS":
        return "PASS"
    if text == "STOP":
        return "STOP"
    return "FAIL"


def _normalize_stop_reason(value: object) -> StopReason | None:
    if value is None:
        return None
    text = str(value)
    if text in {
        "pass_gate",
        "converged",
        "max_rounds",
        "budget_exceeded",
        "timeout",
        "manual_stop",
        "error",
    }:
        return cast(StopReason, text)
    return None


def _normalize_review(raw: dict[str, object]) -> Review:
    scores_raw = raw.get("scores")
    if isinstance(scores_raw, dict):
        scores_map: dict[str, object] = {str(k): v for k, v in scores_raw.items()}
    else:
        scores_map = {}

    review_scores = ReviewScores(
        value=_to_float(scores_map.get("value")),
        feasibility=_to_float(scores_map.get("feasibility")),
        risk=_to_float(scores_map.get("risk")),
        execution=_to_float(scores_map.get("execution")),
        clarity=_to_float(scores_map.get("clarity")),
    )

    crs: list[CR] = []
    cr_items = raw.get("crs")
    if isinstance(cr_items, list):
        for item in cr_items:
            if not isinstance(item, dict):
                continue
            crs.append(
                CR(
                    artifact_id="",
                    round_id="",
                    problem=str(item.get("problem", "")),
                    rationale=str(item.get("rationale", "")),
                    change=str(item.get("change", "")),
                    acceptance=str(item.get("acceptance", "")),
                    severity=_normalize_severity(item.get("severity")),
                    dimension=str(item.get("dimension", "")),
                )
            )

    blocking = len([c for c in crs if c.severity == "blocking"])
    return Review(
        round_id="",
        artifact_id="",
        hat=str(raw.get("hat", "")),
        verdict=_normalize_verdict(raw.get("verdict", "FAIL")),
        scores=review_scores,
        blocking_count=blocking,
        crs=crs,
        summary=str(raw.get("summary", "")),
    )


def _assign_cr_ids(crs: Iterable[CR], prefix: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for idx, cr in enumerate(crs, start=1):
        items.append(
            {
                "cr_id": f"{prefix}-{idx:03d}",
                "problem": cr.problem,
                "rationale": cr.rationale,
                "change": cr.change,
                "acceptance": cr.acceptance,
                "severity": cr.severity,
                "dimension": cr.dimension,
            }
        )
    return items


def _complete_sync(provider: BaseProvider, req: CompletionRequest) -> CompletionResult:
    return asyncio.run(provider.complete(req))


def _complete_with_fallback(
    registry: ProviderRegistry,
    role: str,
    req: CompletionRequest,
) -> tuple[CompletionResult, dict[str, object]]:
    last_error: Exception | None = None
    attempts: list[dict[str, object]] = []
    for provider in registry.resolve_candidates(role):
        for attempt in range(3):
            try:
                model = req.model or getattr(provider, "default_model", "")
                next_req = CompletionRequest(
                    messages=req.messages,
                    model=model,
                    temperature=req.temperature,
                    max_tokens=req.max_tokens,
                    response_format=req.response_format,
                    extra=req.extra,
                )
                result = _complete_sync(provider, next_req)
                attempts.append(
                    {
                        "provider": provider.name,
                        "attempt": attempt + 1,
                        "status": "success",
                    }
                )
                used_providers = {str(item["provider"]) for item in attempts}
                metadata: dict[str, object] = {
                    "role": role,
                    "attempt_count": len(attempts),
                    "fallback_used": len(used_providers) > 1,
                    "attempts": attempts,
                }
                return result, metadata
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                attempts.append(
                    {
                        "provider": provider.name,
                        "attempt": attempt + 1,
                        "status": "error",
                        "error": str(exc),
                    }
                )
                if attempt < 2:
                    time.sleep(1 + attempt)
                    continue

    if last_error is None:
        raise RuntimeError("No providers configured")
    raise RuntimeError(f"All providers failed for role '{role}': {last_error}") from last_error


def run_refinery(
    *,
    config: RunConfig,
    registry: ProviderRegistry,
    store: SqliteStore,
    artifact_type: ArtifactType = "PRD",
) -> str:
    run = Run(idea=config.idea, status="running", config_json=config.model_dump_json())
    store.insert_run(run)

    state: RefineryState = {
        "idea": config.idea,
        "artifact_json": "{}",
        "crs_json": "[]",
        "round_number": 0,
        "avg_score": 0.0,
        "blocking_count": 0,
        "total_cost_usd": 0.0,
        "run_start": time.monotonic(),
        "decision": "",
        "stop_reason": None,
        "gate_reason": "",
        "changelog": "",
    }

    def draft_node(state: RefineryState) -> RefineryState:
        if config.dry_run:
            artifact = _mock_artifact(artifact_type, state["idea"])
            state["artifact_json"] = json.dumps(artifact, ensure_ascii=False)
            return state

        messages = build_author_prompt(state["idea"], artifact_type)
        req = CompletionRequest(messages=messages, model="")
        result, retry_meta = _complete_with_fallback(registry, "author", req)
        state["total_cost_usd"] += result.cost_usd

        rnd = Round(
            run_id=run.id,
            step="draft",
            role="author",
            provider_name=result.provider,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            raw_output=result.content,
            metadata=retry_meta,
        )
        store.insert_round(rnd)

        prd_obj = _as_dict(parse_json(result.content))
        state["artifact_json"] = json.dumps(prd_obj, ensure_ascii=False)
        return state

    def review_node(state: RefineryState) -> RefineryState:
        state["round_number"] += 1
        all_crs: list[CR] = []
        score_list: list[float] = []

        if config.dry_run:
            state["avg_score"] = 9.0
            state["blocking_count"] = 0
            state["crs_json"] = json.dumps([], ensure_ascii=False)
            return state

        for hat in config.reviewer_hats:
            messages = build_reviewer_prompt(
                state["idea"],
                state["artifact_json"],
                artifact_type,
                hat,
                state["round_number"],
            )
            req = CompletionRequest(messages=messages, model="")
            result, retry_meta = _complete_with_fallback(registry, f"reviewer:{hat}", req)
            state["total_cost_usd"] += result.cost_usd

            rnd = Round(
                run_id=run.id,
                step="review",
                role=f"reviewer:{hat}",
                provider_name=result.provider,
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                latency_ms=result.latency_ms,
                raw_output=result.content,
                metadata=retry_meta,
            )
            store.insert_round(rnd)

            raw = _as_dict(parse_json(result.content))
            review = _normalize_review(raw)
            review.round_id = rnd.id
            store.insert_review(review)

            for cr in review.crs:
                cr.round_id = rnd.id
                store.insert_cr(cr)

            score_list.append(review.scores.average)
            all_crs.extend(review.crs)

        avg_score = sum(score_list) / len(score_list) if score_list else 0.0
        blocking = len([c for c in all_crs if c.severity == "blocking"])
        state["avg_score"] = avg_score
        state["blocking_count"] = blocking
        state["crs_json"] = json.dumps(
            _assign_cr_ids(all_crs, f"R{state['round_number']}"), ensure_ascii=False
        )
        return state

    def edit_node(state: RefineryState) -> RefineryState:
        if config.dry_run:
            state["changelog"] = "dry-run: no changes"
            return state

        messages = build_editor_prompt(
            state["idea"],
            state["artifact_json"],
            state["crs_json"],
            artifact_type,
            state["round_number"],
        )
        req = CompletionRequest(messages=messages, model="")
        result, retry_meta = _complete_with_fallback(registry, "editor", req)
        state["total_cost_usd"] += result.cost_usd

        rnd = Round(
            run_id=run.id,
            step="edit",
            role="editor",
            provider_name=result.provider,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            raw_output=result.content,
            metadata=retry_meta,
        )
        store.insert_round(rnd)

        raw = _as_dict(parse_json(result.content))
        updated = raw.get("updated_artifact")
        if updated is None:
            updated = raw.get("updated_prd")
        if updated is None:
            updated = {}
        updated_prd = _as_dict(updated) if updated else {}
        state["artifact_json"] = json.dumps(updated_prd, ensure_ascii=False)
        state["changelog"] = str(raw.get("changelog", ""))
        return state

    def gate_node(state: RefineryState) -> RefineryState:
        elapsed = time.monotonic() - state["run_start"]
        timed_out = elapsed >= config.gate.timeout_seconds
        decision = evaluate_gate(
            avg_score=state["avg_score"],
            blocking_count=state["blocking_count"],
            round_number=state["round_number"],
            max_rounds=config.gate.max_rounds,
            min_avg_score=config.gate.min_avg_score,
            max_blocking=config.gate.max_blocking,
            budget_usd=config.gate.budget_usd,
            total_cost_usd=state["total_cost_usd"],
            timed_out=timed_out,
        )
        state["decision"] = decision.decision
        state["stop_reason"] = decision.stop_reason
        state["gate_reason"] = decision.reason
        return state

    def route_after_gate(state: RefineryState) -> Literal["review", "end"]:
        return "end" if state["decision"] in {"PASS", "STOP"} else "review"

    builder = StateGraph(RefineryState)
    _ = builder.add_node("draft", draft_node)
    _ = builder.add_node("review", review_node)
    _ = builder.add_node("edit", edit_node)
    _ = builder.add_node("gate", gate_node)

    _ = builder.add_edge(START, "draft")
    _ = builder.add_edge("draft", "review")
    _ = builder.add_edge("review", "edit")
    _ = builder.add_edge("edit", "gate")
    _ = builder.add_conditional_edges("gate", route_after_gate, {"review": "review", "end": END})

    graph = builder.compile()
    invokable_graph = cast(_InvokableGraph, graph)
    try:
        final_state = cast(RefineryState, invokable_graph.invoke(state))
        prd_obj = _as_dict(parse_json(final_state.get("artifact_json", "{}")))
    except JSONParseError as exc:
        run.status = "failed"
        run.error = exc.message
        run.updated_at = datetime.now(timezone.utc)
        store.update_run(run)
        raise

    coverage, _missing = _coverage_for_artifact(artifact_type, prd_obj)
    previous = store.get_latest_artifact(run.id, artifact_type)
    artifact_version = previous.version + 1 if previous is not None else final_state.get("round_number", 1)

    artifact = Artifact(
        run_id=run.id,
        artifact_type=artifact_type,
        version=artifact_version,
        content=prd_obj,
        raw_text=artifact_to_markdown(artifact_type, prd_obj),
        summary="",
        diff_summary=final_state.get("changelog", ""),
        previous_artifact_id=previous.id if previous is not None else None,
        schema_coverage=coverage,
    )
    store.insert_artifact(artifact)

    output_path = write_markdown(artifact.raw_text, config.output_dir, default_filename(artifact_type))

    decision_value: Literal["PASS", "FAIL", "STOP"] = _normalize_decision(
        final_state.get("decision", "FAIL")
    )
    stop_reason_value: StopReason | None = _normalize_stop_reason(
        final_state.get("stop_reason")
    )

    decision = Decision(
        run_id=run.id,
        round_number=final_state.get("round_number", 0),
        decision=decision_value,
        stop_reason=stop_reason_value,
        avg_score=final_state.get("avg_score", 0.0),
        blocking_count=final_state.get("blocking_count", 0),
        reason=final_state.get("gate_reason", ""),
    )
    store.insert_decision(decision)

    run.status = "done" if final_state.get("decision") in {"PASS", "STOP"} else "failed"
    run.total_rounds = int(final_state.get("round_number", 0))
    run.cost_usd = float(final_state.get("total_cost_usd", 0.0))
    run.stop_reason = stop_reason_value
    run.updated_at = datetime.now(timezone.utc)
    store.update_run(run)

    return output_path


def run_full_pipeline(
    *,
    config: RunConfig,
    registry: ProviderRegistry,
    store: SqliteStore,
) -> dict[ArtifactType, str]:
    outputs: dict[ArtifactType, str] = {}

    prd_path = run_refinery(config=config, registry=registry, store=store, artifact_type="PRD")
    outputs["PRD"] = prd_path

    prd_markdown = Path(prd_path).read_text(encoding="utf-8")
    tech_idea = f"""{config.idea}

Use this PRD as baseline for TECH_SPEC:
{prd_markdown}
"""
    tech_config = config.model_copy(update={"idea": tech_idea})
    tech_path = run_refinery(
        config=tech_config,
        registry=registry,
        store=store,
        artifact_type="TECH_SPEC",
    )
    outputs["TECH_SPEC"] = tech_path

    tech_markdown = Path(tech_path).read_text(encoding="utf-8")
    plan_idea = f"""{config.idea}

Use this TECH_SPEC as baseline for EXEC_PLAN:
{tech_markdown}
"""
    plan_config = config.model_copy(update={"idea": plan_idea})
    plan_path = run_refinery(
        config=plan_config,
        registry=registry,
        store=store,
        artifact_type="EXEC_PLAN",
    )
    outputs["EXEC_PLAN"] = plan_path

    return outputs
