# Data Model: Skills Agent Runnable MVP

## Overview

All persisted MVP data is tenant-scoped. `tenant_id` is the root isolation key for skills, knowledge, sessions, tasks, memory, audit, and Human-in-the-loop payloads.

Default artifact layout:

```text
data/
└── tenants/
    └── {tenant_id}/
        ├── sessions/
        ├── tasks/
        ├── memory/
        ├── knowledge/
        ├── handoff/
        └── audit/
```

## Entities

### Tenant

Represents a merchant or business context.

**Fields**:

- `tenant_id`: stable tenant identifier.
- `display_name`: human-readable tenant name.
- `skill_sources`: ordered list of tenant-enabled local skill source roots.
- `knowledge_paths`: ordered list of tenant-local knowledge files or directories.
- `enabled_providers`: provider settings enabled for this tenant.
- `guardrail_policy`: tenant-level high-risk and safety rule configuration.
- `script_permissions`: allowlist policy for skill scripts.

**Validation rules**:

- `tenant_id` is required for every user-facing operation.
- Tenant paths must resolve under configured project roots.
- A tenant cannot reference another tenant's data directory.

**Relationships**:

- Owns many sessions, skill registry entries, task checklists, memory records, audit events, knowledge sources, and handoff payloads.

### User

Represents a customer or operator in a tenant-scoped session.

**Fields**:

- `tenant_id`: owning tenant.
- `user_id`: stable user identifier within tenant.
- `profile_summary`: optional lightweight summary derived from long-term memory.

**Validation rules**:

- `user_id` is required for session creation and chat.
- `user_id` is scoped by tenant; the same value in different tenants represents different users.

**Relationships**:

- Has many sessions.
- Has zero or one long-term memory record per tenant.

### Session

Represents a tenant-scoped conversation.

**Fields**:

- `tenant_id`
- `session_id`
- `user_id`
- `created_at`
- `updated_at`
- `status`: `active`, `handoff_required`, `closed`
- `messages`: ordered conversation messages.
- `summary`: concise session summary.
- `active_skills`: activated skill identifiers and versions.
- `recent_sources`: retrieval source references used in recent turns.
- `risk_tags`: risk labels detected in the session.
- `handoff`: summary of current Human-in-the-loop state.

**Validation rules**:

- `session_id` must be unique within a tenant.
- Session reads and writes require matching `tenant_id`.
- Message order must be preserved.

**State transitions**:

```text
active -> handoff_required -> closed
active -> closed
```

### Message

Represents a single session turn.

**Fields**:

- `role`: `user`, `assistant`, `system`, or `tool`.
- `content`: message text.
- `created_at`
- `metadata`: optional risk tags, skill references, or retrieval references.

**Validation rules**:

- User messages must not be empty.
- Stored metadata must not contain raw secrets.

### Skill Package

Represents a discovered skill directory.

**Fields**:

- `tenant_id`
- `skill_id`
- `name`
- `description`
- `version`
- `source`
- `root_path`
- `checksum`
- `enabled`
- `declared_permissions`
- `granted_permissions`
- `resource_manifest`
- `warnings`

**Validation rules**:

- `SKILL.md` is required.
- `name` and `description` are required for selection.
- Resolved paths must stay inside the skill root.
- Same-tenant name conflicts must be rejected or require namespace disambiguation.

**Relationships**:

- May have references, assets, and scripts.
- May be activated by sessions.

### Skill Activation

Represents one session's use of a skill.

**Fields**:

- `tenant_id`
- `session_id`
- `skill_id`
- `skill_name`
- `version`
- `checksum`
- `activated_at`
- `selection_reason`: `explicit`, `keyword`, or `fallback`
- `resource_manifest`

**Validation rules**:

- Activated skill must be enabled for the current tenant.
- Activation must be audited.

### Task Checklist

Represents a human-readable task plan for one session.

**Fields**:

- `tenant_id`
- `session_id`
- `goal`
- `created_at`
- `updated_at`
- `items`: ordered task items.
- `notes`

**Validation rules**:

- Stored Markdown must preserve stable task IDs.
- Task items must be external, observable steps.
- High-risk actions cannot be executable tasks; they must become review or handoff tasks.

### Task Item

Represents one task line in a checklist.

**Fields**:

- `task_id`
- `description`
- `status`: `pending`, `completed`, `failed`
- `note`
- `failure_reason`
- `updated_at`

**State transitions**:

```text
pending -> completed
pending -> failed
failed -> pending     # allowed only when retrying or regenerating the plan
```

### Long-term Memory Record

Represents reusable user information scoped by tenant.

**Fields**:

- `tenant_id`
- `user_id`
- `facts`: lightweight remembered facts.
- `preferences`: user preferences.
- `issue_summaries`: prior issue summaries.
- `intent_tags`: common customer intent labels.
- `updated_at`

**Validation rules**:

- Memory must be scoped by both tenant and user.
- Sensitive information should be minimized and redacted when stored.
- Provider-specific IDs must not leak into business contracts.

### Knowledge Source

Represents tenant-local support content.

**Fields**:

- `tenant_id`
- `source_id`
- `path`
- `title`
- `content_type`
- `checksum`
- `last_indexed_at`

**Validation rules**:

- Path must resolve under the tenant's configured knowledge path.
- Retrieved snippets must include source references.

### Retrieval Result

Represents one matched knowledge snippet.

**Fields**:

- `tenant_id`
- `source_id`
- `title`
- `path`
- `snippet`
- `score`
- `metadata`

**Validation rules**:

- Results must come from the current tenant's knowledge sources.
- A no-match result must not be turned into unsupported factual claims.

### Audit Event

Represents an append-only record of critical behavior.

**Fields**:

- `event_id`
- `tenant_id`
- `user_id`
- `session_id`
- `event_type`
- `created_at`
- `actor`
- `resource`
- `decision`
- `metadata`

**Validation rules**:

- Critical events must be written for chat turns, skill activation, script decisions, memory access, task updates, retrieval, guardrail decisions, and handoff payload generation.
- Sensitive fields must be redacted or omitted.

### Guardrail Decision

Represents safety classification for a request or response.

**Fields**:

- `tenant_id`
- `session_id`
- `risk_level`: `low`, `medium`, `high`, `blocked`
- `risk_tags`
- `decision`: `allow`, `block`, `handoff_required`, `requires_approval`
- `reason`
- `redactions`

**Validation rules**:

- High-risk business actions must not execute automatically.
- Cross-tenant access attempts must be blocked.

### Script Execution Request

Represents a controlled request to run a skill script.

**Fields**:

- `tenant_id`
- `session_id`
- `skill_id`
- `script_path`
- `input`
- `authorization_decision`
- `status`: `denied`, `completed`, `failed`, `timed_out`
- `output_summary`

**Validation rules**:

- Default authorization is deny.
- Script path must stay under the skill root.
- Inputs and outputs must be structured.
- Authorization and execution result must be audited.

### Human-review Payload

Represents context prepared for Human-in-the-loop review.

**Fields**:

- `tenant_id`
- `user_id`
- `session_id`
- `created_at`
- `reason`
- `risk_tags`
- `session_summary`
- `messages_or_summary`
- `activated_skills`
- `task_status`
- `sources`
- `agent_attempted_steps`
- `recommended_next_steps`
- `status`: `created`, `review_pending`, `resolved`

**Validation rules**:

- Payload must not execute the requested high-risk action.
- Payload must contain enough context for a human operator to continue the case.

**State transitions**:

```text
created -> review_pending -> resolved
created -> resolved
```
