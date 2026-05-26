# 长期记忆框架调研

## 1. 结论摘要

长期记忆层应设计成可插拔 `LongTermMemoryProvider`，Mem0 作为 v1 默认实现，但业务层不能直接依赖 Mem0 SDK。LangGraph memory 适合作为 agent 状态和本地 fallback；LangMem 适合作记忆抽取和整理器；Zep/Graphiti、Cognee 适合更复杂的图谱和企业知识场景；Letta 更像完整 stateful agent runtime；Supermemory 适合 MCP 和跨工具记忆。

推荐落地顺序：

1. `LongTermMemoryProvider` 抽象接口。
2. `Mem0MemoryProvider` 作为默认长期记忆实现。
3. `LangGraphStoreMemoryProvider` 作为本地开发和无外部服务 fallback。
4. `LangMemMemoryManager` 作为可选记忆抽取/整理组件。
5. 后续按场景扩展 `ZepMemoryProvider`、`GraphitiMemoryProvider`、`CogneeMemoryProvider`、`SupermemoryProvider`。
6. Letta 作为独立 runtime adapter 评估，不建议 v1 绑定。

## 2. 对比表

| 框架 | 定位 | 开源/托管 | 接入方式 | 优点 | 风险 | 适用场景 |
|---|---|---|---|---|---|---|
| LangGraph memory | LangChain 生态内的状态、短期记忆和长期 store 基础设施 | OSS，可配 LangGraph Platform/LangSmith | `checkpointer` 做 thread 状态，`store` 做长期 namespace/key 数据 | 与 LangGraph 原生集成，适合做系统骨架 | 不是完整记忆产品，记忆提取、冲突处理、治理要自己做 | agent 编排、会话状态、本地 fallback |
| LangMem | LangChain 团队的记忆管理库 | OSS | memory manager、memory tools、LangGraph Store | 支持热路径/后台记忆提取，贴合 LangGraph | 更偏 library，不是独立服务 | 结构化记忆抽取、记忆整理 |
| Mem0 | 通用 AI agent memory layer | OSS + Cloud + self-host server | Python/Node SDK、REST server | 上手快，适合 v1 默认长期记忆；支持自托管和可配置组件 | 默认依赖 LLM、embedding、vector store，需要 adapter 防锁定 | 用户偏好、客服上下文、长期个人记忆 |
| Zep/Graphiti | temporal knowledge graph / agent memory | Zep 托管，Graphiti OSS | Zep SDK/API 或 Graphiti Python | 时间知识图谱、fact invalidation、Graph RAG | 图谱建模和运维复杂 | 时变事实、关系推理、业务数据融合 |
| Cognee | AI memory / knowledge engine | OSS + Cloud | Python SDK、HTTP API、MCP | vector + graph + relational provenance，适合企业知识库 | 比 Mem0 更重，配置项更多 | 企业知识库、历史工单、多数据源融合 |
| Letta | memory-first stateful agents 平台 | OSS + hosted API + CLI/app | Letta API/SDK | 完整 agent 状态、memory blocks、工具、消息持久化 | 容易接管整个 agent 架构 | 采用完整 stateful agent runtime 时 |
| Supermemory | Memory API + MCP 跨工具记忆层 | 开源 MCP + hosted API | SDK、REST、MCP tools | MCP 生态友好，跨工具记忆方便 | 更偏托管 API，完全自托管需确认 | 跨 AI 工具共享记忆、MCP 场景 |

## 3. LangGraph Memory

LangGraph 官方将 memory 分为：

- 短期记忆：作为 agent state 的一部分，通常通过 checkpointer 做 thread-level persistence。
- 长期记忆：用于跨会话保存用户级或应用级数据，通常通过 store 接口访问。

调研要点：

- `checkpointer` 适合会话内多轮状态，不应直接等同于长期记忆产品。
- `store` 提供 namespace/key/value 形态的持久化接口，适合作为通用抽象或本地 fallback。
- 生产场景中，LangGraph 的 InMemory 实现会丢失数据，应替换为数据库型 store。

来源：

- https://docs.langchain.com/oss/python/langgraph/add-memory

## 4. LangMem

LangMem 是 LangChain 团队维护的 memory management 库。它提供：

- core memory API。
- agent 可使用的 manage/search memory tools。
- 后台 memory manager，用于抽取、整合和更新 agent knowledge。
- 与 LangGraph Long-term Memory Store 的原生集成。

调研结论：

- LangMem 更适合作“记忆抽取器/整理器”，不一定作为唯一 memory provider。
- 它可以放在 `MemoryManager` 层，而不是直接替代 `LongTermMemoryProvider`。
- 如果系统主要使用 LangGraph，LangMem 是很自然的增强组件。

来源：

- https://github.com/langchain-ai/langmem

## 5. Mem0

Mem0 定位为 AI agents 和 assistants 的 memory layer。OSS 版本支持：

- Python SDK 和 Node.js SDK。
- 作为库嵌入应用，或以 self-hosted server 运行。
- 可配置 LLM、embedding、vector store、reranker。
- 自托管以满足数据控制和合规需求。

调研结论：

- Mem0 适合作为 v1 默认长期记忆实现，因为接口语义接近 `add/search`，接入成本低。
- 但业务层必须只依赖 `LongTermMemoryProvider`，避免把 Mem0 的 memory id、metadata shape、过滤语义泄漏到核心业务。
- 配置中可以默认启用 Mem0，但必须允许 `custom` provider。

来源：

- https://docs.mem0.ai/open-source/overview
- https://docs.mem0.ai/

## 6. Zep 与 Graphiti

Zep 是 agent memory / context engineering 平台，Graphiti 是 Zep 的开源 temporal knowledge graph 引擎。Zep 文档强调：

- Knowledge Graph 是 memory store。
- 节点表示实体，边表示事实和关系。
- Fact invalidation 可以记录事实何时失效。
- Memory Context String 可为 agent 提供相关事实和实体。

Graphiti 适合构建时间感知知识图谱，支持增量更新、hybrid search、custom entities。

调研结论：

- 当客服场景需要处理“事实随时间变化”时，Zep/Graphiti 很有价值。
- 例如用户地址变更、订阅状态变化、企业客户关系、历史投诉状态。
- v1 不建议直接默认使用图谱记忆，因为图建模和运维成本更高。

来源：

- https://help.getzep.com/docs
- https://help.getzep.com/graphiti/getting-started/welcome
- https://github.com/getzep/graphiti

## 7. Cognee

Cognee 将数据组织成 AI memory，官方描述其核心操作包括：

- `remember`：存储文本、文件或 URL，并构建知识图谱。
- `recall`：自然语言查询 memory。
- `improve`：对已有 memory 做 enrichment。
- `forget`：删除 memory。

调研结论：

- Cognee 适合企业知识库和知识图谱方向，而不只是用户偏好记忆。
- 如果客服系统未来要把产品文档、历史工单、FAQ、邮件等统一成 graph + vector 的长期知识层，Cognee 值得评估。
- v1 可作为二期 provider，不建议压到第一阶段默认依赖里。

来源：

- https://docs.cognee.ai/getting-started/introduction
- https://docs.cognee.ai/core-concepts/overview

## 8. Letta

Letta 是 memory-first stateful agents 平台。其文档强调：

- stateful agent 可维护跨会话 memory 和 context。
- 所有状态、用户消息、reasoning、tool calls 都持久化在数据库中。
- memory blocks 可注入 context，agent 可通过工具修改自己的 memory。

调研结论：

- Letta 强在完整 stateful agent runtime，而不是薄 memory provider。
- 如果采用 Letta，可能会影响 agent 编排、工具执行、消息状态等整体架构。
- 对本项目而言，Letta 更适合作未来可选 runtime adapter，不适合作默认长期记忆后端。

来源：

- https://www.letta.com/
- https://docs.letta.com/guides/core-concepts/stateful-agents

## 9. Supermemory

Supermemory 提供 Memory API 和 MCP server，强调跨 AI 工具的持久记忆。其 MCP 文档描述：

- 通过 MCP 让不同 AI 客户端共享 memory。
- 支持 OAuth、API key、project scoping。
- 提供 memory、recall、profile/context 等能力。

调研结论：

- Supermemory 适合跨工具共享记忆和 MCP 生态集成。
- 如果客服系统未来支持 MCP 或希望用户在多个 agent 工具之间共享记忆，可作为 provider。
- v1 默认不建议绑定，因为本项目核心是客服 API 服务，不是个人跨工具记忆产品。

来源：

- https://supermemory.ai/docs/supermemory-mcp/introduction
- https://supermemory.ai/mcp/

## 10. 推荐抽象接口

```python
class LongTermMemoryProvider:
    async def add(
        self,
        *,
        tenant_id: str,
        user_id: str,
        session_id: str | None,
        content: str,
        metadata: dict,
    ) -> dict: ...

    async def search(
        self,
        *,
        tenant_id: str,
        user_id: str,
        query: str,
        limit: int,
        filters: dict | None = None,
    ) -> list[dict]: ...

    async def get_profile(
        self,
        *,
        tenant_id: str,
        user_id: str,
    ) -> dict | None: ...

    async def delete(
        self,
        *,
        tenant_id: str,
        user_id: str | None = None,
        memory_id: str | None = None,
        filters: dict | None = None,
    ) -> dict: ...

    async def health(self) -> dict: ...
```

Provider capability 建议：

```python
capabilities = {
    "structured_memory": False,
    "profile": False,
    "graph": False,
    "temporal_facts": False,
    "hybrid_search": False,
    "self_hosted": False,
}
```

## 11. 设计原则

- 业务层只调用抽象接口，不直接调用 Mem0、Zep、Cognee SDK。
- 每个 provider 必须实现租户隔离：`tenant_id` 和 `user_id` 是所有读写的必传上下文。
- memory provider 失败不应阻断客服主流程，应降级为无长期记忆模式。
- 短期记忆和长期记忆分离，避免把完整聊天记录全部写入长期记忆。
- 长期记忆写入应可配置为同步、异步或人工审核后写入。
- 支持数据删除、保留期、审计和 PII 脱敏。
