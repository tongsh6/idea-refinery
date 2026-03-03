# 工作流导航

> 定义 IdeaRefinery 项目的任务阶段流转和 AI 协作方式。

## 阶段模型

IdeaRefinery 的核心编排流程为 **Draft → Review → Edit → Gate** 循环，工作流阶段与之对齐。

```
触发请求 → 任务路由 → 阶段执行 → 验证 → 下一阶段/完成
```

### 阶段定义

| 阶段 | 触发条件 | 产出物 | IdeaRefinery 对应角色 |
|------|---------|--------|-----------------------|
| [proposal](phases/proposal.md) | 新功能、重大变更 | 提案文档 | — |
| [design](phases/design.md) | 需要技术设计 | 设计文档 | — |
| [implement](phases/implement.md) | 设计完成或简单任务 | 代码变更 | Author / Editor |
| [review](phases/review.md) | 实现完成 | 审查报告 | Reviewer / Gate Evaluator |

> **注意**：proposal 和 design 属于"开发流程"阶段（AIEF 工作流），implement 和 review 映射到引擎内部的 Draft→Review→Edit→Gate 循环。两者互补而非替代。

### 阶段流转图

```
┌──────────┐
│  触发请求  │
└────┬─────┘
     │
     ▼
┌──────────┐    新功能/重大变更   ┌──────────┐
│ 任务路由  │────────────────────→│  提案阶段  │
└────┬─────┘                     └────┬─────┘
     │                                │
     │ Bug修复/重构/文档                ▼
     │                          ┌──────────┐
     │                          │  设计阶段  │(可选)
     │                          └────┬─────┘
     │                                │
     ▼                                ▼
┌──────────┐                    ┌──────────┐
│  实现阶段  │←───────────────────│          │
└────┬─────┘                    └──────────┘
     │
     ▼
┌──────────┐     不通过     ┌──────────┐
│  审查阶段  │──────────────→│ 返回实现   │
└────┬─────┘               └──────────┘
     │ 通过
     ▼
┌──────────┐
│   完成    │
└──────────┘
```

## 任务路由规则

AI 接收任务时，根据以下规则判断流程：

### 需要提案的任务

- 新功能或新能力（如新增 Provider 插件、新增 GUI 模块）
- 破坏性变更（API、数据库 schema、CLI 参数格式）
- 架构调整（Orchestrator 流程变更、Store 模型扩展）
- 性能优化（改变可观察行为）
- Gate 规则变更

### 直接实现的任务

- Bug 修复（恢复预期行为）
- 代码重构（不改变行为）
- 文档更新（AGENTS.md、context/ 下内容）
- 配置变更
- 依赖更新（非破坏性）

### 需要设计的任务

- 跨模块变更（Orchestrator + Store + Exporter）
- 新增外部依赖
- Pydantic schema 变更（影响持久化与导出）
- 有安全/性能考虑

## 与 IdeaRefinery 引擎内部流程的关系

IdeaRefinery 引擎自身的 Draft→Review→Edit→Gate 循环是**产品功能**（用于精炼文档方案），工作流阶段是**开发过程管理**（用于管理代码变更）。

```
开发工作流（AIEF）：  proposal → design → implement → review
引擎内部流程：        Draft → Review → Edit → Gate → Stop/Loop
```

在 implement 阶段修改引擎代码时，需确保不破坏引擎内部的 Draft→Review→Edit→Gate 闭环。

## 阶段文档

- [提案阶段](phases/proposal.md) — 创建和审核变更提案
- [设计阶段](phases/design.md) — 技术设计和决策
- [实现阶段](phases/implement.md) — 代码编写和测试
- [审查阶段](phases/review.md) — 代码审查和验收

## 与外部工具集成

项目已集成 **spec-kit** 和 **superpowers** 辅助开发过程。完整安装和使用说明见 [工具集成指南](context/tech/TOOL_INTEGRATION.md)。

### spec-kit（提案 + 设计阶段）

| 阶段 | 命令 | 用途 |
|------|------|------|
| 提案 | `/speckit.constitution` | 建立项目原则（仅首次） |
| 提案 | `/speckit.specify` | 从 idea 生成结构化规范 |
| 提案 | `/speckit.clarify` | 澄清不明确的需求（可选） |
| 设计 | `/speckit.plan` | 生成技术实现计划 |
| 设计 | `/speckit.analyze` | 跨产物一致性分析（可选） |
| 实现 | `/speckit.tasks` | 分解为可执行任务 |
| 实现 | `/speckit.implement` | 按任务清单执行实现 |

### superpowers（实现 + 审查阶段）

superpowers 通过 AI 编码助手插件系统安装后，以下技能在对应阶段自动生效：

| 阶段 | 技能 | 用途 |
|------|------|------|
| 提案 | brainstorming | 苏格拉底式设计细化 |
| 设计 | writing-plans | 详细实现计划 |
| 实现 | test-driven-development | RED-GREEN-REFACTOR 强制执行 |
| 实现 | subagent-driven-development | 子代理驱动的任务分派 |
| 实现/审查 | systematic-debugging | 4 阶段根因分析 |
| 审查 | requesting-code-review | 代码审查请求 |

### OpenSpec — 已评估，跳过

OpenSpec 与 spec-kit 功能 80%+ 重叠，且为 TypeScript 栈（与本项目 Python 栈不匹配）。详细评估见 [工具集成指南](context/tech/TOOL_INTEGRATION.md#openspec-fission-aiopenspec--已评估跳过)。
