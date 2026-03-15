# GUI 原型说明（v3）

本目录用于产品评审阶段，不是生产实现代码。

## 文件
- `review-workbench-v3.html`：**当前最新草案** v3，在 v2 基础上新增多文件上传面板与岗位画像配置面板，完整 i18n 支持。
- `review-workbench-v2.html`：草案 v2，覆盖 Timeline / CR Workspace / Gate 决策 / Artifact 入口 / 思考链 / 中英文切换（已归档）。
- `review-workbench-v1.html`：草案 v1（已归档）。

## 本地打开
```bash
open prototypes/gui/review-workbench-v3.html
```

## v3 新增功能（审阅重点）

### 面板 0：Idea 输入 + 补充材料上传
- **Idea 输入框**：顶部 `textarea` 作为主体输入，支持直接粘贴一句话或多段 idea
- **拖拽区域**：大拖拽区域，支持点击选文件；拖拽悬停时边框高亮、背景变色
- **文件列表**：图标（📄 PDF / 📝 Word / #️⃣ MD / 🗒️ TXT / 📁 目录）+ 文件名 + 大小 + ✕ 删除；行滑入动画
- **补充材料定位**：文件上传区文案为"补充材料（可选）"，不再与 idea 主输入冲突
- **Start Run 按钮**：idea 为空时禁用灰色；idea 有内容时激活为绿色（不依赖是否上传文件）
- **审阅确认项**：idea 输入优先级是否清晰？拖拽反馈是否足够？"Start Run" 状态切换是否清晰？

### 面板 1：岗位画像配置
- **Library 标签**：4 张预设卡片（产品经理 / 技术负责人 / 算法工程师 / 数据分析师），点击"选择"高亮
- **Custom JSON 标签**：textarea 粘贴 JSON，Import 解析；JSON 非法时显示内联错误
- **已选 Badge**：选中画像后，"Start Run" 旁显示 `[画像名 ×]` 徽章，点 ✕ 清除
- **审阅确认项**：两个 Tab 的切换是否流畅？卡片选中状态是否明显？Custom JSON 的错误提示是否清晰？

### 面板 1.5：Run Events Timeline（SQLite）
- **事件导入**：支持粘贴 `refinery observe --json` 输出并加载为事件表格
- **示例填充**：点击“填充示例 / Fill Sample”可快速预览表格效果
- **表格字段**：`time / round / step / event / detail / payload`
- **审阅确认项**：事件字段是否足够排障？中英文切换下文案是否一致？

## v2 保留功能

- **执行过程可视化（思考链）**：点击阶段卡片（Draft/Review/Edit/Gate），展示对应 CoT 日志
- **中英文切换（i18n）**：顶部 `EN / 中文` 按钮，所有文案（含新增面板）同步切换
- **Gate 模拟**：点击 `Simulate PASS/FAIL/STOP`，切换状态与判定说明
- **CR 工作区**：勾选进度条、严重级别筛选

## 交互说明
- **中英文切换**：点击顶部 `EN / 中文` 按钮，所有面板文案同步切换
- **Idea 输入**：先在 Panel 0 的 `💡 你的 Idea` 输入框填写需求描述
- **文件上传**：点击拖拽区域选择文件，或将文件拖入；点 ✕ 删除单个文件（可选）
- **岗位画像**：Library Tab 点"选择"选中预设；Custom Tab 粘贴 JSON 后点 Import
- **事件时间线**：执行 `refinery observe --latest --json`，复制输出到 Panel 1.5，点击"加载事件 / Load Events"
- **查看思考链**：点击 Timeline 中的阶段卡片，下方展示该阶段执行日志
- **Gate 模拟**：点击 `Simulate PASS/FAIL/STOP`
- **CR 进度**：勾选 CR 项，实时更新进度条

## 下一步建议
1. 确认 v3 原型的交互与视觉是否满足需求。
2. 确认后，可开始规划真实前端工程（React/Vue/原生）的搭建。
3. 设计后端 API：`POST /api/v1/documents`、`GET/POST /api/v1/profiles`、`POST /api/v1/runs`
4. 将 Run/Round/CR/Decision 数据与 SQLite Store 对接。
