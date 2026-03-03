# 开发环境工具集成指南

> 记录 IdeaRefinery 开发过程中使用的外部工具、安装方式和使用场景。

## 工具概览

| 工具 | 定位 | AIEF 阶段 | 安装状态 |
|------|------|-----------|----------|
| **spec-kit** (GitHub) | SDD 规范驱动开发 | 提案 + 设计 | ✅ 已集成 |
| **superpowers** (obra) | AI 代理技能框架 | 实现 + 审查 | ✅ 可选安装 |
| **OpenSpec** (Fission-AI) | SDD 框架 | — | ⏭️ 已评估，跳过 |

## spec-kit (github/spec-kit)

**73k★ · Python · MIT · GitHub 官方**

### 是什么

spec-kit 是 GitHub 官方的规范驱动开发工具包。通过 `/speckit.*` slash 命令引导 AI 编码助手按照结构化流程开发：constitution → specify → plan → tasks → implement。

### 安装

```bash
# 安装 uv（如尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 specify-cli
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# 在项目中初始化（已完成）
specify init . --ai opencode --force --no-git
```

### 项目中的文件

```
.specify/
├── memory/
│   └── constitution.md          # 项目宪法（已填充）
├── scripts/bash/                # 自动化脚本（feature 分支、计划设置等）
└── templates/                   # 规范模板（spec/plan/tasks/checklist）

.opencode/command/
├── speckit.constitution.md      # /speckit.constitution 命令
├── speckit.specify.md           # /speckit.specify 命令
├── speckit.plan.md              # /speckit.plan 命令
├── speckit.tasks.md             # /speckit.tasks 命令
├── speckit.implement.md         # /speckit.implement 命令
├── speckit.clarify.md           # /speckit.clarify 命令（可选）
├── speckit.analyze.md           # /speckit.analyze 命令（可选）
├── speckit.checklist.md         # /speckit.checklist 命令（可选）
└── speckit.taskstoissues.md     # /speckit.taskstoissues 命令
```

### 在 AIEF 工作流中的使用

| AIEF 阶段 | spec-kit 命令 | 说明 |
|-----------|--------------|------|
| 提案 (Proposal) | `/speckit.constitution` | 建立项目原则（仅首次） |
| 提案 (Proposal) | `/speckit.specify` | 从 idea 生成结构化规范 |
| 提案 (Proposal) | `/speckit.clarify` | 澄清不明确的需求（可选） |
| 设计 (Design) | `/speckit.plan` | 生成技术实现计划 |
| 设计 (Design) | `/speckit.analyze` | 跨产物一致性分析（可选） |
| 实现 (Implement) | `/speckit.tasks` | 分解为可执行任务 |
| 实现 (Implement) | `/speckit.implement` | 按任务清单执行实现 |

### 与 IdeaRefinery 自身流水线的区别

- **spec-kit** 用于 IdeaRefinery *项目本身*的开发过程——帮助开发者用 AI 编码助手规范化地开发新功能
- **IdeaRefinery 流水线** 是 IdeaRefinery *产品*的核心功能——自动把用户的 idea 精炼为 PRD/TECH_SPEC/EXEC_PLAN
- 两者不冲突：spec-kit 管理"怎么开发 IdeaRefinery"，IdeaRefinery 管理"怎么精炼方案"

---

## superpowers (obra/superpowers)

**66.7k★ · Shell/JS/Python · MIT**

### 是什么

superpowers 是一个 AI 编码代理的技能框架和软件开发方法论。它提供一套可组合的"技能"（skills），自动注入到 AI 编码助手的系统提示中，使代理遵循结构化的开发流程。

### 核心技能

| 技能 | 说明 | 对应 AIEF 阶段 |
|------|------|----------------|
| brainstorming | 苏格拉底式设计细化 | 提案 |
| writing-plans | 详细实现计划 | 设计 |
| test-driven-development | RED-GREEN-REFACTOR 强制执行 | 实现 |
| subagent-driven-development | 子代理驱动的任务分派 | 实现 |
| systematic-debugging | 4 阶段根因分析 | 实现/审查 |
| requesting-code-review | 代码审查请求 | 审查 |
| using-git-worktrees | 隔离工作空间 | 实现 |
| finishing-a-development-branch | 分支完成流程 | 审查 |

### 安装（可选）

superpowers 通过 AI 编码助手的插件系统安装。根据你使用的工具选择：

**Claude Code:**
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

**OpenCode:**
```
告诉 OpenCode：
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md
```

**Cursor:**
```
/plugin-add superpowers
```

### 在 AIEF 工作流中的使用

superpowers 在**实现和审查阶段**自动生效：

1. **开始新功能前**：brainstorming 技能引导设计讨论
2. **编写代码时**：TDD 技能强制 RED-GREEN-REFACTOR
3. **任务执行**：subagent-driven-development 自动分派子任务
4. **遇到 bug**：systematic-debugging 引导根因分析
5. **代码完成后**：requesting-code-review 生成审查清单

### 对 AIEF Skill 设计的启发

superpowers 的 skill 设计模式值得借鉴到 IdeaRefinery 的 `docs/standards/skill-spec.md`：

- **技能自动触发**：基于上下文自动激活（vs. IdeaRefinery 的显式调用）
- **分层设计**：rigid skills（TDD 必须遵守）vs. flexible skills（可调整）
- **可组合性**：每个 skill 独立、可组合使用

---

## OpenSpec (Fission-AI/OpenSpec) — 已评估，跳过

**26.6k★ · TypeScript · MIT**

### 评估结论

| 维度 | 结论 |
|------|------|
| 技术栈 | Node.js/TypeScript — 与 IdeaRefinery 的 Python 栈不匹配 |
| 功能重叠 | 与 spec-kit 80%+ 重叠（propose/spec/design/tasks/implement） |
| 集成成本 | 需要 Node.js 运行时 + CLI 桥接，收益不成比例 |
| 额外价值 | OpenSpec 更轻量灵活，但 spec-kit 的模板和阶段体系更完整 |

### 跳过理由

1. **功能重复**：同时使用两个 SDD 框架会造成混乱（OpenSpec 用 `/opsx:*`，spec-kit 用 `/speckit.*`）
2. **技术栈不匹配**：OpenSpec 需要 Node.js 20.19+，IdeaRefinery 是纯 Python 项目
3. **spec-kit 更适合**：Python 原生、GitHub 官方维护、模板体系更完整
4. **OpenSpec 自己的评价**：其 README 称 spec-kit "thorough but heavyweight"——但对于 IdeaRefinery 这种结构化项目，"thorough" 正是我们需要的

### 未来可能重新评估的条件

- OpenSpec 推出 Python SDK
- spec-kit 停止维护或不再满足需求
- 需要更轻量的 SDD 流程（如快速原型场景）

---

## 工具之间的关系

```
                    ┌─────────────────────────────────┐
                    │    IdeaRefinery 开发过程         │
                    │                                  │
   AIEF 阶段        │    使用的外部工具                │
   ─────────        │    ──────────────                │
   提案 Proposal ──→│    spec-kit /speckit.specify     │
                    │    superpowers brainstorming     │
   设计 Design ───→ │    spec-kit /speckit.plan        │
                    │    superpowers writing-plans     │
   实现 Implement ─→│    spec-kit /speckit.implement   │
                    │    superpowers TDD + subagent    │
   审查 Review ───→ │    superpowers code-review       │
                    │    superpowers debugging          │
                    └─────────────────────────────────┘
```

## 版本信息

| 工具 | 安装版本 | 安装日期 |
|------|---------|---------|
| uv | 0.10.7 | 2026-03-02 |
| specify-cli | 0.1.6 | 2026-03-02 |
| superpowers | — (按需安装) | — |
