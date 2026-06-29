"""Tests for LSAS domain enumerations and frozen dataclasses."""

from __future__ import annotations

from datetime import datetime

import pytest

from electripy.ai.lsas.domain import (
    Decision,
    DecisionEvent,
    Finding,
    LsasAuditMetadata,
    LsasProvenance,
    LsasResult,
    RemediationApplied,
    RiskDomain,
    RiskDomainScore,
    RiskSummary,
    RiskTier,
    Severity,
)

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


def test_decision_values() -> None:
    assert set(Decision) == {
        Decision.ALLOW,
        Decision.ALLOW_WITH_WARNINGS,
        Decision.REDACTED,
        Decision.BLOCKED,
        Decision.ESCALATE_HITL,
    }


def test_decision_str_values() -> None:
    assert Decision.ALLOW == "ALLOW"
    assert Decision.ESCALATE_HITL == "ESCALATE_HITL"


def test_risk_domain_values() -> None:
    assert RiskDomain.HIPAA_PHI == "HIPAA_PHI"
    assert RiskDomain.PCI == "PCI"
    assert RiskDomain.SECURITY == "SECURITY"
    assert len(set(RiskDomain)) == 6


def test_severity_values() -> None:
    assert Severity.LOW == "LOW"
    assert Severity.CRITICAL == "CRITICAL"
    assert len(set(Severity)) == 4


def test_risk_tier_values() -> None:
    assert RiskTier.SAFE == "SAFE"
    assert RiskTier.CRITICAL == "CRITICAL"
    assert len(set(RiskTier)) == 5


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


def test_finding_is_frozen() -> None:
    finding = Finding(
        validator_id="test",
        code="TEST_CODE",
        message="Test message",
        severity=Severity.HIGH,
        domain=RiskDomain.SECURITY,
    )
    with pytest.raises((AttributeError, TypeError)):
        finding.code = "CHANGED"  # type: ignore[misc]


def test_finding_optional_fields() -> None:
    finding = Finding(
        validator_id="v",
        code="C",
        message="m",
        severity=Severity.LOW,
        domain=RiskDomain.OTHER,
    )
    assert finding.start is None
    assert finding.end is None
    assert finding.matched_text is None


def test_finding_with_offsets() -> None:
    finding = Finding(
        validator_id="v",
        code="C",
        message="m",
        severity=Severity.HIGH,
        domain=RiskDomain.HIPAA_PHI,
        start=5,
        end=20,
        matched_text="alice@example.com",
    )
    assert finding.start == 5
    assert finding.end == 20
    assert finding.matched_text == "alice@example.com"


# ---------------------------------------------------------------------------
# RiskDomainScore / RiskSummary
# ---------------------------------------------------------------------------


def test_risk_domain_score_frozen() -> None:
    rds = RiskDomainScore(domain=RiskDomain.PCI, score=42.0, finding_count=3)
    with pytest.raises((AttributeError, TypeError)):
        rds.score = 0.0  # type: ignore[misc]


def test_risk_summary_immutable() -> None:
    rds = RiskDomainScore(domain=RiskDomain.SECURITY, score=7.0, finding_count=1)
    summary = RiskSummary(
        overall_score=7.0,
        domain_scores=(rds,),
        tier=RiskTier.LOW,
        finding_count=1,
    )
    assert summary.overall_score == 7.0
    assert summary.tier == RiskTier.LOW


# ---------------------------------------------------------------------------
# RemediationApplied
# ---------------------------------------------------------------------------


def test_remediation_applied_frozen() -> None:
    rem = RemediationApplied(
        remediation_type="BLOCK",
        description="Blocked",
        domain=RiskDomain.PCI,
    )
    with pytest.raises((AttributeError, TypeError)):
        rem.remediation_type = "WARN"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# LsasProvenance / LsasAuditMetadata / LsasResult
# ---------------------------------------------------------------------------


def test_provenance_defaults() -> None:
    prov = LsasProvenance(pack_id="demo", pack_version="1.0.0")
    assert prov.engine_version == "1.0.0"


def test_audit_metadata_defaults() -> None:
    meta = LsasAuditMetadata()
    assert meta.request_id is None
    assert isinstance(meta.scored_at, datetime)
    assert meta.scored_at.tzinfo is not None


def test_lsas_result_frozen() -> None:
    rds = RiskDomainScore(domain=RiskDomain.OTHER, score=0.0, finding_count=0)
    summary = RiskSummary(
        overall_score=0.0,
        domain_scores=(rds,),
        tier=RiskTier.SAFE,
        finding_count=0,
    )
    prov = LsasProvenance(pack_id="demo", pack_version="1.0.0")
    result = LsasResult(
        decision=Decision.ALLOW,
        risk_summary=summary,
        findings=(),
        remediations=(),
        provenance=prov,
    )
    with pytest.raises((AttributeError, TypeError)):
        result.decision = Decision.BLOCKED  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DecisionEvent
# ---------------------------------------------------------------------------


def test_decision_event_frozen() -> None:
    event = DecisionEvent(
        event_id="evt-1",
        decision=Decision.BLOCKED,
        overall_score=35.0,
        tier=RiskTier.HIGH,
        pack_id="demo",
    )
    assert event.event_id == "evt-1"
    with pytest.raises((AttributeError, TypeError)):
        event.decision = Decision.ALLOW  # type: ignore[misc]
