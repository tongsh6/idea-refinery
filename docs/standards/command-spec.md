# Command 规范标准

> 定义 IdeaRefinery 项目中 Command（用户入口层）的标准格式、编排模式和与 Agent 的区别。

## 概述

Command 是 AIEF 三层架构中的**入口层**，代表用户可直接触发的操作。Command 负责编排 Agent 和 Skill，定义完整的工作流程。

### 定位

```
Command（入口层）→ Agent（决策层）→ Skill（执行层）
^^^^^^^^
当前规范
```

## 标准格式

每个 Command 文档应包含以下章节：

```markdown
# Command: {Name}

## 用法
# 触发方式和参数

## 工作流程
# 阶段列表（含跳过条件）

## 调用链
# 引用的 Agent 和 Skill

## 快速判断规则
# 任务分类逻辑（可选）

## 产出物
# 每个阶段的输出
```

### 必填章节

| 章节 | 必填 | 说明 |
|------|------|------|
| 用法 | 是 | 触发方式、参数、前置条件 |
| 工作流程 | 是 | 有序的阶段列表 |
| 调用链 | 是 | 引用了哪些 Agent 和 Skill |
| 快速判断规则 | 否 | 需要分类的 Command 才需要 |
| 产出物 | 是 | 每个阶段产出什么 |

## IdeaRefinery 的 Command 清单

| Command | 说明 |
|---------|------|
| `refinery run` | 核心命令：输入 idea，执行 Draft→Review→Edit→Gate 循环，输出三件套 |

## 三种编排模式

### 1. 顺序执行（Sequential）

```
阶段 1 → 阶段 2 → 阶段 3 → 完成
```

**适用**：固定流程

### 2. 条件跳过（Conditional Skip）

```
阶段 1 → [条件] → 阶段 2（可跳过）→ 阶段 3 → 完成
```

**适用**：大多数 Command。IdeaRefinery 的 `refinery run` 使用此模式（如 `--dry-run` 跳过实际 Provider 调用）。

### 3. 分支执行（Branch）

```
阶段 1 → [判断] ─→ 路径 A → 完成
                  └→ 路径 B → 完成
```

**适用**：需要分类的 Command

## 完整示例

```markdown
# Command: Refinery Run

## 用法

refinery run --idea "..." --out ./out [--dry-run] [--ollama]

- idea: 输入的 idea 描述（必需）
- out: 输出目录（必需）
- --dry-run: 预演模式，不实际调用 Provider
- --ollama: 使用 Ollama 本地推理

**前置条件**：
- 至少配置一个 Provider（环境变量或 CLI 参数）
- 输出目录可写

## 工作流程

### 阶段 1：PRD Pipeline
- **执行**：Draft(PRD v0.1) → Review(多帽子) → Edit(v0.2) → Gate → Loop/Pass
- **调用**：Orchestrator → Author → Reviewer → Editor → Gate Evaluator
- **输出**：PRD 结构化 JSON + Markdown

### 阶段 2：TECH_SPEC Pipeline
- **跳过条件**：PRD 未通过 Gate（FAIL 且达到 STOP 条件）
- **执行**：同阶段 1 流程，输入为 PRD + idea
- **输出**：TECH_SPEC 结构化 JSON + Markdown

### 阶段 3：EXEC_PLAN Pipeline
- **跳过条件**：TECH_SPEC 未通过 Gate
- **执行**：同阶段 1 流程，输入为 PRD + TECH_SPEC + idea
- **输出**：EXEC_PLAN 结构化 JSON + Markdown

### 阶段 4：导出
- **执行**：调用 `skill-export-markdown`
- **输出**：`out/PRD.md`、`out/TECH_SPEC.md`、`out/EXEC_PLAN.md`

## 调用链

Command: refinery run
├── Orchestrator (Agent, 编排型)
│   ├── Router (Agent, 编排型)
│   │   └── skill-route-provider
│   ├── Author (Agent, 执行型)
│   │   └── skill-validate-schema
│   ├── Reviewer (Agent, 执行型)
│   │   ├── skill-generate-cr
│   │   └── skill-trim-context
│   ├── Editor (Agent, 执行型)
│   │   ├── skill-process-cr
│   │   └── skill-validate-schema
│   └── Gate Evaluator (Agent, 执行型)
│       └── skill-evaluate-gate
├── skill-export-markdown
└── skill-calculate-cost

## 快速判断规则

| Gate 判定 | 行为 |
|-----------|------|
| PASS | 进入下一个 Pipeline |
| FAIL (blocking > 0) | 进入下一轮 Review 循环 |
| STOP (收敛/预算/超时) | 输出当前最佳版本，进入下一个 Pipeline |

## 产出物

| 阶段 | 产出 | 格式 |
|------|------|------|
| PRD Pipeline | PRD 文档 | JSON + Markdown |
| TECH_SPEC Pipeline | 技术规范 | JSON + Markdown |
| EXEC_PLAN Pipeline | 执行计划 | JSON + Markdown |
| 导出 | 三件套 Markdown | Markdown 文件 |
```

## Command vs Agent

| 维度 | Command | Agent |
|------|---------|-------|
| 触发 | 用户直接触发（CLI） | 被 Command 或 Orchestrator 调用 |
| 职责 | 编排完整流程 | 执行领域决策 |
| 粒度 | 粗粒度（完整任务） | 细粒度（单一领域） |
| IdeaRefinery 示例 | `refinery run` | Author, Reviewer, Editor, Gate Evaluator |

## 与 AIEF 的关系

- Command 规范是 **L2 级别** 的标准
- Command 与 `workflow/` 中的阶段定义互补：workflow 定义通用阶段，Command 定义具体流程
- Command 是用户与 AI 系统交互的入口点

## 参考

- [Skill 规范标准](skill-spec.md) — 执行层规范
- [Agent 规范标准](agent-spec.md) — 决策层规范
- [自动阶段路由模式](patterns/phase-router.md) — 阶段自动流转
