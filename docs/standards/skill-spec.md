# Skill 规范标准

> 定义 IdeaRefinery 项目中 Skill（执行层原子单元）的标准格式、命名约定和设计原则。

## 概述

Skill 是 AIEF 三层架构中的**执行层**，代表一个原子化的、可复用的能力单元。Skill 不做决策，只执行明确定义的任务。

### 定位

```
Command（入口层）→ Agent（决策层）→ Skill（执行层）
                                      ^^^^^^^^
                                      当前规范
```

## 标准格式

每个 Skill 文档应包含以下章节：

```markdown
# Skill: {Name}

## 功能
# 单一职责描述（一句话）

## 输入
# Pydantic model 或 TypeScript 接口定义

## 输出
# Pydantic model 或 TypeScript 接口定义

## 执行策略
# 具体算法/规则（可选，复杂 Skill 需要）

## 示例
# 完整 Input → Output 示例

## 边界约束
# 不做什么（可选，明确边界）
```

### 必填章节

| 章节 | 必填 | 说明 |
|------|------|------|
| 功能 | 是 | 一句话描述，必须是单一职责 |
| 输入 | 是 | Pydantic model 或接口定义，明确每个字段 |
| 输出 | 是 | Pydantic model 或接口定义，明确每个字段 |
| 执行策略 | 否 | 复杂逻辑时需要，简单 CRUD 可省略 |
| 示例 | 是 | 至少一个完整的 Input → Output |
| 边界约束 | 否 | 有歧义时明确"不做什么" |

## 命名约定

### 文件名

```
skill-{verb}-{noun}.md
```

### IdeaRefinery 已识别的 Skill

| Skill | 动词 | 说明 |
|-------|------|------|
| `skill-validate-schema` | validate | 验证产物是否符合 Pydantic schema |
| `skill-generate-cr` | generate | 从 Reviewer 输出生成结构化 CR |
| `skill-process-cr` | process | Editor 逐条处理 CR（ACCEPT/REJECT/DEFER） |
| `skill-evaluate-gate` | evaluate | 执行 Gate 规则评估（Blocking/Score/Budget） |
| `skill-calculate-cost` | calculate | 统计 tokens/cost/latency |
| `skill-trim-context` | trim | 上下文裁剪（章节级投喂、diff 摘要） |
| `skill-export-markdown` | export | 从 JSON 产物导出 Markdown |
| `skill-route-provider` | route | 根据角色/预算/策略选择 Provider |

## 设计原则

### 1. 原子化（Atomic）

每个 Skill 只做一件事。如果描述中包含"和"、"并且"，应拆分。

```
❌ "生成 CR 并评估 Gate"
✅ "从 Reviewer 输出生成结构化 CR" (skill-generate-cr)
✅ "根据 CR 状态和评分执行 Gate 判定" (skill-evaluate-gate)
```

### 2. 无状态（Stateless）

Skill 不依赖外部状态，不产生副作用。相同输入永远产生相同输出。

```
❌ 读取 SQLite、调用 Provider API、修改文件
✅ 接收数据，返回结果
```

> 注意：与外部系统交互的操作（如 Store 读写、Provider 调用）应包装为 Agent 行为，而非 Skill。

### 3. 可复用（Reusable）

Skill 不绑定特定 Command 或 Agent，可被任意上层调用。

### 4. 明确 I/O（Explicit I/O）

输入和输出使用 Pydantic v2 model 或 TypeScript 接口明确定义，禁止 `Any` / `as any`。

## 完整示例

```markdown
# Skill: Evaluate Gate

## 功能

根据 CR 状态和评审评分，执行 Gate 规则评估，返回 PASS/FAIL/STOP 决策。

## 输入

class GateInput(BaseModel):
    blocking_count: int            # 未关闭的 Blocking CR 数量
    avg_score: float               # 平均评审评分
    consecutive_no_new_blocking: int  # 连续无新增 Blocking 的轮数
    budget_remaining: float        # 剩余预算
    round_count: int               # 当前轮次
    max_rounds: int                # 最大轮次
    sections_present: list[str]    # 当前产物已有章节
    required_sections: list[str]   # 必需章节列表

## 输出

class GateOutput(BaseModel):
    decision: Literal["PASS", "FAIL", "STOP"]
    reason: str
    stop_reason: str | None = None  # STOP 时的具体原因

## 执行策略

1. 章节缺失 → FAIL（reason: "缺少必需章节: {missing}"）
2. blocking_count > 0 → FAIL（reason: "存在未关闭的 Blocking CR"）
3. avg_score >= 8.0 且 blocking_count == 0 → PASS
4. consecutive_no_new_blocking >= 2 → STOP（stop_reason: "收敛"）
5. round_count >= max_rounds → STOP（stop_reason: "轮次上限"）
6. budget_remaining <= 0 → STOP（stop_reason: "预算耗尽"）
7. 其他情况 → FAIL（进入下一轮 Review）

## 示例

Input:
  blocking_count: 0
  avg_score: 8.5
  consecutive_no_new_blocking: 1
  budget_remaining: 0.5
  round_count: 3
  max_rounds: 10
  sections_present: ["目标", "里程碑", "风险", "验收标准"]
  required_sections: ["目标", "里程碑", "风险", "验收标准"]

Output:
  decision: "PASS"
  reason: "avg_score >= 8.0 且无 Blocking CR"
  stop_reason: null

## 边界约束

- 不修改 CR 状态（由 skill-process-cr 负责）
- 不调用外部 Provider
- 不写入 Store（由 Agent 层负责持久化决策）
```

## 与 AIEF 的关系

- Skill 规范是 **L2 级别** 的标准
- L0/L1 阶段可以不定义独立 Skill 文件，在 AGENTS.md 中描述能力即可
- 进入 L2 后，标准化 Skill 定义能显著提升复用性
- Skill 被 Agent 调用，Agent 被 Command 编排

## 参考

- [Agent 规范标准](agent-spec.md) — 决策层规范
- [Command 规范标准](command-spec.md) — 入口层规范

## 外部 Skill 模式参考：superpowers

> 以下总结 [superpowers](https://github.com/obra/superpowers) 的 Skill 设计模式，作为 IdeaRefinery Skill 规范演进的参考。

### 分层设计

superpowers 将 skill 分为两类：

- **Rigid skills**：强制遵守，无法跳过（如 TDD 的 RED-GREEN-REFACTOR 循环）
- **Flexible skills**：可根据上下文调整（如 brainstorming 的讨论深度）

IdeaRefinery 当前 Skill 均为显式调用，未区分强制/可选。后续可考虑引入类似分层，例如 `skill-validate-schema` 为 rigid（Gate 前必须执行），`skill-trim-context` 为 flexible（按预算弹性裁剪）。

### 自动触发机制

superpowers 的 skill 基于上下文自动激活（如检测到测试文件变更时自动启用 TDD skill）。IdeaRefinery 目前依赖 Agent 层显式调用 Skill。

未来可借鉴的方向：
- Agent 根据当前阶段自动加载相关 Skill（Draft 阶段自动加载 `skill-validate-schema`）
- Gate Evaluator 自动组合 `skill-evaluate-gate` + `skill-calculate-cost`

### 可组合性

superpowers 每个 skill 独立定义、互不依赖，可自由组合。这与 IdeaRefinery 的 Skill 原子化原则一致，验证了当前设计方向的合理性。

### 关键差异

| 维度 | superpowers | IdeaRefinery Skill |
|------|------------|-------------------|
| 调用方式 | 上下文自动触发 | Agent 显式调用 |
| 执行环境 | AI 编码助手系统提示 | Python 运行时 |
| I/O 定义 | 自然语言描述 | Pydantic v2 model |
| 状态管理 | 无状态 | 无状态（一致） |
| 分层 | rigid / flexible | 未分层（待演进） |

详见 [工具集成指南](../../context/tech/TOOL_INTEGRATION.md#superpowers-obrasuperpowers)。
