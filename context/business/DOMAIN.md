# 业务领域说明（IdeaRefinery / ConvergeX）

## 定位
- IdeaRefinery：开源“方案精炼引擎”内核，将 idea 收敛为可执行的三件套文档（PRD/TECH_SPEC/EXEC_PLAN）。
- ConvergeX：商业化工作台，提供 Web UI、协作、模板/评测集管理、审计与企业集成。

## 问题与价值
- 痛点：发散无收敛、文档不可验收、风险与执行脱节、复盘不可追溯。
- 价值：产出可验收、可回放、可追溯、可执行的方案文档，支持成本与上下文治理。

## 核心目标（可验收）
- 输入 idea 自动输出 PRD/TECH_SPEC/EXEC_PLAN，结构完整（DoD、里程碑、风险缓解、未决问题）。
- 支持 OpenAI-compatible 端点与 Ollama 原生；其它供应商通过插件扩展。
- 支持多轮 CR 闭环：Reviewer 产出可验收 CR，Editor 合并修订，Gate 判定 Stop/Continue。
- 成本可控：预算/轮次/超时；上下文治理通过摘要、diff、章节裁剪。
- 全链路可回放：每轮提示词、输出、CR 状态、评分、停机原因、成本指标。

## 供应商接入需求（新增）
- 接入目标：支持 Gemini、Claude、GLM、MiniMax、Kimi 等主流供应商。
- 接入原则：优先使用 OpenAI-compatible 协议接入；非兼容协议通过 Provider 插件接入。
- 友好性目标：单供应商接入需最少配置（base_url/api_key/model）；多供应商可并存并支持角色路由。
- 可靠性要求：Provider 失败时必须触发重试与 fallback，避免单点供应商导致流程中断。
- 可观测要求：按供应商统计 tokens/cost/latency，并可回放到 run/round 级别。

### 验收标准（供应商接入）
- AC1：任一 OpenAI-compatible 供应商可在不改业务编排代码的前提下完成接入。
- AC2：非 OpenAI-compatible 供应商可通过实现 BaseProvider 在 1 个插件文件内完成接入。
- AC3：同一 run 支持至少 2 个供应商并存，且可按 role 配置优先级与 fallback 顺序。
- AC4：联调报告可输出按 provider/model 聚合的调用次数、token、延迟与成本。

### 当前能力基线（2026-02-27）
- 已支持多 OpenAI-compatible 供应商并存注册（CLI 与环境变量两种配置入口）。
- 已支持角色优先路由（role->provider）和候选顺序 fallback。
- 已支持真实联调后按 provider/model 聚合输出 tokens/latency 指标。

## 非目标（v0.x）
- 不要求“所有模型一致通过”作为默认停机条件。
- 不强绑定 IDE（Copilot 作为可选插件）。
- 不做全功能 RAG 平台，仅提供检索接口与引用插槽。

## 核心概念
- Loop：Draft → Review → Edit → Gate 循环，直到 Pass/Stop。
- CR（Change Request）：结构化变更请求，必须包含 problem/rationale/change/acceptance/severity。
- Gate：停机门禁，规则可度量（Blocking、评分、预算等）。
- 三件套：PRD / TECH_SPEC / EXEC_PLAN。
- 回放：每轮提示与输出可追溯。

## 用户与场景
- 个人：单一 idea 快速产出可执行方案。
- 团队：评审前自动补齐，评审后 CR 落地，形成决策证据链。
- 企业：审计合规、权限、私有部署、模型网关对接。

## 规则与策略（摘要）
- Gate 规则：章节缺失 → FAIL；Blocking 未关闭 → FAIL；avgScore≥8 且 Blocking=0 → PASS；连续 2 轮无新增 Blocking → STOP。
- 帽子轮换（默认）：价值 → 可行 → 风险 → 执行 → 反方。
- 成本与上下文治理：章节级投喂、diff 摘要、预算感知路由、失败退避。

## 数据与度量
- tokens/cost/latency（按角色/模型/供应商）
- blocking_count、cr_closed_ratio、avg_score、stop_reason
- 产物质量：schema 覆盖率、DoD 存在率、里程碑数量

## 里程碑（技术交付）
- M1：PRD 单文档闭环（Loop+CR+Gate+回放+导出）
- M2：三件套流水线（PRD→TECH→PLAN）
- M3：Provider 插件体系与路由策略
- M4：商业版 UI + 协作 + 模板/评测 + 审计
