# Agent 规范标准

> 定义 IdeaRefinery 项目中 Agent（决策层角色）的标准格式、分类方式和依赖声明规范。

## 概述

Agent 是 AIEF 三层架构中的**决策层**，代表一个具有领域知识的决策角色。Agent 根据上下文做出判断，调用 Skill 执行具体任务。

### 定位

```
Command（入口层）→ Agent（决策层）→ Skill（执行层）
                   ^^^^^^^
                   当前规范
```

## 标准格式

每个 Agent 文档应包含以下章节：

```markdown
# Agent: {Name}

## 角色
# 职责描述（一句话）

## 能力边界
# 能做什么 / 不能做什么

## 触发条件
# 何时被激活

## 工作流程
# 执行步骤（可选，复杂 Agent 需要）

## 依赖 Skills
# 显式声明使用的 Skill
```

### 必填章节

| 章节 | 必填 | 说明 |
|------|------|------|
| 角色 | 是 | 一句话职责描述 |
| 能力边界 | 是 | 明确能做和不能做的事 |
| 触发条件 | 是 | 被谁、在什么条件下调用 |
| 工作流程 | 否 | 复杂 Agent 需要，简单的可省略 |
| 依赖 Skills | 是 | 显式列出所有依赖的 Skill |

## IdeaRefinery 的 Agent 清单

### 执行型 Agent

| Agent | 角色 | 对应引擎阶段 |
|-------|------|-------------|
| **Author** | 根据 idea 和 prompt 生成初版产物（PRD/TECH_SPEC/EXEC_PLAN） | Draft |
| **Reviewer** | 多帽子审阅产物，输出结构化 CR | Review |
| **Editor** | 逐条处理 CR，修订产物 | Edit |
| **Gate Evaluator** | 根据规则判定 PASS/FAIL/STOP | Gate |

### 编排型 Agent

| Agent | 角色 | 说明 |
|-------|------|------|
| **Orchestrator** | 编排 Draft→Review→Edit→Gate 循环 | 状态机驱动 |
| **Router** | 根据角色/预算/策略选择 Provider | 模型路由 |

## Agent 分类

### 编排型 Agent（Orchestrator）

负责协调其他 Agent 或管理流程，自身不直接执行业务逻辑。

**特征**：
- 调用其他 Agent
- 管理流程状态（Draft→Review→Edit→Gate 循环）
- 做路由/分发决策

**IdeaRefinery 示例**：Orchestrator、Router

### 执行型 Agent（Executor）

负责特定领域的决策和执行，直接调用 Skill 完成任务。

**特征**：
- 直接调用 Skill
- 领域知识密集
- 输出明确的决策结果

**IdeaRefinery 示例**：Author、Reviewer、Editor、Gate Evaluator

## 依赖声明规范

每个 Agent 必须显式声明依赖的 Skill：

```markdown
## 依赖 Skills

| Skill | 用途 | 必需 |
|-------|------|------|
| `skill-validate-schema` | 验证产物 schema | 是 |
| `skill-generate-cr` | 生成结构化 CR | 是 |
| `skill-trim-context` | 上下文裁剪 | 否 |
```

### 依赖规则

1. **只依赖 Skill，不直接依赖其他执行型 Agent**（编排型除外）
2. **循环依赖禁止**
3. **可选依赖标注**：非必需的 Skill 标记为可选

## 完整示例

```markdown
# Agent: Reviewer

## 角色

以多帽子（价值/可行/风险/执行/反方）视角审阅产物，输出结构化 CR。

## 能力边界

**能做**：
- 按帽子角色审阅 PRD/TECH_SPEC/EXEC_PLAN
- 输出结构化 CR（problem/rationale/change/acceptance/severity）
- 给出章节级评分
- 识别 Blocking 级别的问题

**不能做**：
- 不修改产物内容（由 Editor 负责）
- 不做 Gate 判定（由 Gate Evaluator 负责）
- 不选择 Provider（由 Router 负责）

## 触发条件

- 被 Orchestrator 在 Review 阶段调用
- 输入为当前版本产物 + 上一轮 CR 状态（如有）

## 工作流程

1. 加载帽子角色定义
2. 章节级投喂（TL;DR/目标/里程碑/风险/验收/变更摘要）
3. 逐章节审阅，输出 CR
4. 汇总评分（avg_score）和 Blocking 统计

## 依赖 Skills

| Skill | 用途 | 必需 |
|-------|------|------|
| `skill-generate-cr` | 生成结构化 CR | 是 |
| `skill-trim-context` | 章节级上下文裁剪 | 是 |
| `skill-calculate-cost` | 统计本轮 tokens/cost | 否 |
```

## 三层关系

```
Command ──调用──→ Agent ──调用──→ Skill
  │                 │                │
  │ 编排流程         │ 做决策          │ 执行任务
  │ 管理状态         │ 调用 Skill      │ 无状态
  │ 面向用户         │ 面向领域         │ 面向数据
```

### IdeaRefinery 调用链

```
refinery run (Command)
├── Orchestrator (Agent, 编排型)
│   ├── Author (Agent, 执行型)
│   │   └── skill-validate-schema
│   ├── Reviewer (Agent, 执行型)
│   │   ├── skill-generate-cr
│   │   └── skill-trim-context
│   ├── Editor (Agent, 执行型)
│   │   ├── skill-process-cr
│   │   └── skill-validate-schema
│   ├── Gate Evaluator (Agent, 执行型)
│   │   └── skill-evaluate-gate
│   └── Router (Agent, 编排型)
│       └── skill-route-provider
└── skill-export-markdown
```

## 与 AIEF 的关系

- Agent 规范是 **L2 级别** 的标准
- 简单项目中，Agent 的职责可以内联在 AGENTS.md 的任务路由规则中
- 进入 L2 后，独立的 Agent 定义能支持多 Agent 协作
- 编排型 Agent（如 Orchestrator）与 `workflow/` 配合实现自动化流程

## 参考

- [Skill 规范标准](skill-spec.md) — 执行层规范
- [Command 规范标准](command-spec.md) — 入口层规范
- [自动阶段路由模式](patterns/phase-router.md) — 编排型 Agent 的典型实例
