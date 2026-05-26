from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from skills_agents.core.context import TenantContext
from skills_agents.storage.paths import TenantPathResolver


class TaskTracker:
    def __init__(self, paths: TenantPathResolver):
        self._paths = paths

    def path_for(self, context: TenantContext) -> Path:
        if not context.session_id:
            raise ValueError("session_id is required")
        return self._paths.task_path(context.tenant_id, context.session_id)

    def create_plan(self, context: TenantContext, goal: str, tasks: list[dict[str, str]]) -> None:
        now = _now()
        lines = [
            f"# Task Plan: {context.session_id}",
            "",
            f"**Tenant**: {context.tenant_id}",
            f"**User**: {context.user_id}",
            f"**Goal**: {goal}",
            f"**Created**: {now}",
            f"**Updated**: {now}",
            "",
            "## Tasks",
            "",
        ]
        for task in tasks:
            lines.append(f"- [ ] {task['task_id']} {task['description']}")
        lines.extend(["", "## Notes", ""])
        self._write(context, "\n".join(lines))

    def mark_done(self, context: TenantContext, task_id: str, note: str | None = None) -> None:
        self._replace_task_status(context, task_id, "x", note=note)

    def mark_failed(self, context: TenantContext, task_id: str, reason: str) -> None:
        self._replace_task_status(context, task_id, "✗", reason=reason)

    def get_markdown(self, context: TenantContext) -> str:
        path = self.path_for(context)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def summary(self, context: TenantContext) -> dict[str, int]:
        markdown = self.get_markdown(context)
        total = completed = failed = pending = 0
        for line in markdown.splitlines():
            if line.startswith("- ["):
                total += 1
                if line.startswith("- [x]"):
                    completed += 1
                elif line.startswith("- [✗]"):
                    failed += 1
                else:
                    pending += 1
        return {"total": total, "completed": completed, "failed": failed, "pending": pending}

    def _replace_task_status(
        self,
        context: TenantContext,
        task_id: str,
        marker: str,
        note: str | None = None,
        reason: str | None = None,
    ) -> None:
        lines = self.get_markdown(context).splitlines()
        output: list[str] = []
        skip_detail = False
        for line in lines:
            if skip_detail:
                if line.startswith("  - Note:") or line.startswith("  - Reason:"):
                    continue
                skip_detail = False
            if line.startswith("- [") and f" {task_id} " in line:
                description = line.split("] ", 1)[1]
                output.append(f"- [{marker}] {description}")
                if note:
                    output.append(f"  - Note: {note}")
                if reason:
                    output.append(f"  - Reason: {reason}")
                skip_detail = True
            else:
                output.append(line)
        self._write(context, "\n".join(output))

    def _write(self, context: TenantContext, markdown: str) -> None:
        path = self.path_for(context)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
