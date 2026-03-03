# Context 索引

这是项目长期上下文的导航入口。AI 根据任务关键词自动匹配需要加载的上下文（参见 [上下文加载模式](../docs/standards/patterns/context-loading.md)）。

## 目录结构

```
context/
    business/          # 业务知识
    tech/              # 技术文档
    experience/        # 经验库
workflow/              # 工作流阶段定义
docs/standards/        # 规范标准（Skill/Agent/Command）
docs/standards/patterns/  # L3 跨切面模式
```

## 业务知识（第 1 层）

| 文档 | 关键词 | 优先级 | 说明 |
|------|--------|--------|------|
| [DOMAIN.md](business/DOMAIN.md) | Draft, Review, Edit, Gate, CR, 闭环, 验收, 里程碑, GUI, 工作台 | P0 | 领域模型、业务规则、验收标准 |

## 技术知识（第 2 层）

| 文档 | 关键词 | 优先级 | 说明 |
|------|--------|--------|------|
| [ARCHITECTURE.md](tech/ARCHITECTURE.md) | 架构, 模块, schema, Pydantic, orchestrator, gate, store, provider, exporter | P0 | 系统架构、模块边界、Pydantic schema |
| [provider-integration.md](tech/provider-integration.md) | provider, 供应商, OpenAI-compatible, fallback, role-routing | P0 | 多供应商接入契约与路由策略 |
| [MULTI_FILE_ARCHITECTURE.md](tech/MULTI_FILE_ARCHITECTURE.md) | 多文件, GUI, 岗位画像, 上传 | P1 | 多文件输入与岗位画像架构设计 |
| [GITFLOW.md](tech/GITFLOW.md) | git, 分支, 发布, release, feature, merge | P1 | Git 工作流规范 |
| [TOOL_INTEGRATION.md](tech/TOOL_INTEGRATION.md) | spec-kit, superpowers, OpenSpec, 工具集成, SDD, 规范驱动 | P1 | 开发环境工具集成指南（安装、使用、决策记录） |

## 经验知识（第 3 层）

| 文档 | 关键词 | 优先级 | 说明 |
|------|--------|--------|------|
| [experience/INDEX.md](experience/INDEX.md) | 经验, 踩坑, 教训, 复盘, 最佳实践 | P1 | 经验索引（通过经验管理模式检索） |

详细检索策略见 [经验管理模式](../docs/standards/patterns/experience-mgmt.md)。

## 工作流（开发过程管理）

| 文档 | 关键词 | 说明 |
|------|--------|------|
| [workflow/INDEX.md](../workflow/INDEX.md) | 阶段, 流程, proposal, design, implement, review | 工作流导航与阶段流转 |
| [workflow/phases/proposal.md](../workflow/phases/proposal.md) | 提案, 需求, 范围评估 | 提案阶段定义 |
| [workflow/phases/design.md](../workflow/phases/design.md) | 设计, 方案, schema 兼容性 | 设计阶段定义 |
| [workflow/phases/implement.md](../workflow/phases/implement.md) | 实现, 编码, 测试 | 实现阶段定义 |
| [workflow/phases/review.md](../workflow/phases/review.md) | 审查, CR, Gate, 验收 | 审查阶段定义 |

## 规范标准

| 文档 | 关键词 | 说明 |
|------|--------|------|
| [docs/standards/skill-spec.md](../docs/standards/skill-spec.md) | skill, 技能, 能力 | Skill 规范（8 个已识别 Skill） |
| [docs/standards/agent-spec.md](../docs/standards/agent-spec.md) | agent, 角色, 编排 | Agent 规范（6 个 Agent） |
| [docs/standards/command-spec.md](../docs/standards/command-spec.md) | command, 命令, refinery run | Command 规范（Pipeline 编排） |

## 跨切面模式（L3）

| 文档 | 关键词 | 说明 |
|------|--------|------|
| [docs/standards/patterns/phase-router.md](../docs/standards/patterns/phase-router.md) | 路由, 自动阶段, 跳过条件 | 自动阶段路由模式 |
| [docs/standards/patterns/experience-mgmt.md](../docs/standards/patterns/experience-mgmt.md) | 经验管理, 索引, 沉淀, 相关度 | 三层经验管理模式 |
| [docs/standards/patterns/context-loading.md](../docs/standards/patterns/context-loading.md) | 上下文加载, 懒加载, 五层模型 | 上下文自动加载模式 |
