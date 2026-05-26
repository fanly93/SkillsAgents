from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from skills_agents.core.context import TenantContext


RiskLevel = Literal["low", "medium", "high", "blocked"]
Decision = Literal["allow", "block", "handoff_required", "requires_approval"]


@dataclass(frozen=True)
class GuardrailRule:
    tag: str
    pattern: re.Pattern[str]
    risk_level: RiskLevel
    decision: Decision
    reason: str


class RuleBasedGuardrailProvider:
    def __init__(self, rules: list[GuardrailRule] | None = None):
        self.rules = rules or _default_rules()

    def evaluate(self, context: TenantContext, message: str) -> dict[str, Any]:
        matches = [rule for rule in self.rules if rule.pattern.search(message)]
        risk_tags = _ordered_unique([rule.tag for rule in matches])
        redacted_message, redaction_tags = _redact_pii(message)
        risk_tags = _ordered_unique([*risk_tags, *redaction_tags])

        blocking = [rule for rule in matches if rule.decision == "block"]
        high_risk = [rule for rule in matches if rule.risk_level == "high"]

        if blocking:
            risk_level: RiskLevel = "blocked"
            decision: Decision = "block"
            handoff_required = True
            reason = blocking[0].reason
        elif high_risk:
            risk_level = "high"
            decision = "handoff_required"
            handoff_required = True
            reason = "High-risk business action requires human review."
        elif any(rule.decision == "handoff_required" for rule in matches):
            risk_level = "medium"
            decision = "handoff_required"
            handoff_required = True
            reason = matches[0].reason
        else:
            risk_level = "low"
            decision = "allow"
            handoff_required = False
            reason = "No configured high-risk action detected."

        return {
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "risk_level": risk_level,
            "risk_tags": risk_tags,
            "decision": decision,
            "reason": reason,
            "redactions": {"message": redacted_message} if redacted_message != message else {},
            "handoff_required": handoff_required,
            "requires_human_approval": handoff_required,
            "recommended_next_steps": _recommended_next_steps(risk_tags, decision),
        }


def _default_rules() -> list[GuardrailRule]:
    return [
        GuardrailRule(
            tag="cross_tenant_access",
            pattern=re.compile(r"\b(other tenant|another tenant|cross[- ]tenant|tenant data)\b|其他商户|跨租户", re.I),
            risk_level="blocked",
            decision="block",
            reason="Cross-tenant access attempts are blocked and require human review.",
        ),
        GuardrailRule(
            tag="refund",
            pattern=re.compile(r"\b(refund|chargeback|return my money)\b|退款|退钱|原路退回", re.I),
            risk_level="high",
            decision="handoff_required",
            reason="Refund requests require human review.",
        ),
        GuardrailRule(
            tag="address_change",
            pattern=re.compile(r"\b(change|modify|update)\b.{0,40}\b(address|delivery|shipping)\b|改地址|修改地址|变更地址", re.I),
            risk_level="high",
            decision="handoff_required",
            reason="Address changes require human review.",
        ),
        GuardrailRule(
            tag="order_change",
            pattern=re.compile(r"\b(change|modify|cancel|update)\b.{0,40}\border\b|改订单|修改订单|取消订单", re.I),
            risk_level="high",
            decision="handoff_required",
            reason="Order changes require human review.",
        ),
        GuardrailRule(
            tag="account_permission_change",
            pattern=re.compile(r"\b(change|grant|remove|reset)\b.{0,40}\b(permission|role|admin|account)\b|权限|管理员|账号权限", re.I),
            risk_level="high",
            decision="handoff_required",
            reason="Account permission changes require human review.",
        ),
        GuardrailRule(
            tag="prompt_injection",
            pattern=re.compile(r"\b(ignore previous|system prompt|developer message|jailbreak)\b|忽略之前|系统提示词", re.I),
            risk_level="blocked",
            decision="block",
            reason="Prompt-injection indicators are blocked and require human review.",
        ),
        GuardrailRule(
            tag="user_escalation",
            pattern=re.compile(r"\b(human agent|real person|support agent|transfer me|escalate)\b|转人工|人工客服|真人客服", re.I),
            risk_level="medium",
            decision="handoff_required",
            reason="User requested human support.",
        ),
    ]


def _redact_pii(message: str) -> tuple[str, list[str]]:
    tags: list[str] = []
    redacted = re.sub(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]", message)
    if redacted != message:
        tags.append("pii_phone")
    redacted_email = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[REDACTED_EMAIL]", redacted)
    if redacted_email != redacted:
        tags.append("pii_email")
    return redacted_email, tags


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _recommended_next_steps(risk_tags: list[str], decision: Decision) -> list[str]:
    if decision == "allow":
        return []
    if "cross_tenant_access" in risk_tags or "prompt_injection" in risk_tags:
        return ["Do not disclose protected data.", "Escalate the conversation to a human operator."]
    return ["Review the customer request.", "Verify order and account context before taking any business action."]
