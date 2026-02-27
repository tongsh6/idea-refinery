# 会话复盘经验：长链路实现的节奏控制与可观测性

> 当需求跨度大（初始化 + 架构落地 + 联调 + 验证）时，必须先做阶段切分和每阶段可验证闭环，否则容易反复返工。

## 背景

本次会话覆盖了从 AIEF 初始化到三阶段流水线联调的完整链路，涉及文档、代码、工具链、外部依赖与测试验证。

- 项目/模块：IdeaRefinery（context + core engine + CLI + provider + tests）
- 时间：2026-02-27
- 影响：交付完整，但中间出现多次中断和回退，拉长了迭代时间

## 问题

### 1) 会话过程存在的问题

#### 症状
- 任务范围在会话中多次扩张，阶段目标不够清晰，导致实现顺序反复调整。
- 外部依赖（Ollama 服务）状态不稳定，真实联调阶段出现断连/拒绝连接。
- 早期缺少“每阶段 smoke test”，导致问题在后段才暴露（如 datetime 序列化）。
- 多次触发辅助 agent/工具调用重试，产生额外噪音。

#### 根因
- 阶段性 DoD 不够硬，先做了大量实现，再做集中验证。
- 对外部服务可用性的前置检查不完整（仅做一次健康检查，不足以覆盖长耗时过程）。
- 持久化边界缺少统一约束（Pydantic 对象写入 JSON 时未统一使用 `mode="json"`）。

### 2) 本次会话可沉淀的内容

#### 可复用工程实践
- 三阶段推进模板：`AIEF 初始化 -> 最小闭环 -> 测试补齐 -> 真实联调 -> 指标复盘`。
- 真实联调前置清单：provider 可用性、模型可用性、预算/轮次、超时、重试策略。
- 持久化规范：所有含 `datetime` 的 Pydantic 模型入 JSON 前使用 `model_dump(mode="json")`。
- 外部调用韧性：provider 级 fallback + provider 内重试 + 退避。
- 成本与性能观测：运行后必须输出 round/token/latency 分解。

#### 流程沉淀
- 每完成一个阶段就执行一次可验证闭环（命令、产物、数据库记录、测试）。
- 对“文档更新/复盘沉淀”建立固定出口：`lessons/` + `reports/` + `INDEX.md`。

## 解决方案

- 建立了三阶段流水线并完成 dry-run 与非 dry-run 跑通。
- 新增/完善了测试集（包括 `run_full_pipeline`）并保持 `pytest` 全绿。
- 修复了真实联调关键问题：
  - SQLite 持久化 datetime JSON 序列化失败
  - provider 调用重试与超时配置不足
  - Ollama 服务中断后的恢复流程

## 教训

### 应该做
- 在每个里程碑结束时做最小可运行验证，而不是最后集中验证。
- 将“外部依赖健康检查”升级为“前置 + 运行中 + 重试后再检查”。
- 统一持久化编码规则，避免模型对象直接入 JSON。

### 不应该做
- 不应在阶段目标未冻结前并行扩展过多功能面。
- 不应把真实联调放在所有开发动作之后才首次执行。

### 检查清单
- [ ] 是否已明确本阶段 DoD（代码、命令、产物、指标）
- [ ] 是否完成 provider 健康检查与模型可用性检查
- [ ] 是否完成至少一条端到端 smoke test
- [ ] 是否记录运行指标（round/tokens/latency/cost/stop_reason）
- [ ] 是否将新增经验写入 `context/experience/INDEX.md`

## 相关

- `context/experience/reports/2026-02-27-session-audit.md`
- `context/tech/ARCHITECTURE.md`
- `tests/test_pipeline.py`

---

**关键词**：`AIEF`, `session-retrospective`, `provider-retry`, `ollama`, `pipeline`, `observability`

**类别**：踩坑记录
