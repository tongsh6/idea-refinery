# 外部工具集成：spec-kit + superpowers 的开发过程集成策略

> 外部 SDD/Skill 工具应以"开发过程集成"模式接入，避免与产品运行时耦合。

## 背景

- 项目/模块：IdeaRefinery 全局（AIEF 工作流）
- 时间：2026-03-02
- 影响：开发流程增强，不影响运行时代码

IdeaRefinery 使用 AIEF 框架管理开发过程。在 L3 升级完成后，需要评估并集成外部工具（OpenSpec、spec-kit、superpowers）来增强开发效率。

## 问题

### 症状

- 三个候选工具（OpenSpec、spec-kit、superpowers）定位相似但技术栈各异
- 不确定是"运行时集成"还是"开发过程集成"
- 需要避免工具之间的功能重叠和命令冲突

### 复现条件

```
面对多个同类外部工具需要做集成决策时
```

## 原因

### 技术原因

- 三个工具都面向 AI 编码助手，帮助人类开发者通过 AI 更好地开发软件
- IdeaRefinery 本身是 AI 产品——这些工具不适合嵌入其运行时
- OpenSpec 为 TypeScript 栈，与 Python 项目不匹配

### 流程原因

- 初期未明确"集成"的含义（开发过程 vs. 运行时），导致评估范围过大
- 同类工具同时评估时需要系统化的对比维度

## 解决方案

### 决策层面

1. **明确集成模式**：开发过程集成（辅助开发 IdeaRefinery），而非运行时集成（嵌入 IdeaRefinery 产品）
2. **工具选择**：
   - ✅ spec-kit — 主力集成（Python 原生、GitHub 官方、模板完整）
   - ✅ superpowers — 技能层集成（通过 AI 编码助手插件系统安装）
   - ⏭️ OpenSpec — 跳过（与 spec-kit 80%+ 重叠、TypeScript 栈不匹配）

### 配置层面

- spec-kit 通过 `uv tool install specify-cli` 安装，`specify init .` 初始化
- 项目产物：`.specify/`（配置+模板）、`.opencode/command/`（slash 命令）
- superpowers 通过 AI 编码助手的插件系统按需安装，不引入项目依赖
- 所有集成文档归档到 `context/tech/TOOL_INTEGRATION.md`

### 流程层面

- 将工具与 AIEF 四阶段对齐：提案→设计用 spec-kit，实现→审查用 superpowers
- 在 `workflow/INDEX.md` 中更新集成说明，使阶段→工具的映射关系显式化
- 在 `docs/standards/skill-spec.md` 中记录 superpowers 的 Skill 设计模式参考

## 教训

### 应该做

- 先明确"集成"的定义边界（开发过程 vs. 运行时 vs. 代码依赖）
- 候选工具同类比较时，建立统一评估维度表（技术栈、功能重叠度、安装成本、维护方）
- 尽早做技术栈匹配过滤——TypeScript 工具对 Python 项目的集成成本高
- 将集成决策和评估过程记录到文档中，避免后续重复评估

### 不应该做

- 不要同时集成功能重叠度 >50% 的同类工具（如 OpenSpec + spec-kit）
- 不要把"面向 AI 编码助手的工具"误解为"可嵌入 AI 产品运行时的工具"
- 不要在未确认集成模式前开始安装和配置

### 检查清单

下次遇到类似问题时，检查：

- [ ] 明确集成模式：开发过程 / 运行时 / 代码依赖？
- [ ] 技术栈是否匹配（语言、运行时、包管理）？
- [ ] 与现有工具的功能重叠度 <50%？
- [ ] 安装方式是否会引入项目级依赖？
- [ ] 是否有官方维护和社区支持？

## 相关

- [工具集成指南](../../context/tech/TOOL_INTEGRATION.md) — 安装和使用详情
- [Skill 规范标准](../../../docs/standards/skill-spec.md) — superpowers 模式参考章节
- [工作流导航](../../../workflow/INDEX.md) — 工具与 AIEF 阶段的映射

---

**关键词**：`spec-kit`, `superpowers`, `OpenSpec`, `tool-integration`, `SDD`, `开发过程集成`, `AIEF`

**类别**：设计决策
