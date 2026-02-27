# API 与 CLI 约定（v0.1 CLI / v0.2 API）

## CLI（OSS）
命令：
- `refinery run --idea ... --out ./out --budget ... --max-rounds ...`

核心参数：
- `--idea`：输入 idea 文本
- `--out`：输出目录（产物 Markdown）
- `--budget`：预算上限（USD）
- `--max-rounds`：每阶段最大轮次
- `--dry-run`：启用本地模拟运行（不实际调用模型）
- `--ollama`：启用本地 Ollama provider
- `--ollama-model`：指定 Ollama 模型
- `--reviewer-hats`：指定评审帽子（逗号分隔）
- `--openai-base-url` / `--openai-model`：指定 OpenAI-compatible 端点与模型
- `--openai-provider`：新增 OpenAI-compatible 供应商（格式：`name,base_url,model,api_key_env`，可重复）
- `--role-provider`：按角色指定优先 provider（格式：`role=provider`，可重复）

## API（Commercial / 服务化）
基础路由：
- `POST /runs`：创建一次运行
- `GET /runs/{id}`：获取运行状态与摘要
- `GET /runs/{id}/artifacts`：获取产物
- `GET /runs/{id}/rounds`：获取轮次与日志
- `POST /runs/{id}/stop`：手动停止

## OpenAI-Compatible Provider 约定
请求关键字段：
- `model`：模型名称
- `messages`：对话消息数组（role + content）
- `temperature`：采样温度
- `max_tokens`：最大输出 token
- `response_format`（可选）：JSON 输出约束

响应关键字段：
- `choices[0].message.content`：模型输出内容
- `usage.prompt_tokens / completion_tokens / total_tokens`：token 统计

错误处理：
- Provider 错误需返回明确错误信息并触发 fallback。

## 供应商接入说明（新增）

### 可直连（推荐）
- 任何支持 OpenAI-compatible 协议的供应商可直接接入。
- 包括但不限于：Gemini、Claude、GLM、MiniMax、Kimi（前提是使用其兼容端点或网关）。

### 插件接入
- 若供应商无 OpenAI-compatible 端点，新增一个 Provider 插件实现 `BaseProvider` 即可。
- 插件最小要求：实现 `complete` 与 `estimate_cost`，并返回标准化 `CompletionResult`。

### 友好性定义
- 单供应商：只改环境变量（`BASE_URL/API_KEY/MODEL`）即可运行。
- 多供应商：通过 registry role map 与 candidates 顺序进行路由与 fallback。

环境变量扩展：
- `OPENAI_COMPAT_PROVIDERS_JSON`：多供应商 JSON 列表
- `ROLE_PROVIDER_MAP_JSON`：角色到 provider 的优先映射

详细接入步骤与验收清单见：`context/tech/provider-integration.md`

示例（多供应商 + 角色路由）：

```bash
refinery run \
  --idea "..." \
  --openai-provider "kimi,https://api.moonshot.cn/v1,moonshot-v1-8k,KIMI_API_KEY" \
  --openai-provider "glm,https://open.bigmodel.cn/api/paas/v4,glm-4.5,GLM_API_KEY" \
  --role-provider "author=kimi" \
  --role-provider "editor=glm"
```
