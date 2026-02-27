# 技术架构说明（IdeaRefinery OSS v0.x）

## 目标
- 提供可控的“方案精炼”流水线：Draft → Review → Edit → Gate → Stop/Loop。
- 支持多供应商模型（OpenAI-compatible + Ollama）与插件扩展。
- 以 CR 闭环与 Gate 为核心质量门禁，形成可回放证据链。

## 总体架构
核心组件：
- Orchestrator（状态机编排）：负责阶段流转与 Loop 控制。
- Router（模型路由）：根据角色/预算/策略选择 provider。
- Provider Plugins：OpenAI-compatible 与 Ollama。
- Prompt/Schema Library：产物 schema + 角色 prompts 版本化。
- Store：SQLite（OSS），负责 Run/Round/Artifact/CR/Decision 持久化。
- Gate/Evaluator：规则门禁与评分门禁。
- Exporter：Markdown/PDF（OSS 默认 Markdown）。

## 关键流程（文字数据流）
Idea → (Optional) Diverge → Select
→ Author(PRD v0.1)
→ Reviewer(多帽子)
→ Editor(v0.2)
→ Gate
→ Pass → TECH_SPEC pipeline → EXEC_PLAN pipeline → Export
→ Fail → Loop（换帽子/换模型/加强约束）直到 Stop

## Loop 与 CR 闭环
- Reviewer 必须输出结构化 CR（problem/rationale/change/acceptance/severity）。
- Editor 必须逐条处理 CR：ACCEPT/REJECT/DEFER + 理由，并更新正文。
- Gate 规则：Blocking CR 未关闭不得进入下一阶段。

## Gate 规则（默认）
- 章节缺失 → FAIL
- Blocking CR 未关闭 → FAIL
- avgScore ≥ 8 且 Blocking = 0 → PASS
- 连续 2 轮无新增 Blocking → STOP（收敛）
- 预算/轮次/超时 → STOP（硬停）

## 成本与上下文治理
- 章节级投喂：Reviewer 只看关键章节（TL;DR/目标/里程碑/风险/验收/变更摘要）。
- diff 摘要：Editor 产出 changelog，下一轮优先喂 diff + 摘要。
- 预算感知路由：发散/初审用本地或低成本模型，整合/裁判用高质量模型。
- 失败退避：provider 限流/错误 → 自动 fallback。

## 领域模型（核心表）
- Run(id, idea, config, status, cost, created_at)
- Round(id, run_id, step, role, provider, model, prompt_ref, input_ref, output_ref, tokens, cost, latency)
- Artifact(id, run_id, type, version, content, summary, diff, created_at)
- Review(id, round_id, hat, verdict, scores_json, blocking_count)
- CR(id, artifact_id, round_id, severity, dimension, change, acceptance, status)
- Decision(id, round_id, decision, reason, stop_reason)

## 模型与 Provider 约定
- OpenAI-compatible：使用 chat completions 协议，支持 messages/usage/choices 等基础字段。
- Ollama：本地推理，成本默认为 0。
- Provider 需输出 token 使用量与延迟，以便成本统计与 Gate 决策。

## 供应商接入策略（新增）
- 接入优先级：先接 OpenAI-compatible 端点，再补原生插件。
- 目标供应商：Gemini、Claude、GLM、MiniMax、Kimi 等。
- 兼容模式：若供应商提供 OpenAI-compatible 网关，可直接复用 `OpenAICompatibleProvider`。
- 原生模式：若为非兼容 API，通过实现 `BaseProvider` 新增插件。
- 友好性要求：
  - 单供应商接入只需配置 `base_url/api_key/model`
  - 多供应商并存可通过 role map 与 candidate 顺序实现路由/fallback

### 插件接入最小接口
- `complete(req: CompletionRequest) -> CompletionResult`
- `estimate_cost(input_tokens, output_tokens, model) -> float`

### 可靠性与可观测要求
- Provider 失败必须支持重试与 fallback（避免单点供应商中断流程）。
- Run/Round 维度需记录 provider、model、tokens、latency、cost。
- 详细接入流程与验收清单见：`context/tech/provider-integration.md`

## 产物与导出
- 产物先结构化 JSON（schema 驱动）。
- 导出层负责将 JSON 渲染为 Markdown/PDF（OSS 默认 Markdown）。

## 非目标（v0.x）
- 不实现全功能 RAG 平台；仅保留检索接口与引用插槽。
- 不强制“所有模型一致通过”作为默认停机条件。

## 质量与可回放
- 每轮提示、输出、CR 状态、评分、停机原因、成本指标均可追溯。
