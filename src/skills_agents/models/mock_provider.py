from __future__ import annotations

from typing import Any


class MockModelProvider:
    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = config or {}
        return {"role": "assistant", "content": self.reply(context)}

    def reply(self, context: dict[str, Any]) -> str:
        guardrail = context.get("guardrail_decision", {})
        if guardrail.get("handoff_required"):
            return "This request needs human review before any business action is taken."

        skills = context.get("activated_skills", [])
        sources = context.get("sources", [])
        skill_name = skills[0]["name"] if skills else "general-support"
        if sources:
            source = sources[0]
            return f"Using {skill_name}: {source['snippet']}"
        return f"Using {skill_name}: I can help with this request using the configured tenant skills."
