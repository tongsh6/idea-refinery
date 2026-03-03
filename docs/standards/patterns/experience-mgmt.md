# 跨切面模式：三层经验管理（Experience Management）

> 将 `context/experience/` 的目录结构升级为可检索、可沉淀的管理模式。

## 概述

三层经验管理模式将经验知识组织为**索引层 → 文档层 → 摘要层**的三层结构，配合相关度计算和自动沉淀机制，实现经验的高效复用。

### 与现有 context/experience/ 的关系

```
现有 context/experience/：
  提供了目录结构（INDEX.md + lessons/ + reports/）
  ↓ 经验管理模式增值
  索引可检索 → 相关度排序 → 自动沉淀
```

经验管理模式不改变现有目录结构，而是增加使用策略和自动化机制。

### IdeaRefinery 当前经验资产

已有 3 条经验（lessons/）和 1 份审计报告（reports/），涵盖：
- AIEF 初始化决策
- 多供应商路由与 fallback 设计
- 长链路实现的节奏控制与可观测性

## 三层架构

### 第一层：索引层（Index）

**文件**：`context/experience/INDEX.md`

索引层是经验的**入口和导航**，提供快速检索能力。

**IdeaRefinery 的索引格式**（已在 INDEX.md 中使用）：

```markdown
# 经验索引

## 按领域分类

### Orchestrator（编排器）
| 关键词 | 文档 | 摘要 |
|--------|------|------|
| provider-retry, pipeline, observability | [session-retrospective.md](...) | 阶段化 DoD + preflight + 运行指标复盘 |

### Provider（供应商接入）
| 关键词 | 文档 | 摘要 |
|--------|------|------|
| multi-provider, role-routing, fallback | [multi-provider-routing.md](...) | 统一配置入口并明确路由/回退契约 |

### Gate（质量门）
| 关键词 | 文档 | 摘要 |
|--------|------|------|
| （待沉淀） | - | - |

### Store（持久化）
| 关键词 | 文档 | 摘要 |
|--------|------|------|
| （待沉淀） | - | - |

### Exporter（导出器）
| 关键词 | 文档 | 摘要 |
|--------|------|------|
| （待沉淀） | - | - |

### GUI（工作台）
| 关键词 | 文档 | 摘要 |
|--------|------|------|
| （待沉淀） | - | - |
```

**关键设计**：
- 每条索引包含**关键词**（支持中英文）、**文档链接**、**一句话摘要**
- 按 IdeaRefinery 六大领域分组：Orchestrator、Provider、Gate、Store、Exporter、GUI
- 关键词支持模糊匹配

### 第二层：文档层（Documents）

**目录**：`context/experience/lessons/`

文档层存储**完整的经验记录**，使用 `_template.md` 模板。

**IdeaRefinery 的文档命名约定**（已在使用）：

```
lessons/
  YYYY-MM-DD-{slug}.md    # 按日期 + 主题slug命名
  _template.md             # 新经验的模板
```

### 第三层：摘要层（Summaries）

**目录**：`context/experience/summaries/`（当前为可选，待经验积累后启用）

摘要层为**高频领域**提供聚合摘要，避免 AI 需要加载大量单独文档。

**IdeaRefinery 摘要文件规划**：

```
summaries/
  orchestrator.md     # 编排器领域经验汇总（累计 ≥ 5 条时生成）
  provider.md         # 供应商接入经验汇总
  gate.md             # 质量门经验汇总
  ...
```

**触发摘要生成的条件**：某领域累计 ≥ 5 条经验时，建议生成摘要。

## 相关度计算

当 AI 执行 IdeaRefinery 开发任务时，从索引中检索相关经验的算法：

### 评分模型

```
相关度 = 关键词匹配(40%) + 领域匹配(30%) + 任务类型匹配(30%)
```

| 维度 | 权重 | 计算方式 |
|------|------|---------|
| 关键词匹配 | 40% | 任务描述中包含索引关键词的比例 |
| 领域匹配 | 30% | 任务涉及的 IdeaRefinery 领域（Orchestrator/Provider/Gate/Store/Exporter/GUI）与经验领域是否一致 |
| 任务类型匹配 | 30% | 任务类型（新功能/修复/重构）与经验类别（设计决策/踩坑记录/Bug修复）是否匹配 |

### 阈值

| 相关度 | 行为 |
|--------|------|
| ≥ 0.7 | **强相关**：自动加载完整经验文档 |
| 0.4 - 0.7 | **可能相关**：展示摘要，询问是否加载 |
| < 0.4 | **不相关**：不加载 |

### IdeaRefinery 示例

```
任务："接入 Moonshot 作为新的 OpenAI-compatible Provider，支持 role-routing"

关键词提取：provider, moonshot, openai-compatible, role-routing, 接入
领域推断：Provider
任务类型：新功能

索引匹配：
  multi-provider-routing.md
    关键词匹配：provider(✓) role-routing(✓) → 2/5 = 0.4 → × 0.4 = 0.16
    领域匹配：Provider = Provider → 1.0 → × 0.3 = 0.30
    类型匹配：新功能 vs 设计决策 → 0.7 → × 0.3 = 0.21
    总分：0.67 → 可能相关，展示摘要

  session-retrospective.md
    关键词匹配：provider-retry(部分✓) pipeline(✗) → 0.5/5 = 0.1 → × 0.4 = 0.04
    领域匹配：Orchestrator ≠ Provider → 0.3 → × 0.3 = 0.09
    类型匹配：新功能 vs 踩坑记录 → 0.5 → × 0.3 = 0.15
    总分：0.28 → 不相关，不加载
```

## 自动沉淀机制

### 触发条件

IdeaRefinery 开发任务完成后，AI 应评估是否需要沉淀经验：

| 信号 | 沉淀优先级 | IdeaRefinery 具体场景 |
|------|-----------|---------------------|
| 任务中遇到了意外问题 | 高 | Provider 连接超时、Gate 评分异常、Schema 不兼容 |
| 使用了非显而易见的解决方案 | 高 | CR 闭环的特殊处理、Pydantic v2 迁移技巧 |
| 发现了文档未覆盖的边界情况 | 中 | Ollama 本地部署的配置差异、SQLite 并发限制 |
| 任务耗时超过预期 | 中 | 联调多 Provider 时的调试耗时 |
| 任务顺利完成，无特殊情况 | 低（不沉淀） | 常规文档更新、简单配置调整 |

### 沉淀流程

```
任务完成 → 评估沉淀价值 → 生成经验草稿 → 更新索引 → 人工确认（可选）
```

具体步骤：
1. 在 `lessons/` 下创建 `YYYY-MM-DD-{slug}.md`（使用 `_template.md`）
2. 在 `context/experience/INDEX.md` 的对应领域分组下追加索引条目
3. 在按类别索引中追加条目
4. 若为阶段性复盘，同时创建 `reports/` 审计报告

### 索引更新规则

新经验沉淀后，自动追加到 INDEX.md 的对应领域分组下。如果领域不存在，创建新分组。

## 实施指南

### 最小实现

1. 在 `context/experience/INDEX.md` 中按上述格式维护索引（✅ 已完成）
2. 在 AGENTS.md 的知识库中引用本模式的相关度计算规则
3. 每次任务后评估是否需要沉淀（L3 要求：每个重要变更至少一条）

### 渐进采纳

| 级别 | 实现方式 | 适用场景 |
|------|---------|---------|
| 基础 | INDEX.md 手动维护 + 关键词匹配 | L1 项目 |
| 进阶 | 相关度评分 + 自动沉淀建议 | L2 项目 |
| 完整 | 三层结构 + 摘要生成 + 自动沉淀 | L3 项目（当前目标） |

## 与其他模式的协作

- **阶段路由模式**：Phase Router 在 implement 阶段前触发经验检索
- **上下文加载模式**：经验是 5 层上下文中的第 3 层（经验层）

## 参考

- [context/experience/INDEX.md](../../../context/experience/INDEX.md) — 经验索引
- [context/experience/lessons/_template.md](../../../context/experience/lessons/_template.md) — 经验文档模板
- [context/experience/reports/_template.md](../../../context/experience/reports/_template.md) — 审计报告模板
- [上下文加载模式](context-loading.md) — 上下文加载策略
- [阶段路由模式](phase-router.md) — 触发经验检索的路由机制
