from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4
from dataclasses import asdict

import yaml
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from skills_agents.api.routes import create_task_router
from skills_agents.api.schemas import (
    ActivatedSkill,
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    ErrorResponse,
    HealthResponse,
    ReloadSkillsRequest,
    SessionResponse,
    SkillEntry,
    SkillListResponse,
    SkillReloadResponse,
    SourceReference,
    TaskSummary,
)
from skills_agents.audit.jsonl import JsonlAuditSink
from skills_agents.core.context import TenantContext
from skills_agents.handoff.service import HandoffService
from skills_agents.memory.long_term import JsonLongTermMemoryProvider
from skills_agents.memory.short_term import ShortTermMemoryStore
from skills_agents.models.mock_provider import MockModelProvider
from skills_agents.retrieval.local_documents import LocalDocumentRetriever
from skills_agents.safety.guardrails import RuleBasedGuardrailProvider
from skills_agents.skills.activation import SkillActivationService
from skills_agents.skills.registry import SkillRegistry
from skills_agents.skills.selector import ExplicitSelector, KeywordSelector
from skills_agents.storage.paths import TenantPathResolver
from skills_agents.tasks.tracker import TaskTracker


def create_app(
    *,
    tenant_config_path: str | Path = "examples/config/tenants.yaml",
    data_root: str | Path = "data",
) -> FastAPI:
    config_path = Path(tenant_config_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    tenants: dict[str, dict[str, Any]] = config.get("tenants", {})

    paths = TenantPathResolver(data_root)
    config_base = config_path.parent
    registry = SkillRegistry()
    activation_service = SkillActivationService(registry)
    keyword_selector = KeywordSelector(registry)
    explicit_selector = ExplicitSelector(registry)
    memory_store = ShortTermMemoryStore(paths)
    long_term_memory = JsonLongTermMemoryProvider(paths)
    task_tracker = TaskTracker(paths)
    audit_sink = JsonlAuditSink(paths)
    guardrails = RuleBasedGuardrailProvider()
    handoff = HandoffService(paths, audit_sink=audit_sink)
    tenant_skill_sources = {
        tenant_id: _tenant_scoped_paths(
            config_base=config_base,
            tenant_id=tenant_id,
            paths=tenant.get("skill_sources", []),
            kind="skills",
        )
        for tenant_id, tenant in tenants.items()
    }
    tenant_knowledge_paths = {
        tenant_id: _tenant_scoped_paths(
            config_base=config_base,
            tenant_id=tenant_id,
            paths=tenant.get("knowledge_paths", []),
            kind="knowledge",
        )
        for tenant_id, tenant in tenants.items()
    }
    retriever = LocalDocumentRetriever(tenant_knowledge_paths)
    model = MockModelProvider()

    app = FastAPI(title="SkillsAgents MVP API", version="0.1.0")
    app.include_router(create_task_router(task_tracker, tenant_ids=set(tenants)))

    for tenant_id, tenant in tenants.items():
        registry.refresh(tenant_id, tenant_skill_sources[tenant_id])

    @app.get("/v1/health", response_model=HealthResponse)
    def health():
        return HealthResponse(
            status="ok",
            providers={
                "model": "mock",
                "retrieval": "local_documents",
                "storage": str(Path(data_root)),
            },
        )

    @app.post("/v1/skills/reload", response_model=SkillReloadResponse)
    def reload_skills(request: ReloadSkillsRequest):
        tenant = tenants.get(request.tenant_id)
        if tenant is None:
            return _unknown_tenant(request.tenant_id)
        result = registry.refresh(request.tenant_id, tenant_skill_sources[request.tenant_id])
        return SkillReloadResponse(
            tenant_id=request.tenant_id,
            scanned=result.scanned,
            registered=result.registered,
            warnings=result.warnings,
        )

    @app.get("/v1/skills", response_model=SkillListResponse)
    def list_skills(tenant_id: str):
        if tenant_id not in tenants:
            return _unknown_tenant(tenant_id)
        return SkillListResponse(
            tenant_id=tenant_id,
            skills=[
                SkillEntry(
                    skill_id=skill.skill_id,
                    name=skill.name,
                    description=skill.description,
                    source=skill.source,
                    enabled=skill.enabled,
                    version=skill.version,
                    checksum=skill.checksum,
                    warnings=skill.warnings,
                )
                for skill in registry.list(tenant_id)
            ],
        )

    @app.post("/v1/sessions", status_code=201, response_model=SessionResponse)
    def create_session(request: CreateSessionRequest):
        if request.tenant_id not in tenants:
            return _unknown_tenant(request.tenant_id)
        context = TenantContext(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            session_id=f"sess_{uuid4().hex[:12]}",
        )
        memory_store.save(
            context,
            {
                "summary": "",
                "messages": [],
                "active_skills": [],
                "recent_sources": [],
                "risk_tags": [],
                "handoff": {"required": False},
            },
        )
        task_tracker.create_plan(
            context,
            goal="Answer customer question",
            tasks=[
                {"task_id": "T001", "description": "Classify request risk"},
                {"task_id": "T002", "description": "Select tenant skill"},
                {"task_id": "T003", "description": "Retrieve tenant knowledge"},
                {"task_id": "T004", "description": "Prepare customer response or handoff"},
            ],
        )
        audit_sink.write(context, {"event_type": "session_created"})
        audit_sink.write(context, {"event_type": "task_updated", "action": "create_plan"})
        return SessionResponse(
            tenant_id=context.tenant_id,
            user_id=context.user_id or "",
            session_id=context.session_id or "",
            status="active",
        )

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        if request.tenant_id not in tenants:
            return _unknown_tenant(request.tenant_id)

        context = TenantContext(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            session_id=request.session_id,
        )
        session_state = memory_store.load(context)
        if not paths.session_path(request.tenant_id, request.session_id).exists():
            return _error(404, "session_not_found", "No session exists for this tenant and session_id.")
        if session_state.get("user_id") != request.user_id:
            return _error(403, "session_user_mismatch", "Session does not belong to this user.")

        guardrail_decision = guardrails.evaluate(context, request.message)
        audit_sink.write(context, {"event_type": "guardrail_decision", "decision": guardrail_decision})

        try:
            selected = _select_skill(
                tenant_id=request.tenant_id,
                message=request.message,
                skill_id=request.skill_id,
                skill_name=request.skill_name,
                explicit_selector=explicit_selector,
                keyword_selector=keyword_selector,
            )
        except ValueError as exc:
            return _error(400, "skill_not_enabled", str(exc))

        activated_skills = [_activated_skill(selected)] if selected is not None else []
        skill_activations = [asdict(activation_service.activate(request.tenant_id, selected.skill_id))] if selected is not None else []
        if selected is not None:
            audit_sink.write(
                context,
                {
                    "event_type": "skill_activation",
                    "skill_id": selected.skill_id,
                    "skill_name": selected.name,
                    "selection_reason": selected.selection_reason,
                    "resource_manifest": skill_activations[0]["resource_manifest"],
                },
            )

        memory_results = long_term_memory.search(context, request.message)
        long_term_memory.add(
            context,
            request.message,
            {"session_id": request.session_id, "role": "user"},
        )
        audit_sink.write(
            context,
            {
                "event_type": "memory_access",
                "operation": "search_add",
                "result_count": len(memory_results),
            },
        )

        sources = retriever.retrieve(request.tenant_id, request.message)
        audit_sink.write(context, {"event_type": "retrieval", "source_count": len(sources)})

        guardrail_decision = _apply_chat_handoff_triggers(
            guardrail_decision,
            selected=selected,
            sources=sources,
            metadata=request.metadata,
        )

        task_tracker.mark_done(context, "T001", note="Guardrail evaluated")
        if selected is not None:
            task_tracker.mark_done(context, "T002", note=f"Selected {selected.name}")
        if sources:
            task_tracker.mark_done(context, "T003", note=f"Retrieved {len(sources)} source(s)")
        audit_sink.write(context, {"event_type": "task_updated", "action": "chat_progress"})

        reply = model.reply(
            {
                "activated_skills": [skill.model_dump() for skill in activated_skills],
                "skill_activations": skill_activations,
                "sources": sources,
                "guardrail_decision": guardrail_decision,
                "task_summary": task_tracker.summary(context),
            }
        )
        memory_store.append_message(context, {"role": "user", "content": request.message})
        memory_store.append_message(context, {"role": "assistant", "content": reply})

        session_state = memory_store.load(context)
        session_state["summary"] = _summary(session_state)
        session_state["active_skills"] = _merge_by_key(
            session_state.get("active_skills", []),
            skill_activations,
            "skill_id",
        )
        session_state["recent_sources"] = _merge_by_key(
            session_state.get("recent_sources", []),
            sources,
            "source_id",
        )
        session_state["risk_tags"] = _merge_scalars(
            session_state.get("risk_tags", []),
            guardrail_decision["risk_tags"],
        )
        session_state["handoff"] = {"required": guardrail_decision["handoff_required"]}

        handoff_path: Path | None = None
        if guardrail_decision["handoff_required"]:
            task_tracker.mark_failed(context, "T004", reason=guardrail_decision["reason"])
            session_state["handoff"] = {"required": True, "status": "review_pending"}
            handoff_path = handoff.create_payload(
                context=context,
                session_state=session_state,
                task_summary=task_tracker.summary(context),
                sources=sources,
                guardrail_decision=guardrail_decision,
            )
        else:
            task_tracker.mark_done(context, "T004", note="Response prepared")
        memory_store.save(context, session_state)

        audit_sink.write(
            context,
            {
                "event_type": "chat_turn",
                "risk_level": guardrail_decision["risk_level"],
                "handoff_required": guardrail_decision["handoff_required"],
            },
        )

        return ChatResponse(
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            reply=reply,
            activated_skills=activated_skills,
            task_summary=TaskSummary(**task_tracker.summary(context)),
            sources=[SourceReference(**source) for source in sources],
            risk_level=guardrail_decision["risk_level"],
            risk_tags=guardrail_decision["risk_tags"],
            handoff_required=guardrail_decision["handoff_required"],
            requires_human_approval=guardrail_decision["requires_human_approval"],
            handoff_payload_path=str(handoff_path) if handoff_path else None,
        )

    return app


def _select_skill(
    *,
    tenant_id: str,
    message: str,
    skill_id: str | None,
    skill_name: str | None,
    explicit_selector: ExplicitSelector,
    keyword_selector: KeywordSelector,
):
    selected = explicit_selector.select_by_id(tenant_id, skill_id)
    if selected is not None:
        return selected
    selected = explicit_selector.select(tenant_id, message, skill_name)
    if selected is not None:
        return selected
    return keyword_selector.select(tenant_id, message)


def _merge_by_key(existing: list[dict[str, Any]], updates: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in [*existing, *updates]:
        value = item.get(key)
        if value:
            merged[value] = item
    return list(merged.values())


def _merge_scalars(existing: list[str], updates: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*existing, *updates]:
        if item not in merged:
            merged.append(item)
    return merged


def _apply_chat_handoff_triggers(
    decision: dict[str, Any],
    *,
    selected,
    sources: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    updated = {**decision, "risk_tags": list(decision.get("risk_tags", []))}
    if metadata.get("tool_failed"):
        _require_handoff(updated, "failed_tool", "A tool failed and the conversation needs human review.")
    elif selected is None and not sources and not updated.get("handoff_required"):
        _require_handoff(updated, "low_confidence", "No tenant skill or local source matched the request.")
    return updated


def _require_handoff(decision: dict[str, Any], tag: str, reason: str) -> None:
    if tag not in decision["risk_tags"]:
        decision["risk_tags"].append(tag)
    decision["risk_level"] = "medium" if decision.get("risk_level") == "low" else decision["risk_level"]
    decision["decision"] = "handoff_required"
    decision["reason"] = reason
    decision["handoff_required"] = True
    decision["requires_human_approval"] = True
    steps = decision.setdefault("recommended_next_steps", [])
    if not steps:
        steps.append("Escalate the conversation to a human operator.")


def _tenant_scoped_paths(
    *,
    config_base: Path,
    tenant_id: str,
    paths: list[str],
    kind: str,
) -> list[Path]:
    allowed: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_absolute():
            candidate = path
            if not candidate.exists():
                candidate = config_base / path
            path = candidate
        resolved = path.resolve()
        parts = resolved.parts
        if kind == "skills" and _is_tenant_skill_path(parts, tenant_id):
            allowed.append(resolved)
        elif kind == "skills" and "common" in parts:
            allowed.append(resolved)
        elif kind == "knowledge" and _is_tenant_data_path(parts, tenant_id):
            allowed.append(resolved)
    return allowed


def _is_tenant_skill_path(parts: tuple[str, ...], tenant_id: str) -> bool:
    return _contains_sequence(parts, ("skills", "tenants", tenant_id))


def _is_tenant_data_path(parts: tuple[str, ...], tenant_id: str) -> bool:
    return _contains_sequence(parts, ("data", "tenants", tenant_id))


def _contains_sequence(parts: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    width = len(sequence)
    return any(parts[index : index + width] == sequence for index in range(len(parts) - width + 1))


def _activated_skill(selected) -> ActivatedSkill:
    return ActivatedSkill(
        skill_id=selected.skill_id,
        name=selected.name,
        version=selected.version,
        checksum=selected.checksum,
        selection_reason=selected.selection_reason,
    )


def _summary(session_state: dict[str, Any]) -> str:
    messages = session_state.get("messages", [])
    if not messages:
        return ""
    return f"{len(messages)} message(s) exchanged in this session."


def _unknown_tenant(tenant_id: str) -> JSONResponse:
    return _error(404, "unknown_tenant", f"Unknown tenant: {tenant_id}")


def _error(status_code: int, error: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=error, message=message).model_dump(),
    )
