"""Tests for LSAS policy scoring functions and PolicyPack."""

from __future__ import annotations

import pytest

from electripy.ai.lsas.domain import Decision, Finding, RiskDomain, RiskTier, Severity
from electripy.ai.lsas.policy import (
    DEFAULT_THRESHOLDS,
    PolicyPack,
    RiskThresholds,
    SeverityWeights,
    classify_tier,
    compute_risk_summary,
    map_risk_to_decision,
    severity_to_score,
)

# ---------------------------------------------------------------------------
# severity_to_score
# ---------------------------------------------------------------------------


def test_severity_to_score_defaults() -> None:
    weights = SeverityWeights()
    assert severity_to_score(Severity.LOW, weights) == 1.0
    assert severity_to_score(Severity.MEDIUM, weights) == 3.0
    assert severity_to_score(Severity.HIGH, weights) == 7.0
    assert severity_to_score(Severity.CRITICAL, weights) == 15.0


def test_severity_to_score_custom_weights() -> None:
    weights = SeverityWeights(low=0.5, medium=1.0, high=2.0, critical=4.0)
    assert severity_to_score(Severity.CRITICAL, weights) == 4.0
    assert severity_to_score(Severity.LOW, weights) == 0.5


# ---------------------------------------------------------------------------
# map_risk_to_decision — exact boundary conditions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score,expected",
    [
        (0.0, Decision.ALLOW),
        (4.99, Decision.ALLOW),
        (5.0, Decision.ALLOW_WITH_WARNINGS),
        (14.99, Decision.ALLOW_WITH_WARNINGS),
        (15.0, Decision.REDACTED),
        (29.99, Decision.REDACTED),
        (30.0, Decision.BLOCKED),
        (49.99, Decision.BLOCKED),
        (50.0, Decision.ESCALATE_HITL),
        (100.0, Decision.ESCALATE_HITL),
    ],
)
def test_map_risk_to_decision_boundaries(score: float, expected: Decision) -> None:
    assert map_risk_to_decision(score, DEFAULT_THRESHOLDS) == expected


def test_map_risk_to_decision_custom_thresholds() -> None:
    thresholds = RiskThresholds(warn=10.0, redact=20.0, block=40.0, escalate=60.0)
    assert map_risk_to_decision(9.9, thresholds) == Decision.ALLOW
    assert map_risk_to_decision(10.0, thresholds) == Decision.ALLOW_WITH_WARNINGS
    assert map_risk_to_decision(20.0, thresholds) == Decision.REDACTED
    assert map_risk_to_decision(40.0, thresholds) == Decision.BLOCKED
    assert map_risk_to_decision(60.0, thresholds) == Decision.ESCALATE_HITL


# ---------------------------------------------------------------------------
# classify_tier — exact boundary conditions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score,expected",
    [
        (0.0, RiskTier.SAFE),
        (4.99, RiskTier.SAFE),
        (5.0, RiskTier.LOW),
        (14.99, RiskTier.LOW),
        (15.0, RiskTier.MEDIUM),
        (29.99, RiskTier.MEDIUM),
        (30.0, RiskTier.HIGH),
        (49.99, RiskTier.HIGH),
        (50.0, RiskTier.CRITICAL),
        (999.0, RiskTier.CRITICAL),
    ],
)
def test_classify_tier_boundaries(score: float, expected: RiskTier) -> None:
    assert classify_tier(score, DEFAULT_THRESHOLDS) == expected


# ---------------------------------------------------------------------------
# compute_risk_summary — scoring math
# ---------------------------------------------------------------------------


def _make_finding(severity: Severity, domain: RiskDomain) -> Finding:
    return Finding(
        validator_id="test",
        code="TEST",
        message="test",
        severity=severity,
        domain=domain,
    )


def test_compute_risk_summary_empty_findings() -> None:
    pack = PolicyPack(
        pack_id="test",
        version="1.0.0",
        description="",
    )
    summary = compute_risk_summary([], pack)
    assert summary.overall_score == 0.0
    assert summary.finding_count == 0
    assert summary.tier == RiskTier.SAFE
    assert len(summary.domain_scores) == 0


def test_compute_risk_summary_single_finding_math() -> None:
    """HIGH SECURITY: 7.0 × 1.5 = 10.5 → ALLOW_WITH_WARNINGS tier."""
    pack = PolicyPack(pack_id="test", version="1.0.0", description="")
    findings = [_make_finding(Severity.HIGH, RiskDomain.SECURITY)]
    summary = compute_risk_summary(findings, pack)
    # severity HIGH=7.0, domain SECURITY=1.5
    assert summary.overall_score == pytest.approx(7.0 * 1.5)  # 10.5
    assert summary.tier == RiskTier.LOW  # 5 ≤ 10.5 < 15
    assert summary.finding_count == 1
    assert len(summary.domain_scores) == 1
    assert summary.domain_scores[0].domain == RiskDomain.SECURITY
    assert summary.domain_scores[0].score == pytest.approx(10.5)


def test_compute_risk_summary_multiple_domains() -> None:
    """Two findings in different domains — verify additive scoring."""
    pack = PolicyPack(pack_id="test", version="1.0.0", description="")
    findings = [
        _make_finding(Severity.HIGH, RiskDomain.SECURITY),  # 7 × 1.5 = 10.5
        _make_finding(Severity.CRITICAL, RiskDomain.PCI),  # 15 × 2.0 = 30.0
    ]
    summary = compute_risk_summary(findings, pack)
    assert summary.overall_score == pytest.approx(10.5 + 30.0)  # 40.5
    assert summary.tier == RiskTier.HIGH  # 30 ≤ 40.5 < 50
    assert summary.finding_count == 2
    assert len(summary.domain_scores) == 2


def test_compute_risk_summary_same_domain_accumulates() -> None:
    """Multiple findings in the same domain are summed."""
    pack = PolicyPack(pack_id="test", version="1.0.0", description="")
    findings = [
        _make_finding(Severity.MEDIUM, RiskDomain.HIPAA_PHI),  # 3 × 2 = 6
        _make_finding(Severity.HIGH, RiskDomain.HIPAA_PHI),  # 7 × 2 = 14
    ]
    summary = compute_risk_summary(findings, pack)
    assert summary.overall_score == pytest.approx(6.0 + 14.0)  # 20.0
    assert summary.finding_count == 2
    assert len(summary.domain_scores) == 1
    assert summary.domain_scores[0].score == pytest.approx(20.0)
    assert summary.domain_scores[0].finding_count == 2


def test_compute_risk_summary_enabled_domains_filter() -> None:
    """Findings from excluded domains are not counted."""
    pack = PolicyPack(
        pack_id="test",
        version="1.0.0",
        description="",
        enabled_domains=(RiskDomain.SECURITY,),
    )
    findings = [
        _make_finding(Severity.CRITICAL, RiskDomain.PCI),  # filtered out
        _make_finding(Severity.HIGH, RiskDomain.SECURITY),  # 7 × 1.5 = 10.5
    ]
    summary = compute_risk_summary(findings, pack)
    assert summary.overall_score == pytest.approx(10.5)
    assert summary.finding_count == 1


def test_compute_risk_summary_escalate_tier() -> None:
    """Enough findings to hit the escalate threshold."""
    pack = PolicyPack(pack_id="test", version="1.0.0", description="")
    # CRITICAL × HIPAA_PHI = 15 × 2 = 30 per finding; need ≥ 50 total
    findings = [
        _make_finding(Severity.CRITICAL, RiskDomain.HIPAA_PHI),  # 30
        _make_finding(Severity.CRITICAL, RiskDomain.HIPAA_PHI),  # 30 → total 60
    ]
    summary = compute_risk_summary(findings, pack)
    assert summary.overall_score == pytest.approx(60.0)
    assert summary.tier == RiskTier.CRITICAL


# ---------------------------------------------------------------------------
# PolicyPack frozen
# ---------------------------------------------------------------------------


def test_policy_pack_frozen() -> None:
    pack = PolicyPack(pack_id="test", version="1.0.0", description="")
    with pytest.raises((AttributeError, TypeError)):
        pack.pack_id = "changed"  # type: ignore[misc]
