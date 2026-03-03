# 多文件输入与岗位画像架构设计

版本：v0.2  
状态：草案（待评审）  
关联需求：GUI v2 原型评审反馈

---

## 1. 背景与问题

当前 IdeaRefinery 的输入模型极度简化：`Run.idea: str`，一个单一字符串。整个编排管道（Orchestrator/Graph）围绕这个字符串构建 Prompt，经历 Draft → Review → Edit → Gate 的闭环。

用户反馈指出三个核心限制：

1. **语料来源单一**：真实场景中，原始素材是多个文件（PDF、Word、TXT、Markdown 等），不是手敲的一段话。
2. **缺乏领域上下文**：不同业务场景（如招聘岗位评估、投资方案分析）需要不同的评审视角和验收标准，但系统没有机制注入这些配置。
3. **执行过程不透明**：用户看不到每个阶段在做什么，无法信任 AI 的决策路径。

本文档定义扩展后的架构，重点覆盖：
- 多文件摄入（Ingestion）层的设计
- `JobProfile`（岗位画像）的数据模型与配置机制
- 对现有 `Run`/`RunConfig`/`RefineryState` 的最小侵入式变更
- 思考链（Trace）的数据结构与 API 设计
- i18n 支持的职责边界

---

## 2. 架构总览

```
用户 / GUI
  │
  ├─ 上传文件/目录      → [Ingestion API]
  ├─ 选择/导入画像      → [Profile API]
  └─ 触发运行          → [Run API]
           │
           ▼
    ┌──────────────────────────────────────────────┐
    │              Ingestion Layer（新增）           │
    │  FileParser (PDF/Word/TXT/MD) → DocumentRef  │
    │  ContextAssembler (文档 + 画像 → Context)     │
    └──────────────────────────────────────────────┘
           │ assembled_context: str
           ▼
    ┌──────────────────────────────────────────────┐
    │           Orchestrator / LangGraph            │
    │   Draft → Review → Edit → Gate → Loop/Stop   │
    │   （核心闭环语义不变）                         │
    └──────────────────────────────────────────────┘
           │ 每个阶段产生 TraceEvent
           ▼
    ┌──────────────────────────────────────────────┐
    │                 Store (SQLite)                │
    │  Run / Round / Artifact / CR / Decision      │
    │  + documents / profiles / trace_events（新增）│
    └──────────────────────────────────────────────┘
           │
           ▼
      REST API → GUI（思考链、状态轮询、i18n 枚举值）
```

---

## 3. 领域模型变更

### 3.1 新增：`DocumentRef`

代表一个已上传并解析完成的文件引用。解析结果（纯文本）存储在数据库中，不重复解析。

```python
# idea_refinery/models/document.py

from __future__ import annotations
from datetime import UTC, datetime
from typing import Any
import uuid
from pydantic import BaseModel, Field


def _uid() -> str:
    return str(uuid.uuid4())

def _now() -> datetime:
    return datetime.now(UTC)


DocumentFileType = Literal[
    "pdf", "docx", "doc", "txt", "md", "csv", "json", "html", "unknown"
]

DocumentStatus = Literal["pending", "parsing", "ready", "failed"]


class DocumentRef(BaseModel):
    id: str = Field(default_factory=_uid)
    filename: str                        # 原始文件名，如 "JD-后端工程师.pdf"
    file_type: DocumentFileType = "unknown"
    size_bytes: int = 0
    storage_path: str                    # 本地路径或对象存储 Key
    parsed_content: str = ""            # 提取后的纯文本，供 Prompt 注入
    char_count: int = 0                 # 解析后字符数，用于 token 估算
    status: DocumentStatus = "pending"
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
```

**设计决策**：
- `parsed_content` 直接落库，避免每次 Run 重复解析。同一文件上传一次，多个 Run 可复用。
- `char_count` 而非 `token_count`，因 tokenizer 依赖模型，char_count 做粗估更通用。
- `storage_path` 在 MVP 阶段指本地文件系统路径；后续迁移对象存储时只改 Ingestion 层，不动 Prompt 层。

---

### 3.2 新增：`JobProfile`（岗位画像）

代表一套可复用的"领域知识注入包"，包含场景描述、评审视角补充、验收偏好等。

```python
# idea_refinery/models/profile.py

from __future__ import annotations
from datetime import UTC, datetime
import uuid
from pydantic import BaseModel, Field


class JobProfile(BaseModel):
    id: str = Field(default_factory=_uid)
    name: str                           # 如 "后端工程师岗位评估"
    description: str = ""              # 简短说明，显示在 GUI 下拉列表中
    domain: str = ""                   # 如 "recruitment", "investment", "product"
    context_template: str = ""         # 注入到 Prompt 的领域上下文文本块
    # 领域特定的评审帽子权重调整（覆盖默认 REVIEWER_HATS 顺序/权重）
    reviewer_hat_overrides: list[str] = Field(default_factory=list)
    # 领域特定的额外验收标准，Editor 必须逐条处理
    extra_acceptance_criteria: list[str] = Field(default_factory=list)
    # Gate 参数覆盖（如特定场景允许更低分数）
    gate_overrides: dict[str, float | int] = Field(default_factory=dict)
    is_builtin: bool = False           # 内置画像（随项目分发），不可删除
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
```

**示例 `context_template`（招聘场景）**：
```
你正在评估一份候选人资料（简历或能力评估），对标岗位为【{job_title}】。
评审时需特别关注：技术栈匹配度、项目复杂度、团队协作信号、成长潜力。
输出评估时，请引用简历中的具体描述作为证据。
```

**设计决策**：
- `context_template` 支持轻量 `{variable}` 插值，由 GUI 在触发 Run 时填充。
- `gate_overrides` 允许画像覆盖 `GateConfig` 中的部分参数，但不允许完全绕过 Gate，保持闭环语义。
- `reviewer_hat_overrides` 为空时继承全局 `RunConfig.reviewer_hats`；非空时完全替换。

---

### 3.3 `Run` 模型扩展

在**不破坏现有数据库兼容性**的前提下扩展 `Run`，通过 `ALTER TABLE ADD COLUMN` 渐进迁移：

```python
class Run(BaseModel):
    id: str = Field(default_factory=_uid)

    # 原有字段保留，idea 降级为"可选的简短标题/摘要"
    idea: str = ""              # 保持向后兼容；多文件场景填入自动摘要或用户输入的标题

    # 新增字段
    title: str = ""             # 用户可读的 Run 名称（GUI 显示用）
    document_ids: list[str] = Field(default_factory=list)   # DocumentRef.id 列表
    profile_id: str | None = None                           # JobProfile.id（可选）

    config_json: str = ""
    status: RunStatus = "pending"
    cost_usd: float = 0.0
    total_rounds: int = 0
    stop_reason: StopReason | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
```

**`idea` 字段的过渡策略**：
- 多文件场景：`idea` 由 `ContextAssembler` 自动生成（"基于 N 份文档的方案精炼，画像：{profile.name}"）。
- 单文本场景（CLI `refinery run --idea "..."`）：行为完全不变，`document_ids = []`，`profile_id = None`。
- 数据库层：新增两列 `document_ids_json TEXT` 和 `profile_id TEXT`，通过 `_ensure_column` 迁移。

---

### 3.4 新增：`TraceEvent`（思考链事件）

支持 GUI 实时渲染执行轨迹。每个阶段（Draft/Review/Edit/Gate）的关键动作以结构化事件记录。

```python
# idea_refinery/models/trace.py

from __future__ import annotations
from datetime import UTC, datetime
import uuid
from typing import Literal
from pydantic import BaseModel, Field

TraceActor = Literal[
    "SYSTEM",
    "AUTHOR",
    "REVIEWER_VALUE",
    "REVIEWER_FEASIBILITY",
    "REVIEWER_RISK",
    "REVIEWER_EXECUTION",
    "REVIEWER_DEVIL",
    "EDITOR",
    "GATE",
    "INGESTION",
]

TraceAction = Literal[
    "PHASE_START",
    "PHASE_END",
    "PROMPT_BUILT",
    "LLM_CALL_START",
    "LLM_CALL_END",
    "PARSE_SUCCESS",
    "PARSE_FAIL_RETRY",
    "CR_FOUND",
    "CR_RESOLVED",
    "GATE_EVALUATED",
    "FILE_PARSED",
    "CONTEXT_ASSEMBLED",
    "FALLBACK_TRIGGERED",
]


class TraceEvent(BaseModel):
    id: str = Field(default_factory=_uid)
    run_id: str
    round_id: str | None = None         # 关联到具体 Round（非阶段级事件为 None）
    sequence: int = 0                   # 同 Run 内单调递增，用于有序渲染
    actor: TraceActor
    action: TraceAction
    details: str = ""                   # 人类可读的补充说明
    metadata: dict = Field(default_factory=dict)   # 结构化附加数据
    created_at: datetime = Field(default_factory=_now)
```

**i18n 约定**：`actor` 和 `action` 为枚举值（英文），GUI 前端维护翻译表：
```javascript
// GUI 前端翻译映射（示例）
const ACTOR_LABELS = {
  zh: { AUTHOR: "起草者", REVIEWER_RISK: "审查者·风险", EDITOR: "编辑者", GATE: "门禁" },
  en: { AUTHOR: "Author",  REVIEWER_RISK: "Reviewer·Risk",  EDITOR: "Editor",  GATE: "Gate" }
}
```

后端不存储任何展示文案，彻底分离关注点。

---

## 4. 新增组件：Ingestion Layer

### 4.1 `FileParser` 接口

```python
# idea_refinery/ingestion/base.py

from abc import ABC, abstractmethod
from pathlib import Path


class BaseFileParser(ABC):
    supported_extensions: list[str] = []

    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """提取文件的纯文本内容，返回 UTF-8 字符串。失败时抛 ParseError。"""
        ...


class ParseError(Exception):
    def __init__(self, message: str, file_path: str):
        super().__init__(message)
        self.file_path = file_path
```

**内置解析器（MVP）**：

| 类名 | 支持扩展名 | 实现方式 |
|---|---|---|
| `PlainTextParser` | `.txt`, `.md`, `.csv` | 直接读取，无依赖 |
| `PdfParser` | `.pdf` | `pdfplumber`（轻量，无需 Java） |
| `DocxParser` | `.docx` | `python-docx` |
| `HtmlParser` | `.html`, `.htm` | `BeautifulSoup4`，提取正文文本 |

**扩展方式**：实现 `BaseFileParser` 并注册到 `ParserRegistry`，不需要修改核心编排。

### 4.2 `ContextAssembler`

将多个 `DocumentRef` 的内容与 `JobProfile` 拼装成最终注入 Prompt 的 Context 字符串：

```python
# idea_refinery/ingestion/assembler.py

class ContextAssembler:
    # 每份文档的最大字符数（防止单文件撑爆上下文）
    MAX_CHARS_PER_DOC = 8_000
    # 全部文档合并后的最大字符数
    MAX_TOTAL_CHARS = 30_000

    def assemble(
        self,
        documents: list[DocumentRef],
        profile: JobProfile | None,
        user_note: str = "",       # 用户在 GUI 补充的说明
    ) -> str:
        ...
```

**组装格式（草案）**：
```
[领域上下文]（来自 JobProfile.context_template，若有）
{profile.context_template}

[原始语料]（共 N 份文件）
--- 文件 1/N: {filename} ---
{truncated_content}

--- 文件 2/N: {filename} ---
{truncated_content}

[用户补充说明]（若有）
{user_note}
```

**截断策略**：
1. 单文档超过 `MAX_CHARS_PER_DOC` 时，保留前 60% + 后 40%，中间插入 `[...内容已截断...]`。
2. 所有文档超过 `MAX_TOTAL_CHARS` 时，按文件序号优先保留，后续文件截断更激进。
3. 截断信息记录到 `TraceEvent(action="CONTEXT_ASSEMBLED", metadata={"truncated_docs": [...]}`。

---

## 5. 流水线变更

### 5.1 新增 Ingestion 阶段（前置）

在 `run_refinery` / LangGraph 图的 START 节点之前，插入 Ingestion 节点：

```
START
  │
  ▼ [ingestion_node]（新增）
    1. 加载 document_ids 对应的 DocumentRef（从 Store）
    2. 若文档 status == "pending"，调用 FileParser 解析并更新 DocumentRef
    3. 加载 profile_id 对应的 JobProfile（若有）
    4. 调用 ContextAssembler.assemble() 生成 assembled_context
    5. 发射 TraceEvent(INGESTION, CONTEXT_ASSEMBLED)
    6. 写入 state["assembled_context"]
  │
  ▼ [draft_node]
    使用 state["assembled_context"] 替代原来的 state["idea"]
    构建 Prompt 时：build_author_prompt(context=assembled_context, ...)
  │
  ...（Review / Edit / Gate 不变）
```

### 5.2 `RefineryState` 扩展

```python
class RefineryState(TypedDict, total=True):
    # 原有字段（保持不变）
    idea: str               # 保留，向后兼容；多文件场景由 assembler 填充
    artifact_json: str
    crs_json: str
    round_number: int
    avg_score: float
    blocking_count: int
    total_cost_usd: float
    run_start: float
    decision: str
    stop_reason: str | None
    gate_reason: str
    changelog: str

    # 新增字段
    assembled_context: str  # ContextAssembler 输出，多文件场景替代 idea 注入 Prompt
    trace_sequence: int     # 单调递增计数器，用于 TraceEvent.sequence
    profile_id: str | None  # 传入 Review 阶段，附加 extra_acceptance_criteria
```

### 5.3 Prompt 变更

`build_author_prompt` 增加 `context` 参数：

```python
def build_author_prompt(
    idea: str,
    artifact_type: ArtifactType,
    context: str = "",              # 新增：assembled_context（多文件场景）
    previous_artifact: str | None = None,
    editor_changelog: str | None = None,
) -> list[Message]:
    # 若 context 非空，优先使用 context；否则退回 idea（向后兼容）
    primary_input = context if context.strip() else idea
    ...
```

`build_reviewer_prompt` 增加 `extra_criteria` 参数：

```python
def build_reviewer_prompt(
    idea: str,
    artifact_json: str,
    artifact_type: ArtifactType,
    hat: str,
    round_number: int,
    extra_criteria: list[str] | None = None,   # 来自 JobProfile
) -> list[Message]:
    ...
```

---

## 6. Store 层变更

### 6.1 新增数据表

在 `SqliteStore._init_schema()` 中追加：

```sql
-- 已解析的文档引用
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT,
    size_bytes INTEGER DEFAULT 0,
    storage_path TEXT,
    parsed_content TEXT,
    char_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    error TEXT,
    metadata_json TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- 岗位画像（Job Profile）
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    context_template TEXT,
    reviewer_hat_overrides_json TEXT,   -- JSON array
    extra_acceptance_criteria_json TEXT, -- JSON array
    gate_overrides_json TEXT,           -- JSON object
    is_builtin INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

-- 思考链事件
CREATE TABLE IF NOT EXISTS trace_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT,
    sequence INTEGER DEFAULT 0,
    actor TEXT,
    action TEXT,
    details TEXT,
    metadata_json TEXT,
    created_at TEXT
);
```

### 6.2 `runs` 表扩展

通过 `_ensure_column` 渐进迁移：

```python
self._ensure_column("runs", "title", "TEXT")
self._ensure_column("runs", "document_ids_json", "TEXT")   # JSON array of doc IDs
self._ensure_column("runs", "profile_id", "TEXT")
```

---

## 7. REST API 设计

当前系统是 CLI 工具，暂无 HTTP 服务器。引入 GUI 后，需要一个轻量后端服务（FastAPI 推荐，与 Pydantic v2 原生兼容）。

### 7.1 文档管理

```
POST   /api/v1/documents
       Content-Type: multipart/form-data
       Body: files=[@file1, @file2, ...]
       Response: { "documents": [DocumentRef, ...] }
       说明: 上传后触发异步解析（status 从 pending → parsing → ready/failed）

GET    /api/v1/documents/{id}
       Response: DocumentRef

DELETE /api/v1/documents/{id}
       说明: 只删除 parsed_content，保留文件元数据，避免破坏引用中的 Run
```

### 7.2 画像管理

```
GET    /api/v1/profiles
       Response: { "profiles": [JobProfile, ...] }

POST   /api/v1/profiles
       Body: JobProfile（不含 id，由服务端生成）
       Response: JobProfile

POST   /api/v1/profiles/import
       Content-Type: multipart/form-data
       Body: file=[@profile.json]
       说明: 导入 JSON 格式的画像文件，用于团队共享

PUT    /api/v1/profiles/{id}
       Body: 部分更新（Pydantic model_copy + update）

DELETE /api/v1/profiles/{id}
       约束: is_builtin == true 时返回 403
```

**画像导入格式（profile.json）**：
```json
{
  "name": "后端工程师岗位评估",
  "domain": "recruitment",
  "context_template": "你正在评估候选人资料...",
  "reviewer_hat_overrides": ["value", "feasibility", "risk"],
  "extra_acceptance_criteria": [
    "候选人技术栈与 JD 要求匹配度必须量化（%）",
    "至少引用简历中 2 处具体项目描述作为评分依据"
  ],
  "gate_overrides": {
    "min_avg_score": 7.5
  }
}
```

### 7.3 Run 管理

```
POST   /api/v1/runs
       Body:
       {
         "title": "张三·后端工程师评估",
         "document_ids": ["doc_abc", "doc_def"],
         "profile_id": "prof_xyz",       // 可选
         "user_note": "重点关注分布式系统经验",  // 可选
         "config": {                     // 可选，覆盖默认 RunConfig
           "gate": { "max_rounds": 4 },
           "dry_run": false
         }
       }
       Response: { "run_id": "run_...", "status": "pending" }

GET    /api/v1/runs/{id}
       Response: Run（含 document_ids, profile_id）

GET    /api/v1/runs/{id}/traces
       Query: ?since_sequence=0&limit=50
       Response: { "events": [TraceEvent, ...], "has_more": bool }
       说明: 轮询接口，GUI 每 1-2 秒拉取，渲染思考链
```

---

## 8. GUI 集成要点

### 8.1 文件上传区（替换现有输入框）

```
┌─────────────────────────────────────────────────────────┐
│   拖拽文件至此 / 点击选择文件                              │
│   支持: PDF、Word、TXT、Markdown（最多 10 个文件，100MB）  │
│                                                          │
│   [已上传]                                               │
│   📄 简历-张三.pdf  ✅ 解析完成 (8,432 字)               │
│   📄 JD-后端工程师.docx  ✅ 解析完成 (2,109 字)          │
│   📄 项目经历补充.md  ⏳ 解析中...                       │
└─────────────────────────────────────────────────────────┘
```

**交互逻辑**：
1. 文件上传后立即调用 `POST /api/v1/documents`，返回 `DocumentRef` 列表。
2. 轮询 `GET /api/v1/documents/{id}` 直到 `status == "ready"`，展示字符数。
3. 触发 Run 时，把 `document_ids` 传入 `POST /api/v1/runs`。

### 8.2 画像选择器

```
┌─────────────────────────┐
│ 岗位画像（可选）         │
│ ┌─────────────────────┐ │
│ │ 后端工程师岗位评估 ▼ │ │
│ └─────────────────────┘ │
│ [+ 导入画像] [创建新画像]│
└─────────────────────────┘
```

### 8.3 思考链面板

GUI 通过轮询 `GET /api/v1/runs/{id}/traces` 实时渲染：

```
[系统] 数据摄入阶段开始
[系统] 文件 "简历-张三.pdf" 解析完成 (8,432 字)
[系统] 上下文组装完成：共 2 份文件，画像"后端工程师岗位评估"
[起草者] 开始起草 PRD（第 1 轮）
[起草者] 调用模型 gpt-4o...
[起草者] 草稿完成，覆盖率 87%
[审查者·价值] 评审中...
[审查者·风险] 发现 2 个 Blocking CR
[编辑者] 处理 CR，更新草稿
[门禁] avgScore=7.8，Blocking=0，决策：PASS
```

**i18n 切换**：actor 和 action 由 GUI 翻译表映射，`details` 字段的内容语言取决于模型输出语言（不做后端控制，属于 LLM 行为）。

---

## 9. 向后兼容性保证

| 场景 | 现有行为 | 扩展后行为 |
|---|---|---|
| `refinery run --idea "..."` CLI | 正常运行 | 完全不变，`document_ids=[]`, `profile_id=None` |
| `Run.idea` 字段 | 必填字符串 | 改为默认 `""`，通过 `assembled_context` 注入 |
| SQLite 数据库 | 不含新列 | 通过 `_ensure_column` 自动迁移，旧记录新列为 NULL |
| `build_author_prompt` | 只接受 `idea` | 新增 `context` 参数，默认 `""`，退回原行为 |
| `RefineryState` | 不含 trace 字段 | 新增字段有默认值，不破坏现有 Graph 节点 |

---

## 10. 分阶段实施路线

### Phase 1：模型层与 Store（无 LLM 变化）
- 定义 `DocumentRef`、`JobProfile`、`TraceEvent` Pydantic 模型
- 扩展 `SqliteStore`：新增三张表，`runs` 表 `_ensure_column` 迁移
- 单元测试：CRUD 覆盖率 100%
- **验收**：`pytest` 全绿，`python -m build` 成功

### Phase 2：Ingestion Layer
- 实现 `BaseFileParser` + `PlainTextParser` + `PdfParser` + `DocxParser`
- 实现 `ContextAssembler`（截断策略 + 格式化）
- 集成测试：上传真实文件，验证解析结果字符数与 `parsed_content` 正确性
- **验收**：5 种文件格式解析通过，截断行为有 TraceEvent 记录

### Phase 3：编排层扩展
- 在 LangGraph 图中插入 `ingestion_node`
- 扩展 `RefineryState`（`assembled_context`、`trace_sequence`、`profile_id`）
- 扩展 `build_author_prompt` / `build_reviewer_prompt`
- `TraceEvent` 在每个节点入口/出口发射
- **验收**：`refinery run --idea "..."` 行为不变；带 `document_ids` 的 Run 能产出三件套

### Phase 4：REST API
- 引入 FastAPI，实现 7.1-7.3 节定义的接口
- 文件上传接口异步解析（`asyncio.create_task` 或 `BackgroundTask`）
- `GET /api/v1/runs/{id}/traces` 轮询接口（简单查询，无 WebSocket 依赖）
- **验收**：Postman 或 `httpx` 脚本测试所有端点

### Phase 5：GUI 集成
- 替换输入框为文件上传区
- 接入画像选择器
- 实现思考链面板（轮询 + 渲染 + i18n 切换）
- **验收**：端到端演示：上传 2 份文件 + 选择画像 → 触发 Run → 实时看到思考链 → 产出三件套

---

## 11. 关键约束重申

1. **Draft → Review → Edit → Gate 闭环不变**：Ingestion 是前置预处理，不插入闭环中间。
2. **CR 闭环规则不变**：`JobProfile.extra_acceptance_criteria` 通过 Prompt 注入，不旁路 Gate 规则。
3. **产物先结构化 JSON，再导出 Markdown**：Ingestion 层输出的是纯文本 Context，不是 Artifact。
4. **成本可控**：`ContextAssembler.MAX_TOTAL_CHARS` 限制上下文规模，`TraceEvent` 记录截断行为，配合 `GateConfig.budget_usd`。
5. **可回放**：所有 `TraceEvent` 落库，任何 Run 可事后回放完整执行轨迹。
6. **i18n 职责在前端**：后端所有枚举值使用英文，`details` 字段内容不做语言管控。

---

## 12. 开放问题

| 问题 | 影响 | 建议决策时间 |
|---|---|---|
| 文件存储策略：本地 `./uploads/` vs 对象存储（MinIO/S3） | Phase 2 实现细节 | Phase 1 结束前确认 |
| 大文件解析异步化：是否需要后台 worker（Celery/ARQ）或简单 `BackgroundTask` | Phase 4 架构 | Phase 3 结束前确认 |
| `JobProfile` 版本化：画像变更后，历史 Run 关联的是哪个版本？ | 数据一致性 | Phase 1 设计时确认 |
| 多租户：当前 SQLite 是单进程单文件，GUI 多用户时如何隔离？ | 中期架构风险 | v0.x 暂不解决，记录为技术债 |
| 画像内置库：是否随项目分发预置画像（如"通用 PRD"、"招聘评估"）？ | Phase 5 产品决策 | 产品评审确认 |
