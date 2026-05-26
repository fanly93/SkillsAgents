# Tasks: Skills Agent Runnable MVP

**Input**: Design documents from `/specs/001-skills-agent-mvp/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/openapi.yaml](./contracts/openapi.yaml), [quickstart.md](./quickstart.md)

**Task Size Rule**: Each task is intended to be a 2-5 minute atomic implementation or verification slice. Each task includes explicit Input and Output.

**Tests**: Required by project constitution and user request. Tests are included before or alongside implementation for each user story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel after dependencies are satisfied
- **[Story]**: Maps to user story from [spec.md](./spec.md)
- Every task includes a concrete file path plus Input and Output

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project skeleton and local configuration surfaces.

- [x] T001 Create Python package directories in `src/skills_agents/__init__.py`; Input: [plan.md](./plan.md) project structure; Output: importable `skills_agents` package skeleton.
- [x] T002 [P] Create test package directories in `tests/unit/test_placeholder.py`; Input: [plan.md](./plan.md) testing structure; Output: `tests/unit`, `tests/integration`, and `tests/contract` directories with one placeholder test file.
- [x] T003 [P] Create sample tenant config in `examples/config/tenants.yaml`; Input: [quickstart.md](./quickstart.md) tenant list; Output: `fashion_store` and `electronics_store` config entries with skill and knowledge paths.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared contracts and filesystem safety before user stories.

**Critical**: No user story implementation starts until this phase is complete.

- [x] T004 Create shared Pydantic schemas in `src/skills_agents/api/schemas.py`; Input: [contracts/openapi.yaml](./contracts/openapi.yaml) schemas; Output: request/response models for sessions, chat, tasks, skills, health, errors.
- [x] T005 [P] Create tenant context model in `src/skills_agents/core/context.py`; Input: [data-model.md](./data-model.md) Tenant/User/Session fields; Output: validated `TenantContext` carrying `tenant_id`, `user_id`, `session_id`.
- [x] T006 [P] Create safe tenant path helper in `src/skills_agents/storage/paths.py`; Input: [data-model.md](./data-model.md) artifact layout; Output: path resolver that confines artifacts under `data/tenants/{tenant_id}`.
- [x] T007 [P] Create atomic JSON/JSONL helpers in `src/skills_agents/storage/atomic.py`; Input: [research.md](./research.md) filesystem decision; Output: atomic JSON write, JSON read with corrupt backup, JSONL append helpers.
- [x] T008 Create provider interface definitions in `src/skills_agents/core/orchestrator.py`; Input: [plan.md](./plan.md) provider list; Output: protocol or abstract base definitions for model, runtime, skills, memory, retrieval, tasks, guardrail, handoff, audit.

---

## Phase 3: User Story 1 - Tenant-Specific Skills Drive Responses (Priority: P1)

**Goal**: Same general agent selects and activates different tenant skills for different merchants.

**Independent Test**: Ask the same return-policy question under both sample tenants and verify tenant-local skill selection and tenant-specific guidance.

### Tests for User Story 1

- [x] T009 [P] [US1] Add skill discovery unit test in `tests/unit/test_skill_registry.py`; Input: sample skill directories; Output: test expects valid skills registered and invalid skills warned.
- [x] T010 [P] [US1] Add skill isolation integration test in `tests/integration/test_tenant_skills.py`; Input: two tenant configs; Output: test expects tenant A cannot list or select tenant B skills.

### Implementation for User Story 1

- [x] T011 [US1] Implement skill parser in `src/skills_agents/skills/parser.py`; Input: `SKILL.md` path; Output: parsed name, description, version, permissions, body summary, warnings.
- [x] T012 [US1] Implement skill registry in `src/skills_agents/skills/registry.py`; Input: tenant skill source paths; Output: tenant-local registry entries with checksum and enabled state.
- [x] T013 [US1] Implement explicit and keyword selectors in `src/skills_agents/skills/selector.py`; Input: tenant registry plus optional skill name and message; Output: selected skill entry or safe no-match result.
- [x] T014 [US1] Implement skill activation service in `src/skills_agents/skills/activation.py`; Input: selected skill entry and tenant context; Output: activation payload with instructions, resource manifest, checksum.
- [x] T015 [US1] Add tenant sample skills in `examples/skills/tenants/fashion_store/fashion-return-policy/SKILL.md`; Input: fashion tenant policy scenario; Output: at least one valid fashion skill package.
- [x] T016 [P] [US1] Add tenant sample skills in `examples/skills/tenants/electronics_store/electronics-return-policy/SKILL.md`; Input: electronics tenant policy scenario; Output: at least one valid electronics skill package.

**Checkpoint**: US1 passes when both tenants expose different enabled skills and the same question activates tenant-local skill guidance only.

---

## Phase 4: User Story 2 - Sessions and Tasks Are Persisted Per Tenant (Priority: P2)

**Goal**: Store session JSON and task Markdown per tenant/session.

**Independent Test**: Create a session, send a message, retrieve task Markdown, and verify artifacts stay under the correct tenant.

### Tests for User Story 2

- [x] T017 [P] [US2] Add session store test in `tests/unit/test_session_store.py`; Input: tenant context and message list; Output: test expects session JSON saved, loaded, and corrupt backup handled.
- [x] T018 [P] [US2] Add task tracker test in `tests/unit/test_task_tracker.py`; Input: tenant session goal and task updates; Output: test expects Markdown with `[ ]`, `[x]`, and `[✗]` statuses.

### Implementation for User Story 2

- [x] T019 [US2] Implement short-term memory store in `src/skills_agents/memory/short_term.py`; Input: tenant context and messages; Output: session JSON load/save/append operations.
- [x] T020 [US2] Implement task tracker in `src/skills_agents/tasks/tracker.py`; Input: tenant context, goal, task item updates; Output: tenant-scoped Markdown checklist.
- [x] T021 [US2] Implement task retrieval route in `src/skills_agents/api/routes.py`; Input: `tenant_id` and `session_id`; Output: response containing Markdown task checklist and summary.

**Checkpoint**: US2 passes when session and task files are created under `data/tenants/{tenant_id}` and cross-tenant reads fail safely.

---

## Phase 5: User Story 3 - High-Risk Requests Enter Human-in-the-loop (Priority: P3)

**Goal**: High-risk requests produce review payloads and never execute irreversible actions.

**Independent Test**: Ask for refund/address/order/account changes and verify Human-in-the-loop outcome, risk tags, and audit events.

### Tests for User Story 3

- [x] T022 [P] [US3] Add guardrail decision test in `tests/unit/test_guardrails.py`; Input: high-risk and safe sample messages; Output: test expects correct risk level and decision.
- [x] T023 [P] [US3] Add handoff payload test in `tests/integration/test_handoff_payload.py`; Input: high-risk chat context; Output: test expects tenant-scoped payload with session summary, tasks, sources, and risk tags.

### Implementation for User Story 3

- [x] T024 [US3] Implement rule-based guardrail provider in `src/skills_agents/safety/guardrails.py`; Input: tenant context and user message; Output: decision with risk level, tags, redactions, and handoff flag.
- [x] T025 [US3] Implement handoff service in `src/skills_agents/handoff/service.py`; Input: tenant context, session state, task summary, sources, guardrail decision; Output: JSON handoff payload path.
- [x] T026 [US3] Implement audit sink in `src/skills_agents/audit/jsonl.py`; Input: audit event dict; Output: tenant-scoped append-only `events.jsonl` entry.

**Checkpoint**: US3 passes when high-risk requests create handoff payloads and audit events without executing business actions.

---

## Phase 6: User Story 4 - MVP Is Demonstrable Without External Credentials (Priority: P4)

**Goal**: Full demo flow runs deterministically without external model credentials.

**Independent Test**: Execute quickstart flow with mock provider and verify sessions, skills, tasks, retrieval, audit, and handoff outputs.

### Tests for User Story 4

- [x] T027 [P] [US4] Add end-to-end mock flow test in `tests/integration/test_mock_quickstart_flow.py`; Input: sample tenant config and mock provider; Output: test expects quickstart primary flow artifacts.

### Implementation for User Story 4

- [x] T028 [US4] Implement mock model provider in `src/skills_agents/models/mock_provider.py`; Input: activated skills, sources, guardrail decision, task summary; Output: deterministic assistant reply.
- [x] T029 [US4] Implement local document retriever in `src/skills_agents/retrieval/local_documents.py`; Input: tenant knowledge paths and user query; Output: tenant-local source references and snippets.
- [x] T030 [US4] Implement FastAPI app and chat orchestration in `src/skills_agents/api/app.py`; Input: session/chat/skills/tasks requests; Output: REST app wiring routes, orchestrator, mock provider, storage, audit, guardrail, handoff.

**Checkpoint**: US4 passes when the quickstart can be executed locally without model credentials and produces deterministic results.

---

## Phase 7: Post-review Hardening & Spec Alignment

**Goal**: Resolve Spec Kit analysis findings C1-C4 and keep implementation traceable to formal tasks.

**Independent Test**: Run security, handoff, script-permission, long-term memory, and quickstart tests; verify no tenant isolation or audit regressions.

### Tests for Post-review Hardening

- [x] T031 [P] Add script permission deny-by-default tests in `tests/unit/test_script_permissions.py`; Input: tenant context, script path, and audit sink; Output: tests expect default denial, path-bound script decisions, and script authorization audit events.
- [x] T034 [P] Add malicious skill instruction boundary test in `tests/integration/test_skill_instruction_boundaries.py`; Input: tenant skill that attempts to override guardrails; Output: test expects guardrail-first Human-in-the-loop behavior.
- [x] T036 [P] Add handoff trigger coverage tests in `tests/integration/test_handoff_triggers.py`; Input: user escalation, no-confidence/no-source request, and failed-tool metadata; Output: tests expect human-review payload generation for each trigger.

### Implementation for Post-review Hardening

- [x] T032 Implement deny-first permission policy in `src/skills_agents/scripts/permissions.py`; Input: tenant context and script path; Output: structured authorization decision defaulting to denied.
- [x] T033 Implement deny-only script executor audit path in `src/skills_agents/scripts/executor.py`; Input: script execution request and audit sink; Output: denied execution result and `script_authorization_decision` audit event.
- [x] T035 Enforce guardrail-first orchestration over skill instructions in `src/skills_agents/api/app.py`; Input: activated skill instructions and high-risk message; Output: guardrail decision takes precedence over skill content.
- [x] T037 Implement user-requested escalation handoff in `src/skills_agents/safety/guardrails.py`; Input: customer asks for a human agent; Output: handoff-required decision and payload trigger.
- [x] T038 Implement low-confidence and failed-tool handoff paths in `src/skills_agents/api/app.py`; Input: no selected skill/no sources or failed-tool metadata; Output: human-review payload and audit event.
- [x] T039 Add long-term memory provider tests in `tests/unit/test_long_term_memory.py`; Input: tenant-user context and memory content; Output: tests expect tenant-user memory add/search isolation.
- [x] T040 Implement tenant-user JSON long-term memory provider in `src/skills_agents/memory/long_term.py`; Input: tenant-user context and content; Output: tenant-scoped memory JSON records.
- [x] T041 Wire memory access audit into chat flow in `src/skills_agents/api/app.py`; Input: chat turn context; Output: `memory_access` audit event and tenant-user memory artifact.

**Checkpoint**: Post-review hardening passes when script decisions are audited, malicious skill instructions cannot override guardrails, additional handoff triggers create payloads, and all C1-C4 work is traceable.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1; blocks all user stories.
- **US1 (Phase 3)**: Depends on Phase 2; enables skill discovery, registry, selection, and activation.
- **US2 (Phase 4)**: Depends on Phase 2; can begin in parallel with US1 except route wiring depends on shared schemas.
- **US3 (Phase 5)**: Depends on Phase 2; handoff test is stronger after US2 task/session stores exist.
- **US4 (Phase 6)**: Depends on US1-US3 because it wires the complete quickstart flow.
- **Post-review Hardening (Phase 7)**: Depends on US1-US4 and Spec Kit analysis findings C1-C4.

### User Story Dependencies

- **US1**: Independently verifies tenant-specific skills.
- **US2**: Independently verifies tenant-scoped session and task persistence.
- **US3**: Independently verifies Human-in-the-loop safety.
- **US4**: Integrates US1, US2, and US3 into one deterministic demo flow.

### Parallel Opportunities

- T002 and T003 can run after T001 starts.
- T005, T006, and T007 can run in parallel after T004 shape is known.
- T009 and T010 can be written before T011-T014.
- T015 and T016 can run in parallel.
- T017 and T018 can run in parallel.
- T022 and T023 can run in parallel.
- T028 and T029 can run in parallel before T030.
- T031, T034, and T036 can run in parallel after Phase 6.

---

## Parallel Example: User Story 1

```bash
Task: "T009 Add skill discovery unit test in tests/unit/test_skill_registry.py"
Task: "T010 Add skill isolation integration test in tests/integration/test_tenant_skills.py"
Task: "T015 Add tenant sample skills in examples/skills/tenants/fashion_store/fashion-return-policy/SKILL.md"
Task: "T016 Add tenant sample skills in examples/skills/tenants/electronics_store/electronics-return-policy/SKILL.md"
```

## Parallel Example: User Story 2

```bash
Task: "T017 Add session store test in tests/unit/test_session_store.py"
Task: "T018 Add task tracker test in tests/unit/test_task_tracker.py"
```

## Parallel Example: User Story 3

```bash
Task: "T022 Add guardrail decision test in tests/unit/test_guardrails.py"
Task: "T023 Add handoff payload test in tests/integration/test_handoff_payload.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to prove the core platform promise: tenant-specific skills.
3. Stop and validate US1 independently before expanding the flow.

### Incremental Delivery

1. Add US2 to persist sessions and tasks.
2. Add US3 to enforce Human-in-the-loop safety.
3. Add US4 to wire the full deterministic quickstart flow.

### Validation Gates

- Each user story checkpoint must pass before moving to the next story.
- No high-risk business action may be implemented as an executable action.
- Mock-provider path must remain valid without external credentials.
- Tenant isolation failures block completion.
