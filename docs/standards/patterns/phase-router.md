# 跨切面模式：自动阶段路由（Phase Router）

> 将手动推进的工作流阶段升级为基于任务类型的自动路由。

## 概述

Phase Router 是 `workflow/` 阶段模型的**自动化实现**。传统的 workflow 需要人工判断"当前应该进入哪个阶段"，Phase Router 根据任务特征自动路由，减少人工干预。

### 与现有 workflow/ 的关系

```
现有 workflow/：
  定义了阶段（proposal → design → implement → review）
  ↓ Phase Router 增值
  自动判断任务类型 → 自动跳过不需要的阶段 → 自动传递上下文
```

Phase Router 不替代 workflow/，而是在其上增加自动化能力。

### 与 IdeaRefinery 引擎内部流程的区别

```
AIEF 工作流（开发过程管理）：   proposal → design → implement → review
IdeaRefinery 引擎（产品功能）：  Draft → Review → Edit → Gate

两者互补：
- AIEF 工作流管理的是"如何开发 IdeaRefinery"
- 引擎内部流程管理的是"IdeaRefinery 如何精炼方案"
- Phase Router 作用于 AIEF 工作流层
```

## 核心机制

### 1. 任务类型识别

Phase Router 通过关键词和上下文自动识别 IdeaRefinery 项目中的任务类型：

| 任务类型 | 识别信号 | 默认阶段路径 |
|----------|---------|-------------|
| **新增 Provider** | "provider"、"接入"、"供应商"、"集成" | proposal → design → implement → review |
| **修改 Gate 规则** | "gate"、"评分"、"阈值"、"通过条件" | design → implement → review |
| **新增 Skill** | "skill"、"技能"、"能力" | design → implement → review |
| **GUI 开发** | "GUI"、"界面"、"工作台"、"前端" | proposal → design → implement → review |
| **Bug 修复** | "修复"、"解决"、"fix"、"bug" | implement → review |
| **重构** | "重构"、"优化"、"refactor" | design → implement → review |
| **Schema 变更** | "schema"、"模型"、"Pydantic"、"字段" | design → implement → review |
| **文档** | "文档"、"说明"、"docs"、"AGENTS" | implement → review |
| **配置** | "配置"、"设置"、"config"、"环境变量" | implement |
| **查询** | "查看"、"显示"、"解释" | （直接回答，不走阶段） |

### 2. 阶段跳过逻辑

```
输入任务 → 类型识别 → 计算阶段路径 → 依次执行阶段
                          │
                          ├── 已有提案？ → 跳过 proposal
                          ├── 改动范围小？ → 跳过 design
                          ├── 纯文档？ → 跳过 review
                          └── 全部需要？ → 完整流程
```

**IdeaRefinery 项目的跳过条件**：

| 阶段 | 跳过条件 | IdeaRefinery 具体场景 |
|------|---------|---------------------|
| proposal | 已存在相关提案；或改动明确且范围小 | 仅修改已有 Provider 的参数；调整 Gate 阈值 |
| design | 非架构变更；或变更影响范围 ≤ 2 个文件 | 修改单个 lesson 文档；调整 CLI 参数格式 |
| implement | （不可跳过） | 任何任务都需要实现 |
| review | 纯文档变更；或配置变更 | 更新 AGENTS.md；修改经验索引 |

### 3. 上下文传递

阶段间通过结构化上下文传递信息：

```python
# IdeaRefinery Phase Context（与引擎 Pydantic 模型风格一致）
class PhaseContext(BaseModel):
    task_type: str                          # 任务类型
    current_phase: str                      # 当前阶段
    completed_phases: list[str]             # 已完成阶段
    skipped_phases: list[str]               # 跳过的阶段
    artifacts: dict[str, Any]               # 各阶段产出
    metadata: PhaseMetadata                 # 元信息

class PhaseMetadata(BaseModel):
    started_at: datetime
    estimated_complexity: Literal["low", "medium", "high"]
    affected_modules: list[str]             # 影响的模块：orchestrator/gate/store/provider/exporter/gui
```

每个阶段接收前序阶段的产出，并将自己的产出追加到 `artifacts` 中。

## Phase Router Agent

Phase Router 本身是一个**编排型 Agent**（对应 IdeaRefinery 的 Router Agent）：

```markdown
# Agent: Phase Router

## 角色
根据任务类型和上下文，自动判断应执行的工作流阶段并路由。

## 能力边界
**能做**：
- 识别 IdeaRefinery 任务类型（Provider 接入 / Gate 规则 / Schema 变更 / GUI 等）
- 计算阶段路径（含跳过逻辑）
- 在阶段间传递上下文（affected_modules、artifacts）
- 在阶段失败时提供回退建议

**不能做**：
- 不执行具体阶段的逻辑（由 Author/Reviewer/Editor/Gate Evaluator 负责）
- 不修改阶段定义
- 不直接操作引擎内部的 Draft→Review→Edit→Gate 流程

## 触发条件
- 任何 Command 开始执行时
- 用户描述一个新的 IdeaRefinery 开发任务时

## 依赖
| 依赖 | 用途 |
|------|------|
| workflow/INDEX.md | 阶段定义参考 |
| context/experience/INDEX.md | 经验检索（implement 前自动触发） |
```

## 实施指南

### 最小实现

在 AGENTS.md 的"任务识别与路由"部分已有基础版本。升级为 Phase Router 只需：

1. **明确跳过条件**：为每个阶段定义可计算的跳过条件（见上表）
2. **添加上下文传递**：在阶段间传递结构化数据（而非让 AI 从聊天上下文推断）
3. **记录路由决策**：将路由决策记录到阶段上下文，便于审计

### 渐进采纳

| 级别 | 实现方式 | 适用场景 |
|------|---------|---------|
| 基础 | AGENTS.md 中的任务路由表 | L0-L1 项目 |
| 进阶 | 独立 Phase Router Agent + 跳过条件 | L2 项目 |
| 完整 | 结构化上下文传递 + 路由日志 + 回退机制 | L3 项目（当前目标） |

## 示例：新增 Provider 的自动路由

```
用户输入："接入 Moonshot（Kimi）作为新的 OpenAI-compatible Provider"

Phase Router 判断：
  任务类型：新增 Provider
  识别信号：包含"接入"、"Provider"
  默认路径：proposal → design → implement → review
  
  跳过检查：
    proposal → 执行（新 Provider 需要评估兼容性和配置契约）
    design → 执行（需要设计 config schema 扩展和 fallback 策略）
    implement → 执行
    review → 执行（Provider 变更影响运行时稳定性，需审查）
  
  最终路径：proposal → design → implement → review
  
  上下文传递：
    artifacts.taskAnalysis = {
      type: "new-provider",
      scope: "idea_refinery/providers/",
      affected_modules: ["provider", "orchestrator"],
      estimated_files: ["providers/kimi.py", "config.py"],
      related_experience: ["multi-provider-routing"]  # 来自经验索引
    }
```

## 示例：修复 Gate 评分 Bug

```
用户输入："Gate 评分在 CR 数量为 0 时抛出 ZeroDivisionError"

Phase Router 判断：
  任务类型：Bug 修复
  识别信号：包含"Gate"、"抛出"（错误修复信号）
  默认路径：implement → review
  
  跳过检查：
    proposal → 跳过（Bug 修复不需要提案）
    design → 跳过（修复范围明确，影响 ≤ 2 文件）
    implement → 执行
    review → 执行（Gate 是核心逻辑，必须审查）
  
  最终路径：implement → review
  
  上下文传递：
    artifacts.taskAnalysis = {
      type: "bugfix",
      scope: "idea_refinery/gate/",
      affected_modules: ["gate"],
      estimated_files: ["gate/evaluator.py"],
      related_experience: ["session-retrospective"]
    }
```

## 与其他模式的协作

- **经验管理模式**：Phase Router 在 implement 阶段前自动触发经验检索
- **上下文加载模式**：Phase Router 根据任务类型触发对应层的上下文加载

## 参考

- [Agent 规范标准](../agent-spec.md) — Agent 定义规范（含 IdeaRefinery 6 个 Agent）
- [Command 规范标准](../command-spec.md) — Command 编排模式（含 `refinery run` 4 阶段 Pipeline）
- [workflow/INDEX.md](../../../workflow/INDEX.md) — 工作流阶段定义
