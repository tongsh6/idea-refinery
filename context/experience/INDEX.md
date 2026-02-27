# 经验索引

> 项目经验的可检索入口。实现类任务开始前，先检索此索引，加载相关经验，避免重复踩坑。

## 使用说明

1. 提取任务关键词
2. 匹配下方条目的关键词
3. 加载对应 `lessons/` 文档
4. 执行完成后更新索引与报告

---

## 经验列表（按时间倒序）

### 多供应商路由与 fallback 的最小可用落地

- **类别**：设计决策
- **日期**：2026-02-27
- **关键词**：`multi-provider`, `role-routing`, `fallback`, `openai-compatible`, `config-contract`
- **摘要**：统一了多供应商配置入口（CLI+ENV），支持 role 优先路由和顺序 fallback，形成可复制接入契约。
- **文档**：`lessons/2026-02-27-multi-provider-routing.md`

### 会话复盘：长链路实现的节奏控制与可观测性

- **类别**：踩坑记录
- **日期**：2026-02-27
- **关键词**：`AIEF`, `session-retrospective`, `provider-retry`, `ollama`, `pipeline`, `observability`
- **摘要**：本次会话问题集中在阶段边界不清、外部依赖波动和持久化边界；沉淀了分阶段 DoD、联调 preflight、持久化与指标复盘规范。
- **文档**：`lessons/2026-02-27-session-retrospective.md`

### 项目初始化采用 AIEF 最小入口

- **类别**：设计决策
- **日期**：2026-02-26
- **关键词**：`AIEF`, `init`, `AGENTS`, `context`
- **摘要**：采用 `AGENTS.md + context/INDEX.md + business/tech/experience` 作为最小可用入口，便于后续经验复利。
- **文档**：`lessons/2026-02-26-aief-init.md`

---

## 按类别索引

### 踩坑记录

| 经验 | 关键词 | 摘要 |
|------|--------|------|
| 长链路实现的节奏控制与可观测性 | `provider-retry`, `pipeline`, `observability` | 阶段化 DoD + preflight + 运行指标复盘 |

### 设计决策

| 经验 | 关键词 | 摘要 |
|------|--------|------|
| 多供应商路由与 fallback 最小落地 | `multi-provider`, `role-routing`, `fallback` | 统一配置入口并明确路由/回退契约 |
| AIEF 最小入口初始化 | `AIEF`, `AGENTS`, `context` | 统一项目级 AI 协作入口，减少上下文漂移 |

---

## 审计报告

| 报告 | 日期 | 范围 | 摘要 |
|------|------|------|------|
| [会话审计：初始化到真实联调](reports/2026-02-27-session-audit.md) | 2026-02-27 | AIEF 初始化、流水线、联调、验证 | 识别阶段节奏/依赖稳定性/持久化边界问题并完成修复 |

---

## 新增经验约定

1. 在 `lessons/` 新增 `YYYY-MM-DD-*.md`
2. 在本索引追加条目（关键词必须可检索）
3. 若为阶段性复盘，补充 `reports/` 审计报告
