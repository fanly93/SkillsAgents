# Agent 系统架构调研与设计

## 1. 架构目标

本系统面向生产可用的智能客服 API 服务。核心目标不是构建一个强绑定 LangChain、Mem0 或某个云服务的应用，而是构建一个可插拔 agents 平台。

架构原则：

- API 服务与 agent runtime 解耦。
- Agent 编排与模型 provider 解耦。
- 短期记忆与长期记忆解耦。
- Memory provider 与具体框架解耦。
- Skill 格式与 skill runtime 解耦。
- RAG 检索与具体向量库/搜索引擎解耦。
- 任务追踪与具体存储解耦。
- 观测、评测、审计、安全护栏都以 provider 形式接入。

## 2. 推荐总体架构

```text
Client / Channel
    |
    v
API Service
    |
    +--> Auth & Tenant Context
    +--> Rate Limit / Idempotency
    |
    v
CustomerAgentOrchestrator
    |
    +--> AgentRuntimeAdapter (default: LangGraph)
    +--> ModelProvider
    +--> SkillSubsystem
    +--> ShortTermMemoryStore
    +--> LongTermMemoryProvider
    +--> RetrieverProvider
    +--> TaskTracker
    +--> HandoffService
    +--> GuardrailProvider
    +--> AuditSink
    +--> TraceProvider
```

## 3. API Service

API Service 是系统边界，负责：

- 接收渠道请求。
- 解析 tenant/user/session。
- 鉴权与限流。
- 请求 schema 校验。
- 幂等处理。
- 调用 orchestrator。
- 返回普通响应或流式响应。
- 写入审计日志和 trace。

v1 API 建议：

- `POST /v1/sessions`：创建会话。
- `POST /v1/chat`：发送用户消息。
- `GET /v1/sessions/{session_id}`：查询会话摘要。
- `GET /v1/tasks/{session_id}`：查询任务 Markdown。
- `GET /v1/skills`：列出 skills。
- `POST /v1/skills/reload`：重新扫描 skills。
- `POST /v1/handoff`：触发人工转接。
- `GET /v1/health`：健康检查。

## 4. AgentRuntimeAdapter

默认推荐 LangGraph：

- 用 graph 表达客服流程。
- 用 state 管理当前任务、消息、检索结果、skill 激活状态。
- 用 checkpointer 支持 thread-level persistence。
- 用 tool/node 连接 skills、RAG、memory、handoff。

但系统不应把 LangGraph 泄漏到业务接口中。建议定义：

```python
class AgentRuntimeAdapter:
    async def run_turn(self, *, context: dict, user_message: str) -> dict: ...
    async def stream_turn(self, *, context: dict, user_message: str): ...
```

这样未来可以替换为其他 orchestration runtime。

来源：

- https://docs.langchain.com/oss/python/langgraph/add-memory

## 5. ModelProvider

模型调用应可插拔：

```python
class ModelProvider:
    async def invoke(self, *, messages: list[dict], tools: list[dict], config: dict) -> dict: ...
    async def stream(self, *, messages: list[dict], tools: list[dict], config: dict): ...
```

需要支持：

- 多 provider：OpenAI、Anthropic、Gemini、本地模型。
- fallback 模型。
- token/cost 统计。
- 超时和重试。
- 工具调用 schema。
- 安全策略和 redaction。

## 6. SkillSubsystem

SkillSubsystem 由多个组件组成：

- `SkillSource`：skills 来源。
- `SkillParser`：解析 `SKILL.md`。
- `SkillRegistry`：注册和查询 skill。
- `SkillSelector`：选择 skill。
- `SkillActivationService`：激活 skill instructions。
- `ResourceResolver`：读取 references/assets。
- `ScriptExecutor`：受控执行 scripts。
- `PermissionPolicy`：授权。

Agent 只应通过受控工具访问 skill，不应直接读任意文件或执行任意命令。

## 7. Memory Layer

短期记忆：

- 按 `session_id` 存储。
- v1 默认 JSON 文件。
- 保存当前会话消息、摘要、任务状态、临时上下文。
- 适合恢复多轮对话，不等同于长期用户画像。

长期记忆：

- 通过 `LongTermMemoryProvider`。
- 默认 Mem0。
- 支持自定义 provider。
- 保存跨会话可复用信息，例如用户偏好、历史问题、长期上下文。
- 可配置写入策略：同步、异步、人工审核。

关键原则：

- memory provider 不可用时，客服主流程降级但不崩溃。
- 用户删除、租户隔离、PII 脱敏是 memory 层的基线要求。

## 8. RetrieverProvider

客服知识库/RAG 应抽象为：

```python
class RetrieverProvider:
    async def retrieve(
        self,
        *,
        tenant_id: str,
        user_id: str,
        query: str,
        filters: dict,
        limit: int,
    ) -> list[dict]: ...
```

可替换实现：

- 向量库检索。
- BM25/全文检索。
- 混合检索。
- reranker。
- Graph RAG。
- 企业搜索服务。

必须支持：

- tenant/user 权限过滤。
- 来源引用。
- 文档版本。
- 低置信度标记。
- prompt injection 风险处理。

## 9. TaskTracker

TaskTracker 负责：

- 根据用户请求和 agent 规划生成 Markdown checklist。
- 更新任务状态。
- 记录失败原因。
- 在 handoff 时向人工客服提供任务摘要。

建议接口：

```python
class TaskTracker:
    async def create_plan(self, *, session_id: str, goal: str, tasks: list[dict]) -> str: ...
    async def mark_done(self, *, session_id: str, task_id: str, note: str | None = None) -> None: ...
    async def mark_failed(self, *, session_id: str, task_id: str, reason: str) -> None: ...
    async def get_markdown(self, *, session_id: str) -> str: ...
```

## 10. HandoffService

人工转接是一等能力。触发条件：

- 用户明确要求人工。
- RAG 无依据或依据冲突。
- 多轮未解决。
- 安全护栏拦截。
- 涉及退款、投诉、法务、金融、医疗等高风险场景。
- 工具或 skill 失败超过阈值。

handoff payload 应包含：

- tenant/user/session。
- 会话摘要。
- 用户原始诉求。
- agent 已尝试步骤。
- RAG 引用来源。
- 已完成/失败/待办任务。
- 风险标签。
- 推荐人工下一步。

## 11. GuardrailProvider

安全护栏建议覆盖：

- 输入分类。
- Prompt injection 检测。
- PII 识别与脱敏。
- 输出过滤。
- 工具调用权限控制。
- 高风险动作阻断或要求人工审批。
- RAG 文档不可信处理。

来源：

- https://owasp.org/www-project-top-10-for-large-language-model-applications/
- https://www.nist.gov/itl/ai-risk-management-framework

## 12. Audit 与 Observability

AuditSink 记录不可变审计事件：

- 用户输入。
- agent 输出。
- skill 激活。
- script 执行。
- memory 读写。
- RAG 检索。
- handoff。
- 权限拒绝。
- 安全护栏拦截。

TraceProvider 记录调试和性能：

- LLM 调用。
- tool 调用。
- token/cost。
- latency。
- retrieval score。
- memory recall/write。

来源：

- https://docs.langchain.com/langsmith/observability-concepts
- https://docs.langchain.com/langsmith/evaluation
- https://opentelemetry.io/docs/
