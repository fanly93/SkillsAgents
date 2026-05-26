# 短期记忆与任务追踪设计

## 1. 目标

系统需要做到：

- 短期记忆按 `session_id` 保存到 JSON 文档。
- 任务追踪按 `session_id` 生成 Markdown 文档。
- agent 能规划任务并制定计划。
- 每完成一项任务，在任务前的 `[ ]` 打上完成或失败标记。

本设计只描述文档和接口方案，不实现代码。

## 2. 短期记忆设计

短期记忆用于会话内上下文恢复，不等同于长期用户画像。

建议路径：

```text
data/sessions/{session_id}.json
```

建议 JSON 结构：

```json
{
  "session_id": "sess_123",
  "tenant_id": "tenant_a",
  "user_id": "user_456",
  "created_at": "2026-05-25T10:00:00Z",
  "updated_at": "2026-05-25T10:05:00Z",
  "messages": [
    {
      "role": "user",
      "content": "我的订单什么时候发货？",
      "created_at": "2026-05-25T10:00:10Z"
    }
  ],
  "summary": "用户询问订单发货时间。",
  "active_skills": [],
  "retrieval_context": [],
  "handoff": {
    "required": false,
    "reason": null
  }
}
```

建议字段：

- `session_id`：会话唯一 ID。
- `tenant_id`：租户。
- `user_id`：用户。
- `messages`：当前会话消息。
- `summary`：会话摘要，用于控制上下文长度。
- `active_skills`：已激活 skill。
- `retrieval_context`：最近检索结果摘要。
- `handoff`：是否需要人工转接。

## 3. 短期记忆写入策略

v1 默认：

- 每轮对话后写入 JSON。
- 写入前做 schema 校验。
- 写入采用原子替换，避免部分写入导致 JSON 损坏。
- 文件损坏时保留 `.corrupt` 备份并新建空 session。

后续可替换：

- Redis：适合高并发短期状态。
- Postgres：适合审计和查询。
- LangGraph checkpointer：适合深度依赖 LangGraph 状态恢复的场景。

由于系统要求可插拔，建议定义：

```python
class ShortTermMemoryStore:
    async def load(self, *, session_id: str) -> dict | None: ...
    async def save(self, *, session_id: str, state: dict) -> None: ...
    async def append_message(self, *, session_id: str, message: dict) -> None: ...
    async def summarize(self, *, session_id: str) -> dict: ...
    async def delete(self, *, session_id: str) -> None: ...
```

## 4. 任务追踪 Markdown 设计

建议路径：

```text
data/tasks/{session_id}.md
```

文档模板：

```markdown
# Task Plan: sess_123

**Tenant**: tenant_a
**User**: user_456
**Goal**: 帮用户确认订单发货状态
**Created**: 2026-05-25T10:00:00Z
**Updated**: 2026-05-25T10:05:00Z

## Tasks

- [ ] T001 确认用户要查询的订单号
- [ ] T002 查询知识库或业务说明中关于发货时效的政策
- [ ] T003 生成给用户的答复
- [ ] T004 判断是否需要转人工

## Notes

- 低置信度或缺少订单号时转人工。
```

状态约定：

- `[ ]`：未完成。
- `[x]`：完成。
- `[✗]`：失败。

失败任务建议追加原因：

```markdown
- [✗] T002 查询订单状态 API 失败
  - Reason: provider timeout after 10s
```

## 5. 任务生成策略

任务计划由 agent 根据用户目标生成，但应受系统约束：

- 每项任务必须可验证。
- 不生成越权任务。
- 不生成 v1 不支持的写操作任务，例如退款、改地址。
- 高风险任务必须标记“转人工”或“需人工审批”。
- 任务文本应面向客服操作，而不是模型内部推理。

任务粒度建议：

- 每轮用户请求生成 3-7 个任务。
- 复杂问题可分阶段。
- 短任务不要过度拆分。

## 6. TaskTracker 接口

```python
class TaskTracker:
    async def create_plan(
        self,
        *,
        tenant_id: str,
        user_id: str,
        session_id: str,
        goal: str,
        tasks: list[dict],
    ) -> str: ...

    async def mark_done(
        self,
        *,
        session_id: str,
        task_id: str,
        note: str | None = None,
    ) -> None: ...

    async def mark_failed(
        self,
        *,
        session_id: str,
        task_id: str,
        reason: str,
    ) -> None: ...

    async def get_markdown(
        self,
        *,
        session_id: str,
    ) -> str: ...
```

## 7. 与 agent 的协作方式

推荐流程：

1. 用户发起请求。
2. agent 判断是否需要新建或更新任务计划。
3. TaskTracker 写入 Markdown。
4. 每完成一个外部可观察步骤，agent 调用 TaskTracker 更新状态。
5. 如果步骤失败，标记 `[✗]` 并记录原因。
6. 回复用户时可包含任务摘要。
7. 转人工时把 Markdown 任务计划纳入 handoff payload。

## 8. 审计与一致性

任务状态变化应写审计日志：

- `task.plan.created`
- `task.item.completed`
- `task.item.failed`
- `task.plan.updated`
- `task.plan.handoff_attached`

生产建议：

- Markdown 是面向人类阅读的任务视图。
- 内部最好维护结构化任务 JSON，再渲染 Markdown。
- v1 如只写 Markdown，也应保证任务 ID 稳定。
- 更新 Markdown 时应避免误改用户手动追加的 notes。

## 9. 验收场景

- 给定新 `session_id`，系统能创建短期 JSON 记忆文件。
- 给定用户请求，系统能生成任务 Markdown。
- 完成任务后，对应 `[ ]` 更新为 `[x]`。
- 失败任务后，对应 `[ ]` 更新为 `[✗]` 并记录原因。
- 同一 `session_id` 再次请求能读取已有短期记忆和任务计划。
- 不同 `session_id` 的记忆和任务互不串扰。
