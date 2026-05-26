# Quickstart: Skills Agent Runnable MVP

This quickstart describes how the completed MVP should be validated after implementation. It is part of planning, not an indication that the service already exists.

## 1. Prepare local configuration

Use the sample tenant configuration:

```text
examples/config/tenants.yaml
```

The sample configuration must define at least:

- `fashion_store`
- `electronics_store`

Each tenant must point to tenant-local skills and knowledge sources.

## 2. Run the service

After implementation, start the REST service from the repository root using the project command documented by the implementation.

Expected base URL:

```text
http://localhost:8000
```

The MVP must support deterministic local validation without external model credentials.

## 3. Verify health

```bash
curl http://localhost:8000/v1/health
```

Expected result:

- Overall status is `ok` or `degraded`.
- Provider health includes the mock model path and local storage path.

## 4. Reload skills for sample tenants

```bash
curl -X POST http://localhost:8000/v1/skills/reload \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"fashion_store"}'

curl -X POST http://localhost:8000/v1/skills/reload \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"electronics_store"}'
```

Expected result:

- Each tenant reports registered skills.
- Warnings are returned for invalid or ignored skill packages.
- Skills from one tenant are not listed for the other tenant.

## 5. Create sessions

```bash
curl -X POST http://localhost:8000/v1/sessions \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"fashion_store","user_id":"user_demo"}'

curl -X POST http://localhost:8000/v1/sessions \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"electronics_store","user_id":"user_demo"}'
```

Record the returned `session_id` values.

## 6. Ask the same question under both tenants

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id":"fashion_store",
    "user_id":"user_demo",
    "session_id":"<fashion_session_id>",
    "message":"I want to return my product. What should I do?"
  }'

curl -X POST http://localhost:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id":"electronics_store",
    "user_id":"user_demo",
    "session_id":"<electronics_session_id>",
    "message":"I want to return my product. What should I do?"
  }'
```

Expected result:

- Both calls complete successfully.
- Each response activates only tenant-enabled skills.
- Responses contain tenant-specific policy guidance.
- Responses include source references when local knowledge matches.
- Audit events are written for chat, skill activation, retrieval, memory, and task updates.

## 7. Verify explicit skill selection

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id":"fashion_store",
    "user_id":"user_demo",
    "session_id":"<fashion_session_id>",
    "skill_name":"<fashion_skill_name>",
    "message":"Use this skill to help me understand the policy."
  }'
```

Expected result:

- The explicitly requested tenant-local skill is selected.
- Selecting a skill that belongs only to another tenant is rejected or ignored safely.

## 8. Verify task checklist retrieval

```bash
curl "http://localhost:8000/v1/tasks/<fashion_session_id>?tenant_id=fashion_store"
```

Expected result:

- Markdown task checklist is returned.
- Task status includes pending, completed, or failed items.
- The task file is stored under the correct tenant.

## 9. Verify high-risk Human-in-the-loop behavior

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id":"fashion_store",
    "user_id":"user_demo",
    "session_id":"<fashion_session_id>",
    "message":"Please directly refund my order and change my delivery address."
  }'
```

Expected result:

- The system does not execute the requested business action.
- Response indicates `handoff_required` or `requires_human_approval`.
- A Human-in-the-loop payload is created under the tenant's handoff artifacts.
- Audit events capture the guardrail decision and handoff payload generation.

## 10. Verify local artifacts

After the scripted flows, validate tenant-local artifacts:

```text
data/tenants/fashion_store/sessions/
data/tenants/fashion_store/tasks/
data/tenants/fashion_store/memory/
data/tenants/fashion_store/audit/events.jsonl
data/tenants/fashion_store/handoff/
```

Expected result:

- Files exist only under the correct tenant.
- No tenant can retrieve another tenant's session, task, skill, knowledge, audit, or handoff artifact.

## 11. Validation checklist

The quickstart passes when:

- Two sample tenants can be exercised independently.
- Same question produces tenant-specific skill and policy behavior.
- Session JSON, task Markdown, memory JSON, audit JSONL, and handoff payloads are generated as applicable.
- High-risk actions enter Human-in-the-loop.
- The entire flow works without external model credentials.
