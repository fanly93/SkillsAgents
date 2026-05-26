from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skills_agents.audit.jsonl import JsonlAuditSink
from skills_agents.core.context import TenantContext
from skills_agents.storage.atomic import write_json
from skills_agents.storage.paths import TenantPathResolver


class HandoffService:
    def __init__(self, paths: TenantPathResolver, audit_sink: JsonlAuditSink | None = None):
        self.paths = paths
        self.audit_sink = audit_sink

    def path_for(self, context: TenantContext) -> Path:
        if context.session_id is None:
            raise ValueError("session_id is required for handoff payloads")
        return self.paths.handoff_path(context.tenant_id, context.session_id)

    def create_payload(
        self,
        *,
        context: TenantContext,
        session_state: dict[str, Any],
        task_summary: dict[str, Any],
        sources: list[dict[str, Any]],
        guardrail_decision: dict[str, Any],
    ) -> Path:
        payload = {
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "created_at": _now(),
            "reason": guardrail_decision.get("reason", "Human review required."),
            "risk_tags": list(guardrail_decision.get("risk_tags", [])),
            "session_summary": session_state.get("summary", ""),
            "messages_or_summary": session_state.get("messages", []),
            "activated_skills": session_state.get("active_skills", []),
            "task_status": task_summary,
            "sources": sources,
            "agent_attempted_steps": list(session_state.get("agent_attempted_steps", [])),
            "recommended_next_steps": _recommended_next_steps(guardrail_decision),
            "status": "review_pending",
        }
        path = self.path_for(context)
        write_json(path, payload)

        if self.audit_sink is not None:
            self.audit_sink.write(
                context,
                {
                    "event_type": "handoff_payload_created",
                    "payload_path": str(path),
                    "risk_tags": payload["risk_tags"],
                    "status": payload["status"],
                },
            )

        return path


def _recommended_next_steps(guardrail_decision: dict[str, Any]) -> list[str]:
    steps = guardrail_decision.get("recommended_next_steps") or []
    if steps:
        return list(steps)
    return ["Review the conversation context.", "Decide the next customer-service action manually."]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
