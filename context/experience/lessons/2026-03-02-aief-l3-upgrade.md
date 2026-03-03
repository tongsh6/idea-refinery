# AIEF L1→L3 升级：渐进式接入策略

> 大型框架接入应分级推进、先骨架后血肉，每级有明确的 DoD 和文件清单。

## 背景

- 项目/模块：IdeaRefinery 全项目 / AIEF 框架接入
- 时间：2026-02-27 ~ 2026-03-02
- 影响：项目级——影响所有后续 AI 协作的上下文质量和经验复用效率

## 问题

将 IdeaRefinery 的 AIEF 接入等级从 L1 升级到 L3，涉及 20+ 个文件的创建/更新，需要在保证一致性的前提下完成大量本地化工作。

### 症状

- L1 阶段经验可检索但无管理策略，AI 无法自动评估相关度
- 无工作流阶段定义，开发过程缺乏结构化引导
- 无规范标准，Skill/Agent/Command 定义散落在代码和注释中

### 复现条件

```
任何新项目首次接入 AIEF L3 时都会遇到相同问题
```

## 原因

### 技术原因

AIEF 框架提供的是通用模板，需要根据项目特有的领域模型、技术栈、Agent 角色进行本地化。直接复制模板无法发挥框架价值。

### 流程原因

缺乏分级推进策略，容易在 L2/L3 阶段产生文件间的交叉引用不一致。

## 解决方案

### 分级推进策略

```
L1 → L2（骨架层）→ L3（血肉层）

L2 先建结构：
  1. workflow/ 阶段定义（5 文件）
  2. docs/standards/ 规范标准（3 文件）
  3. experience 模板（2 文件）

L3 再填内容：
  4. patterns/ 跨切面模式（3 文件）—— 必须在 L2 完成后，因为 pattern 引用 L2 的文件
  5. 更新 AGENTS.md 和 INDEX.md —— 最后更新，确保引用完整
  6. 记录升级经验 —— 自举验证
```

### 本地化要点

1. **领域映射**：将 AIEF 通用概念映射到项目特有领域
   - IdeaRefinery 六大领域：Orchestrator、Provider、Gate、Store、Exporter、GUI
   - 引擎内部流程（Draft→Review→Edit→Gate）与 AIEF 工作流（proposal→design→implement→review）互补
2. **示例具体化**：所有示例使用项目实际场景（接入 Provider、修复 Gate Bug 等）
3. **交叉引用一致性**：pattern 文件间使用相对路径互引，最后统一验证

### 文件清单（共 15 个文件创建/更新）

| 级别 | 文件 | 行数 | 类型 |
|------|------|------|------|
| L2 | workflow/INDEX.md | 115 | 新建 |
| L2 | workflow/phases/proposal.md | 95 | 新建 |
| L2 | workflow/phases/design.md | 110 | 新建 |
| L2 | workflow/phases/implement.md | 105 | 新建 |
| L2 | workflow/phases/review.md | 135 | 新建 |
| L2 | docs/standards/skill-spec.md | 179 | 新建 |
| L2 | docs/standards/agent-spec.md | 197 | 新建 |
| L2 | docs/standards/command-spec.md | 179 | 新建 |
| L2 | context/experience/lessons/_template.md | 95 | 新建 |
| L2 | context/experience/reports/_template.md | 57 | 新建 |
| L3 | docs/standards/patterns/phase-router.md | 210 | 新建 |
| L3 | docs/standards/patterns/experience-mgmt.md | 215 | 新建 |
| L3 | docs/standards/patterns/context-loading.md | 174 | 新建 |
| - | AGENTS.md | 36 | 更新 |
| - | context/INDEX.md | 65 | 更新 |

## 教训

### 应该做

- 先确认远程模板的正确路径（GitHub 仓库可能不在预期的子目录下）
- 每个级别完成后立即验证文件存在性和交叉引用
- 本地化时保持项目术语一致性（建立映射表后复用）
- L3 pattern 文件最后创建（依赖 L2 文件的存在）

### 不应该做

- 不要一次性创建所有文件——分级推进能及时发现引用问题
- 不要直接复制远程模板——未本地化的模板对 AI 的指导价值接近零
- 不要在 pattern 文件中使用绝对路径——项目迁移后会全部失效

### 检查清单

下次进行 AIEF 升级时，检查：

- [ ] 远程模板路径正确（先验证 404 再批量获取）
- [ ] 本地化映射表已建立（领域、Agent、Skill 清单）
- [ ] L2 文件全部就位后再开始 L3
- [ ] 所有交叉引用使用相对路径且目标文件存在
- [ ] AGENTS.md 知识库表已更新（去掉 optional、标注正确 Level）
- [ ] context/INDEX.md 已添加关键词标签（L3 上下文加载模式要求）
- [ ] 至少记录一条 experience（自举验证经验沉淀机制）

## 相关

- [AIEF 框架仓库](https://github.com/tongsh6/ai-engineering-framework)
- [context/INDEX.md](../../context/INDEX.md) — 更新后的知识库索引
- [docs/standards/patterns/](../../docs/standards/patterns/) — L3 跨切面模式

---

**关键词**：`AIEF`, `L3`, `migration`, `localization`, `cross-reference`, `experience-management`

**类别**：设计决策
