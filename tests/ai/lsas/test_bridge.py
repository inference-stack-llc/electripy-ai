"""Tests for the optional policy_gateway ↔ LSAS bridge."""

from __future__ import annotations

from electripy.ai.lsas.domain import Decision, LsasResult
from electripy.ai.lsas.policy_packs import DEMO_PACK, HIPAA_PACK
from electripy.ai.policy_gateway.domain import PolicyContext
from electripy.ai.policy_gateway.lsas_bridge import run_lsas_for_policy_input


def test_bridge_clean_text_returns_allow() -> None:
    result = run_lsas_for_policy_input("Hello, this is safe text.", pack=DEMO_PACK)
    assert isinstance(result, LsasResult)
    assert result.decision == Decision.ALLOW


def test_bridge_email_triggers_finding() -> None:
    result = run_lsas_for_policy_input(
        "Contact alice@example.com for details.",
        pack=DEMO_PACK,
    )
    assert result.decision != Decision.ALLOW
    assert len(result.findings) > 0


def test_bridge_context_populates_audit() -> None:
    context = PolicyContext(
        request_id="req-123",
        actor_id="user-456",
        tenant_id="tenant-789",
    )
    result = run_lsas_for_policy_input(
        "Safe text",
        pack=DEMO_PACK,
        context=context,
    )
    assert result.audit is not None
    assert result.audit.request_id == "req-123"
    assert result.audit.actor_id == "user-456"
    assert result.audit.tenant_id == "tenant-789"


def test_bridge_uses_hipaa_pack() -> None:
    result = run_lsas_for_policy_input(
        "Patient SSN: 123-45-6789",
        pack=HIPAA_PACK,
    )
    assert result.provenance.pack_id == "hipaa"
    assert result.decision in (Decision.BLOCKED, Decision.ESCALATE_HITL)


def test_bridge_default_pack_is_demo() -> None:
    result = run_lsas_for_policy_input("Safe text")
    assert result.provenance.pack_id == "demo"


def test_bridge_custom_validators() -> None:
    from electripy.ai.lsas.validators.phi_pii import PhiPiiValidator

    result = run_lsas_for_policy_input(
        "email: bob@clinic.com",
        validators=[PhiPiiValidator()],
    )
    assert any(f.code == "PHI_EMAIL" for f in result.findings)


def test_bridge_does_not_modify_policy_gateway() -> None:
    """The bridge must not change PolicyGateway behavior."""
    from electripy.ai.policy_gateway import (
        PolicyAction,
        PolicyGateway,
        PolicyRule,
        PolicySeverity,
        PolicyStage,
    )

    gateway = PolicyGateway(
        rules=[
            PolicyRule(
                rule_id="email",
                code="PII_EMAIL",
                description="email",
                stage=PolicyStage.PREFLIGHT,
                pattern=r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
                action=PolicyAction.SANITIZE,
                severity=PolicySeverity.MEDIUM,
            )
        ]
    )

    decision = gateway.evaluate_preflight("hi alice@example.com bye")
    assert decision.action == PolicyAction.SANITIZE

    # Bridge can also score the same text independently
    lsas_result = run_lsas_for_policy_input("hi alice@example.com bye", pack=DEMO_PACK)
    assert lsas_result.decision != Decision.ALLOW
    # Gateway decision unchanged
    assert decision.action == PolicyAction.SANITIZE
