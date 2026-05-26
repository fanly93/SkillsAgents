from __future__ import annotations

from pathlib import Path
from typing import Any

from skills_agents.audit.jsonl import JsonlAuditSink
from skills_agents.core.context import TenantContext
from skills_agents.scripts.permissions import PermissionPolicy


class ScriptExecutor:
    def __init__(
        self,
        *,
        permission_policy: PermissionPolicy,
        audit_sink: JsonlAuditSink | None = None,
    ):
        self.permission_policy = permission_policy
        self.audit_sink = audit_sink

    def execute(
        self,
        context: TenantContext,
        *,
        skill_root: str | Path,
        script_path: str | Path,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        decision = self.permission_policy.authorize(
            context,
            skill_root=skill_root,
            script_path=script_path,
            input_data=input_data,
        )
        if self.audit_sink is not None:
            self.audit_sink.write(
                context,
                {
                    "event_type": "script_authorization_decision",
                    "decision": decision,
                },
            )
        return {
            "status": "denied",
            "authorization_decision": decision,
            "output_summary": "Script execution denied by policy.",
        }
