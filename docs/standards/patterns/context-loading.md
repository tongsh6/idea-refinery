# 跨切面模式：上下文自动加载（Context Loading）

> 将 `context/` 的索引导航升级为基于任务类型的自动加载策略。

## 概述

上下文自动加载模式定义了 AI 在执行 IdeaRefinery 开发任务时，如何自动选择和加载相关上下文的策略。目标是**零配置**——AI 根据任务描述自动匹配需要的上下文，无需用户手动指定。

### 与现有 context/INDEX.md 的关系

```
现有 context/INDEX.md：
  提供了知识库的索引和导航
  ↓ 上下文加载模式增值
  自动匹配 → 优先级排序 → 去重 → 按需摘要
```

上下文加载模式不替代 INDEX.md，而是定义 AI 如何"使用"这个索引。

## 五层加载模型

上下文按优先级分为 5 层，AI 根据任务需要加载对应层级：

```
第 1 层：业务上下文（Business）     —— 领域模型、术语、业务规则
第 2 层：技术上下文（Technical）     —— 架构、API、开发规范
第 3 层：经验上下文（Experience）    —— 历史经验、踩坑记录
第 4 层：会话上下文（Session）       —— 当前会话中的决策和产出
第 5 层：规范上下文（Specification） —— OpenSpec / spec-kit 规范文档（未来集成）
```

### IdeaRefinery 各层对应

| 层级 | 来源 | IdeaRefinery 具体文件 | 加载时机 | 持久性 |
|------|------|---------------------|---------|--------|
| 业务 | `context/business/` | `DOMAIN.md`（领域模型、验收标准、里程碑） | 涉及领域逻辑时 | 持久 |
| 技术 | `context/tech/` | `ARCHITECTURE.md`、`GITFLOW.md`、`MULTI_FILE_ARCHITECTURE.md`、`provider-integration.md` | 涉及代码实现时 | 持久 |
| 经验 | `context/experience/` | `INDEX.md` → `lessons/*.md` → `summaries/`（未来） | 任何实现类任务 | 持久 |
| 会话 | 当前对话历史 | AI 会话中的决策记录和阶段产出 | 始终可用 | 临时 |
| 规范 | `openspec/`（未来） | OpenSpec / spec-kit 规范文档（待集成） | 涉及规范定义的功能时 | 持久 |

## 加载策略

### 1. IdeaRefinery 自动匹配规则

根据任务关键词自动匹配需要加载的上下文：

| 任务关键词 | 自动加载 |
|-----------|---------|
| Draft, Review, Edit, Gate, 编排, 流水线 | `context/business/DOMAIN.md` + `context/tech/ARCHITECTURE.md` |
| Provider, 供应商, 接入, fallback, routing | `context/tech/provider-integration.md` + `context/tech/ARCHITECTURE.md` |
| Schema, Pydantic, 模型, 字段 | `context/tech/ARCHITECTURE.md` |
| GUI, 界面, 工作台, 原型 | `context/business/DOMAIN.md`（GUI 验收标准）+ `context/tech/MULTI_FILE_ARCHITECTURE.md` |
| Git, 分支, 发布, 合并 | `context/tech/GITFLOW.md` |
| CR, 闭环, 回放 | `context/business/DOMAIN.md`（CR 规则）+ `context/tech/ARCHITECTURE.md` |
| 任何实现类任务 | `context/experience/INDEX.md`（通过经验管理模式检索） |

### 2. 懒加载（Lazy Loading）

不预加载所有上下文，而是按需加载：

```
阶段 1（任务分析）：加载第 1 层（业务）→ 理解 IdeaRefinery 领域和验收标准
阶段 2（方案设计）：加载第 2 层（技术）→ 确定架构方案（Pydantic schema、Store、Provider）
阶段 3（实现前）  ：加载第 3 层（经验）→ 检索相关经验，避免踩坑
阶段 4（实现中）  ：使用第 4 层（会话）→ 保持上下文一致
阶段 5（涉及规范）：加载第 5 层（规范）→ 遵循 OpenSpec/spec-kit 标准（未来）
```

### 3. 优先级排序

当多个上下文被匹配时，按以下优先级排序：

```
直接相关 > 同领域 > 同层级 > 通用
```

| 优先级 | 匹配方式 | IdeaRefinery 示例 |
|--------|---------|------------------|
| P0 - 直接相关 | 文件名/标题包含任务关键词 | 任务提到"Gate" → `ARCHITECTURE.md` 中的 Gate 模块 |
| P1 - 同领域 | 属于同一领域分组 | 任务涉及 Provider → 整个 `context/tech/provider-integration.md` |
| P2 - 同层级 | 属于同一上下文层 | 涉及技术实现 → 整个 `context/tech/` |
| P3 - 通用 | 通用规范/约定 | GITFLOW、编码约束 |

### 4. 去重

多个匹配规则可能命中同一个文档，加载时自动去重：

```
规则 1 命中：DOMAIN.md, ARCHITECTURE.md
规则 2 命中：DOMAIN.md, provider-integration.md
→ 实际加载：DOMAIN.md, ARCHITECTURE.md, provider-integration.md
```

### 5. 摘要化

当上下文总量超过 AI 处理窗口时，按优先级保留原文，低优先级内容进行摘要：

```
P0 内容 → 保留原文
P1 内容 → 保留原文
P2 内容 → 若总量超限，摘要化（保留结构 + 关键信息）
P3 内容 → 若总量超限，仅加载标题和概述
```

## IdeaRefinery 任务类型与加载策略映射

| 任务类型 | 加载的层级 | IdeaRefinery 具体上下文 |
|----------|-----------|----------------------|
| 新增 Provider | 1 + 2 + 3 | DOMAIN.md + ARCHITECTURE.md + provider-integration.md + 经验 |
| 修改 Gate 规则 | 1 + 2 + 3 | DOMAIN.md（Gate 验收标准）+ ARCHITECTURE.md（Gate 模块）+ 经验 |
| GUI 开发 | 1 + 2 + 3 | DOMAIN.md（GUI AC）+ MULTI_FILE_ARCHITECTURE.md + 经验 |
| Schema 变更 | 2 + 3 | ARCHITECTURE.md（Pydantic schema）+ 经验 |
| Bug 修复 | 2 + 3 | ARCHITECTURE.md + 经验 |
| 重构 | 2 + 3 | ARCHITECTURE.md + 经验 |
| 文档 | 1 + 2 | DOMAIN.md + ARCHITECTURE.md |
| 查询 | 按需 | 根据问题内容决定 |

## 实施指南

### 最小实现

在 AGENTS.md 中已有基础版本（知识库表）。升级为完整模式需要：

1. **明确匹配规则**：在 `context/INDEX.md` 中为每个文档添加关键词标签（✅ 即将完成）
2. **定义加载顺序**：在任务路由后，按层级顺序加载
3. **控制加载量**：设置每层的最大加载文档数

### 渐进采纳

| 级别 | 实现方式 | 适用场景 |
|------|---------|---------|
| 基础 | AGENTS.md 中的加载表 | L0-L1 项目 |
| 进阶 | 按关键词自动匹配 + 懒加载 | L2 项目 |
| 完整 | 5 层模型 + 优先级 + 摘要化 | L3 项目（当前目标） |

### IdeaRefinery context/INDEX.md 关键词标签配置

```markdown
# 知识库索引

## 业务知识

| 文档 | 关键词 | 优先级 |
|------|--------|--------|
| [DOMAIN.md](business/DOMAIN.md) | Draft, Review, Edit, Gate, CR, 闭环, 验收, 里程碑, GUI, 工作台 | P0 |

## 技术知识

| 文档 | 关键词 | 优先级 |
|------|--------|--------|
| [ARCHITECTURE.md](tech/ARCHITECTURE.md) | 架构, 模块, schema, Pydantic, orchestrator, gate, store, provider, exporter | P0 |
| [provider-integration.md](tech/provider-integration.md) | provider, 供应商, OpenAI-compatible, fallback, role-routing | P0 |
| [MULTI_FILE_ARCHITECTURE.md](tech/MULTI_FILE_ARCHITECTURE.md) | 多文件, GUI, 岗位画像, 上传 | P1 |
| [GITFLOW.md](tech/GITFLOW.md) | git, 分支, 发布, release, feature, merge | P1 |

## 经验知识

| 文档 | 关键词 | 优先级 |
|------|--------|--------|
| [experience/INDEX.md](experience/INDEX.md) | 经验, 踩坑, 教训, 复盘, 最佳实践 | P1 |
```

## 与其他模式的协作

- **阶段路由模式**：Phase Router 确定任务类型后，触发对应的上下文加载策略
- **经验管理模式**：经验是第 3 层上下文，通过经验管理模式的相关度算法加载

## 参考

- [context/INDEX.md](../../../context/INDEX.md) — 知识库索引
- [经验管理模式](experience-mgmt.md) — 经验层的加载策略
- [自动阶段路由模式](phase-router.md) — 触发上下文加载的路由机制
