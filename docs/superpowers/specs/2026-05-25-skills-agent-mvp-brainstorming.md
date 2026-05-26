# Skills Agent MVP Brainstorming Design

> 本文档是 Superpowers brainstorming 阶段产物，用于梳理项目基调、MVP 边界、架构方向和验收标准。
> 它是后续 `speckit-specify` 的上游参考材料，不是最终正式规范文档。
> 最终 `spec.md`、`plan.md`、`tasks.md` 仍必须由 Spec Kit 生成和维护。

## 1. 项目基调

本项目第一阶段目标是构建一个可运行的通用 Agent 平台骨架，而不是构建单一电商客服 bot。

平台默认以智能客服为场景，以电商多租户作为样例域，通过 `tenant_id + skill sources + knowledge + memory + task tracking` 证明：

- 同一个通用 Agent runtime 可以服务多个商户。
- 不同商户通过不同 skills 和知识库获得领域专家效果。
- 系统核心能力依赖抽象接口，不强绑定某个模型、memory provider、RAG 引擎、渠道、观测平台或脚本执行器。

MVP 采用“平台骨架优先”方案：实现完整可插拔骨架，但每个 provider 都用本地最小实现跑通。

## 2. MVP 总边界

MVP 必须可运行，但不追求生产完备。

MVP 主线包括：

- Skills 加载闭环：多本地 skill source 扫描、解析 `SKILL.md`、tenant 内 skill registry、显式/关键词选择、按需激活。
- 会话与任务闭环：按 `session_id` 保存短期 JSON memory，生成和更新 Markdown task tracking。
- 平台可插拔骨架：定义 provider/adapter 边界，并用本地最小实现跑通 model、runtime、memory、retriever、audit、guardrail、handoff、script executor。
- 多租户样例验证：用服装电商和数码电商两个 tenant 展示不同 skills、不同知识库、不同回复路径。
- REST API 验收：不做前端，只做 REST API、样例请求、自动化测试和文档。

MVP 不包含：

- 完整客服坐席系统。
- 远程 skill registry 实现。
- 生产级鉴权、RBAC、管理员后台。
- 向量库、embedding 检索、reranker 或 Graph RAG。
- 真实客服系统对接。
- 自动退款、改订单、改地址、改账号权限等高风险业务写操作。
- SSE/WebSocket 流式聊天。

## 3. 核心架构

MVP 采用分层架构。API 层只负责 HTTP 边界、请求校验、tenant/user/session 上下文、调用 orchestrator 和返回结果。

真正的 agent 执行由 `CustomerAgentOrchestrator` 统一协调。Orchestrator 不直接绑定具体实现，而是依赖抽象接口。

核心组件：

- `AgentRuntimeAdapter`：默认实现为 `LangGraphAgentRuntimeAdapter`。业务层只调用 `run_turn(...)`，不直接依赖 LangGraph graph、node、state 细节。
- `ModelProvider`：支持真实 OpenAI-compatible provider 和 `MockModelProvider`。
- `SkillSubsystem`：包含 `SkillSource`、`SkillParser`、`SkillRegistry`、`SkillSelector`、`SkillActivationService`、`ResourceResolver`。
- `ShortTermMemoryStore`：MVP 用 tenant 分层 JSON 文件保存 session state。
- `LongTermMemoryProvider`：MVP 用本地 JSON fallback provider，未来可替换 Mem0、Zep、Cognee、Supermemory 等。
- `RetrieverProvider`：MVP 用本地 Markdown/TXT 关键词检索，未来可替换向量库、BM25、reranker、Graph RAG。
- `TaskTracker`：生成和更新 Markdown checklist。
- `ScriptExecutor` + `PermissionPolicy`：MVP 提供本地受控执行器，严格限制路径、超时、参数和输出。
- `GuardrailProvider`：MVP 用规则型护栏识别高风险、越权、prompt injection 和敏感信息场景。
- `HandoffService`：MVP 生成 handoff payload 文件，后续扩展为 API 和客服窗口对接。
- `AuditSink`：MVP 写 tenant 级 JSONL，后续扩展结构化审计和查询 API。
- `ConfigProvider`：MVP 使用 YAML + 环境变量，未来可替换为数据库或配置中心。

主流程：

```text
REST API
  -> CustomerAgentOrchestrator
  -> GuardrailProvider
  -> Skill selection / activation
  -> Memory read
  -> RetrieverProvider
  -> AgentRuntimeAdapter / ModelProvider
  -> TaskTracker
  -> Memory write
  -> AuditSink
  -> Response
```

## 4. 多租户与数据边界

MVP 要做轻量但真实的多租户隔离。`tenant_id` 是配置、skill registry、knowledge、session、task、memory、audit 和 handoff 的主隔离键。

默认数据结构：

```text
data/
└── tenants/
    └── {tenant_id}/
        ├── sessions/
        │   └── {session_id}.json
        ├── tasks/
        │   └── {session_id}.md
        ├── memory/
        │   └── {user_id}.json
        ├── knowledge/
        │   ├── faq.md
        │   └── policy.txt
        ├── handoff/
        │   └── {session_id}.json
        └── audit/
            └── events.jsonl
```

每个 tenant 可以在 YAML 配置中声明：

- `display_name`
- `skill_sources`
- `knowledge_paths`
- `enabled_providers`
- `guardrail_policy`
- `script_permissions`

MVP 支持多个本地 `SkillSource`，例如：

```text
skills/common/
skills/tenants/fashion_store/
skills/tenants/electronics_store/
.agents/skills/
```

接口上保留 `RemoteSkillSource` 扩展点，但第一阶段不实现远程 registry、远程同步、远程鉴权和供应链治理。

关键约束：

- tenant A 不能看到 tenant B 的 skills、session、task、memory、knowledge、audit。
- skill selection 只在当前 tenant 启用的 registry 中发生。
- 所有 provider 调用都必须显式传入 `tenant_id`。
- MVP 可以不做完整 API key/JWT，但设计不能阻断未来接入鉴权。

## 5. Skills 系统

MVP skills 采用目录型结构：

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

`SKILL.md` 是唯一必需文件，包含 YAML frontmatter 和 Markdown instructions。`references/`、`scripts/`、`assets/` 都是可选资源。系统可以兼容误写的 `asserts/`，但应产生 warning，并仍以 `assets/` 作为正式标准目录名。

### Discovery

MVP skill discovery 流程：

1. 从当前 tenant 配置的多个本地 skill source 扫描 skill root。
2. 只读取 `SKILL.md` frontmatter 和必要摘要，生成 registry entry。
3. 校验目录边界，防止 symlink/path traversal 逃逸。
4. 校验 `name`、`description`、`version` 等基础字段。
5. 计算 checksum，记录 source、root path、enabled 状态。
6. 同名冲突在同一 tenant 内应报错或要求 namespace。
7. 激活 skill 时才读取完整 `SKILL.md` body 和资源清单。

### Selection

MVP skill selection 支持：

- 请求显式指定 `skill_id` 或 `skill_name`。
- 未指定时，使用 `name`、`description`、tags/metadata 做关键词匹配。
- 只在当前 tenant 启用的 skills 内选择。

必须定义 `SkillSelector` 接口，未来可组合：

- `ExplicitSelector`
- `KeywordSelector`
- `EmbeddingSelector`
- `LLMSelector`
- `PolicySelector`
- `CompositeSelector`

MVP 只实现 `ExplicitSelector` 和 `KeywordSelector`。

### Activation

MVP skill activation 输出：

- skill instructions
- 资源清单
- 权限摘要
- checksum

skill instructions 只能指导 agent，不能覆盖系统策略、租户策略、安全策略。每次激活必须写 audit event。

`references/` 和 `assets/` 只能通过 `ResourceResolver` 受控读取。`scripts/` 只能通过 `ScriptExecutor + PermissionPolicy` 受控执行，模型不能直接执行命令。

## 6. REST API 与 Agent 运行流程

MVP 只做 REST 非流式 API，不做前端、不做 SSE/WebSocket。但接口设计保留未来 `stream_turn(...)` 和流式响应扩展空间。

建议 MVP API：

- `POST /v1/sessions`：创建 session，输入 `tenant_id`、`user_id`，返回 `session_id`。
- `POST /v1/chat`：发送一轮消息，输入 `tenant_id`、`user_id`、`session_id`、`message`，可选 `skill_id` 或 `skill_name`。返回 agent 回复、激活 skill、任务摘要、sources、handoff 状态、risk tags。
- `GET /v1/tasks/{session_id}`：读取当前 tenant 下该 session 的 Markdown task tracking。请求需带 `tenant_id`。
- `GET /v1/skills`：列出当前 tenant 可用 skills，返回 name、description、version、source、enabled、checksum。
- `POST /v1/skills/reload`：重新扫描当前 tenant 的 skill sources。
- `GET /v1/health`：返回 API、runtime、provider、storage 的基础健康状态。

一轮 `POST /v1/chat` 的推荐流程：

1. 校验 tenant/user/session。
2. 写入用户消息到 short-term memory。
3. 运行规则型 guardrail，识别风险和 Human-in-the-loop 条件。
4. 根据显式参数或关键词选择 skill。
5. 激活 skill，读取 instructions 和资源清单。
6. 根据 tenant knowledge 做本地关键词检索，返回 sources。
7. 生成或更新任务计划。
8. 调用 `AgentRuntimeAdapter.run_turn(...)`，默认走 LangGraph adapter，内部使用 `ModelProvider`。
9. 更新任务 Markdown 状态。
10. 写入长期 memory fallback 中可复用的摘要或偏好。
11. 必要时生成 approval/handoff payload。
12. 写 audit JSONL。
13. 返回结构化响应。

## 7. Human-in-the-loop 决策门

高风险场景统一进入 Human-in-the-loop 决策门，而不是简单写成“转人工”。

风险分层：

- 低风险：agent 可直接回答或执行只读工具。
- 中风险：agent 可生成建议，但需要用户确认后继续。
- 高风险：agent 不执行动作，只生成 `approval_request` 或 `handoff_payload`。
- 禁止类：直接拒绝，并记录 audit，例如越权访问、泄露密钥、绕过系统策略。

MVP 实现最小版：

- 规则型 `GuardrailProvider` 判断风险等级。
- `HandoffService` 生成 payload。
- API response 中返回 `risk_level`、`risk_tags`、`requires_human_approval`、`handoff_required`、`approval_request`。
- 不实现审批 API，不接人工客服窗口，不执行高风险动作。

后续生产版可扩展：

- `POST /v1/approvals` 创建审批请求。
- `GET /v1/approvals/{id}` 查询审批状态。
- 人工客服或管理员 approve/reject。
- agent 只在 approved 后执行受控工具。
- 所有审批、执行、拒绝写入审计。
- 高风险动作必须具备幂等、回滚、权限校验和业务侧二次确认。

## 8. Memory、Task、Audit 与 Handoff 产物

### Short-term memory

按 `tenant_id + session_id` 保存 JSON：

```text
data/tenants/{tenant_id}/sessions/{session_id}.json
```

内容包括 messages、summary、active skills、recent retrieval context、risk tags、handoff 状态等。每轮 chat 后写入，写入应采用 schema 校验和原子替换。文件损坏时保留 `.corrupt` 备份并安全新建。

### Long-term memory fallback

按 `tenant_id + user_id` 保存 JSON：

```text
data/tenants/{tenant_id}/memory/{user_id}.json
```

MVP 只保存可复用的轻量信息，例如用户偏好、历史问题摘要、常见诉求标签。

必须定义 `LongTermMemoryProvider`。本地 JSON provider 只是 fallback，后续可替换 Mem0、Zep、Cognee、Supermemory 等。

### Task tracking

按 `tenant_id + session_id` 保存 Markdown：

```text
data/tenants/{tenant_id}/tasks/{session_id}.md
```

任务状态：

- `[ ]` 未完成
- `[x]` 完成
- `[✗]` 失败

任务计划采用混合生成：默认规则模板；真实 LLM 可用时可生成计划，但必须经过规则约束。

约束：

- 任务数量必须合理。
- 任务必须是外部可观察步骤。
- 任务不能包含越权或高风险写操作。
- 高风险动作只能变成“请求人工审批/转人工”的任务项。

### Audit

按 tenant 写 JSONL：

```text
data/tenants/{tenant_id}/audit/events.jsonl
```

记录 session、chat、skill activation、script execution、memory、task、retrieval、guardrail、approval/handoff 等关键事件。

MVP 不做查询 API，但后续可扩展数据库审计和管理查询接口。

### Handoff / Approval payload

高风险、低置信度、用户要求人工、工具失败等情况，MVP 生成 payload：

```text
data/tenants/{tenant_id}/handoff/{session_id}.json
```

payload 包含：

- `tenant_id`
- `user_id`
- `session_id`
- 用户原始诉求
- 会话摘要
- 完整消息或摘要
- 已激活 skills
- 任务状态
- sources
- risk tags
- Human-in-the-loop 原因
- 建议人工下一步

未来可扩展为审批 API、人工客服窗口对接和 approve/reject 流程。

## 9. Script 执行边界

MVP 定义 `ScriptExecutor` 抽象和 `PermissionPolicy`。

MVP 提供 `LocalControlledScriptExecutor`，仅用于低风险开发环境。它必须满足：

- `scripts/` 默认不可执行。
- 只能执行当前 tenant 当前 skill 内、被策略显式授权的脚本。
- 禁止任意 shell 字符串执行。
- 输入输出使用结构化 JSON。
- 限制工作目录，防止路径逃逸。
- 限制超时、输出大小。
- 默认无网络、无 secrets。
- 执行请求、授权结果、执行结果都必须写 audit。

Docker、Firecracker、gVisor、Kubernetes Job 等生产沙箱只作为后续扩展点。

## 10. 配置方式

MVP 使用 YAML + 环境变量。

YAML 管结构化配置：

- tenants
- 每个 tenant 的 skill sources
- knowledge paths
- data root
- enabled providers
- guardrail policy
- script permission policy

环境变量管敏感和环境相关配置：

- LLM API key
- LLM base URL
- model name
- provider 开关
- runtime mode

必须提供 example 配置，不把真实密钥写入仓库。

配置加载层也要抽象，后续可替换为数据库、远程配置中心或管理后台。

## 11. MVP 样例域

MVP 样例域使用两个不同垂类电商 tenant，证明同一个通用 Agent 平台可以通过不同 skills 和知识库变成不同商户专家。

### `fashion_store`

服装电商。

示例 skills：

- 发货政策
- 尺码/换货
- 退货条件
- 改地址风险
- 人工作业升级

知识库：

- 发货时效
- 退换货政策
- 尺码问题说明

### `electronics_store`

数码电商。

示例 skills：

- 保修售后
- 拆封退货限制
- 发票/序列号
- 物流签收风险
- 人工作业升级

知识库：

- 保修政策
- 退货限制
- 发票规则
- 签收注意事项

## 12. 验收标准

手动/API 演示应至少覆盖：

1. 创建两个不同 tenant 的 session。
2. 对两个 tenant 提同一个问题，例如“我想退货”，返回不同 skill 和不同政策答案。
3. 对两个 tenant 提高风险问题，例如“帮我直接退款/改地址”，触发 Human-in-the-loop payload，而不是执行动作。
4. 对一个 tenant 显式指定 skill，验证显式选择优先。
5. 验证 session JSON、task Markdown、memory JSON、audit JSONL、handoff payload 都按 tenant 分层落盘。
6. 验证 tenant A 不能读取 tenant B 的 skills/tasks/session。
7. 验证无 LLM key 时，Mock provider 仍可跑通核心闭环。
8. 验证真实 LLM provider 配置后可替换 mock provider。
9. 验证本地知识库检索返回 sources。
10. 验证 script executor 只执行被 permission policy 明确允许的脚本。

自动化测试应覆盖：

- skill discovery / parser / registry / selector
- tenant isolation
- short-term memory store
- long-term memory fallback
- task tracker markdown rendering
- local document retriever
- rule-based guardrail
- handoff/approval payload generation
- audit JSONL writing
- script permission deny/allow
- mock model deterministic response
- REST API integration happy path

MVP 完成标准不是“客服能力完美”，而是平台骨架稳定、边界清晰、可演示、可测试，并能为后续 Spec Kit `spec.md` 提供高质量输入。

## 13. 后续进入 Spec Kit 的输入要点

后续运行 `speckit-specify` 时，应基于本文档生成正式 `spec.md`。

Spec Kit 阶段需要特别保留：

- 第一阶段是可运行 MVP，不是纯研究包，也不是生产试点版。
- 主线是 skills 加载闭环 + 会话与任务闭环。
- 采用平台骨架优先，而不是客服业务体验优先。
- 多租户必须轻量但真实隔离。
- MVP 必须能通过 Mock provider 无外部 key 跑通。
- MVP 默认 REST 非流式，无前端。
- 高风险业务动作统一进入 Human-in-the-loop 决策门。
- 正式规范文档只能由 Spec Kit 生成和维护。
