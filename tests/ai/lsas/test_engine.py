"""Tests for the LSAS decision engine."""

from __future__ import annotations

import pytest

from electripy.ai.lsas.domain import (
    Decision,
    Finding,
    RiskDomain,
    RiskTier,
    Severity,
)
from electripy.ai.lsas.engine import _apply_redactions, derive_remediations, run_decision_engine
from electripy.ai.lsas.policy import PolicyPack

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FixedValidator:
    """Validator that always returns a fixed list of findings."""

    def __init__(self, validator_id: str, findings: list[Finding]) -> None:
        self.validator_id = validator_id
        self._findings = findings

    def validate(self, text: str) -> list[Finding]:
        del text  # not used
        return list(self._findings)


class _EmptyValidator:
    """Validator that always returns no findings."""

    validator_id = "empty"

    def validate(self, text: str) -> list[Finding]:
        del text
        return []


def _make_finding(
    severity: Severity = Severity.HIGH,
    domain: RiskDomain = RiskDomain.SECURITY,
    start: int | None = None,
    end: int | None = None,
    matched_text: str | None = None,
) -> Finding:
    return Finding(
        validator_id="test",
        code="TEST",
        message="test",
        severity=severity,
        domain=domain,
        start=start,
        end=end,
        matched_text=matched_text,
    )


_DEMO_PACK = PolicyPack(pack_id="demo", version="1.0.0", description="")


# ---------------------------------------------------------------------------
# derive_remediations
# ---------------------------------------------------------------------------


def test_derive_remediations_allow_returns_empty() -> None:
    assert derive_remediations(Decision.ALLOW, []) == ()


def test_derive_remediations_blocked() -> None:
    findings = [_make_finding(domain=RiskDomain.PCI)]
    rems = derive_remediations(Decision.BLOCKED, findings)
    assert len(rems) == 1
    assert rems[0].remediation_type == "BLOCK"
    assert rems[0].domain == RiskDomain.PCI


def test_derive_remediations_redacted() -> None:
    findings = [_make_finding(domain=RiskDomain.HIPAA_PHI)]
    rems = derive_remediations(Decision.REDACTED, findings)
    assert len(rems) == 1
    assert rems[0].remediation_type == "REDACTION"


def test_derive_remediations_escalate() -> None:
    findings = [_make_finding(domain=RiskDomain.SECURITY)]
    rems = derive_remediations(Decision.ESCALATE_HITL, findings)
    assert len(rems) == 1
    assert rems[0].remediation_type == "ESCALATE"


def test_derive_remediations_warn() -> None:
    findings = [_make_finding(domain=RiskDomain.OTHER)]
    rems = derive_remediations(Decision.ALLOW_WITH_WARNINGS, findings)
    assert len(rems) == 1
    assert rems[0].remediation_type == "WARN"


def test_derive_remediations_deduplicated_by_domain() -> None:
    """Multiple findings in the same domain yield one remediation."""
    findings = [
        _make_finding(domain=RiskDomain.PCI),
        _make_finding(domain=RiskDomain.PCI),
    ]
    rems = derive_remediations(Decision.BLOCKED, findings)
    assert len(rems) == 1
    assert rems[0].domain == RiskDomain.PCI


def test_derive_remediations_multi_domain_order_preserved() -> None:
    """Each distinct domain gets a remediation, in first-appearance order."""
    findings = [
        _make_finding(domain=RiskDomain.PCI),
        _make_finding(domain=RiskDomain.SECURITY),
    ]
    rems = derive_remediations(Decision.BLOCKED, findings)
    assert len(rems) == 2
    assert rems[0].domain == RiskDomain.PCI
    assert rems[1].domain == RiskDomain.SECURITY


# ---------------------------------------------------------------------------
# _apply_redactions
# ---------------------------------------------------------------------------


def test_apply_redactions_no_offsets_returns_unchanged() -> None:
    text = "Hello world"
    findings = [_make_finding()]  # no start/end
    assert _apply_redactions(text, findings) == text


def test_apply_redactions_single_span() -> None:
    text = "email: alice@example.com end"
    findings = [_make_finding(start=7, end=24)]
    result = _apply_redactions(text, findings)
    assert result == "email: [REDACTED] end"


def test_apply_redactions_multiple_non_overlapping() -> None:
    text = "a@b.com and c@d.com here"
    findings = [
        _make_finding(start=0, end=7),
        _make_finding(start=12, end=19),
    ]
    result = _apply_redactions(text, findings)
    assert result == "[REDACTED] and [REDACTED] here"


def test_apply_redactions_overlapping_spans_merged() -> None:
    text = "abcdef"
    findings = [
        _make_finding(start=0, end=4),
        _make_finding(start=2, end=6),
    ]
    result = _apply_redactions(text, findings)
    assert result == "[REDACTED]"


# ---------------------------------------------------------------------------
# run_decision_engine
# ---------------------------------------------------------------------------


def test_run_decision_engine_no_findings_returns_allow() -> None:
    result = run_decision_engine(
        text="safe content",
        validators=[_EmptyValidator()],
        pack=_DEMO_PACK,
    )
    assert result.decision == Decision.ALLOW
    assert result.risk_summary.overall_score == 0.0
    assert result.risk_summary.tier == RiskTier.SAFE
    assert result.findings == ()
    assert result.remediations == ()
    assert result.sanitized_text is None


def test_run_decision_engine_low_risk_warns() -> None:
    """One MEDIUM OTHER finding: 3 × 1.0 = 3.0 < warn threshold 5 → ALLOW."""
    findings = [_make_finding(Severity.MEDIUM, RiskDomain.OTHER)]
    result = run_decision_engine(
        text="x",
        validators=[_FixedValidator("v", findings)],
        pack=_DEMO_PACK,
    )
    # 3.0 < 5.0 → ALLOW
    assert result.decision == Decision.ALLOW


def test_run_decision_engine_warn_decision() -> None:
    """HIGH SECURITY: 7 × 1.5 = 10.5 → ALLOW_WITH_WARNINGS."""
    findings = [_make_finding(Severity.HIGH, RiskDomain.SECURITY)]
    result = run_decision_engine(
        text="******",
        validators=[_FixedValidator("v", findings)],
        pack=_DEMO_PACK,
    )
    assert result.decision == Decision.ALLOW_WITH_WARNINGS
    assert len(result.remediations) >= 1


def test_run_decision_engine_block_decision() -> None:
    """CRITICAL PCI: 15 × 2 = 30 → BLOCKED."""
    findings = [_make_finding(Severity.CRITICAL, RiskDomain.PCI)]
    result = run_decision_engine(
        text="card 4111111111111111",
        validators=[_FixedValidator("v", findings)],
        pack=_DEMO_PACK,
    )
    assert result.decision == Decision.BLOCKED
    assert result.remediations[0].remediation_type == "BLOCK"


def test_run_decision_engine_escalate_decision() -> None:
    """4 × CRITICAL PCI: 4 × 30 = 120 → ESCALATE_HITL."""
    findings = [_make_finding(Severity.CRITICAL, RiskDomain.PCI)] * 4
    result = run_decision_engine(
        text="x",
        validators=[_FixedValidator("v", findings)],
        pack=_DEMO_PACK,
    )
    assert result.decision == Decision.ESCALATE_HITL
    assert result.remediations[0].remediation_type == "ESCALATE"


def test_run_decision_engine_sanitize_text() -> None:
    """REDACTED decision produces sanitized_text with spans replaced."""
    text = "email: alice@example.com end"
    findings = [
        Finding(
            validator_id="v",
            code="TEST",
            message="m",
            severity=Severity.HIGH,
            domain=RiskDomain.HIPAA_PHI,
            start=7,
            end=24,
            matched_text="alice@example.com",
        )
    ]
    # Set thresholds so 7×2=14 falls in redact zone (5 ≤ 14 < 15 → WARN at default pack)
    # Use custom thresholds to force REDACTED
    pack = PolicyPack(
        pack_id="test",
        version="1.0.0",
        description="",
        thresholds=__import__(
            "electripy.ai.lsas.policy", fromlist=["RiskThresholds"]
        ).RiskThresholds(warn=5.0, redact=10.0, block=30.0, escalate=50.0),
    )
    result = run_decision_engine(
        text=text,
        validators=[_FixedValidator("v", findings)],
        pack=pack,
    )
    assert result.decision == Decision.REDACTED
    assert result.sanitized_text == "email: [REDACTED] end"


def test_run_decision_engine_provenance_populated() -> None:
    result = run_decision_engine(
        text="x",
        validators=[_EmptyValidator()],
        pack=_DEMO_PACK,
    )
    assert result.provenance.pack_id == "demo"
    assert result.provenance.pack_version == "1.0.0"
    assert result.provenance.engine_version == "1.0.0"


def test_run_decision_engine_audit_populated() -> None:
    result = run_decision_engine(
        text="x",
        validators=[_EmptyValidator()],
        pack=_DEMO_PACK,
    )
    assert result.audit is not None
    assert result.audit.request_id is not None


def test_run_decision_engine_multiple_validators() -> None:
    """Findings from multiple validators are all scored."""
    findings_a = [_make_finding(Severity.HIGH, RiskDomain.SECURITY)]  # 7×1.5=10.5
    findings_b = [_make_finding(Severity.HIGH, RiskDomain.HIPAA_PHI)]  # 7×2=14
    result = run_decision_engine(
        text="x",
        validators=[
            _FixedValidator("va", findings_a),
            _FixedValidator("vb", findings_b),
        ],
        pack=_DEMO_PACK,
    )
    assert result.risk_summary.overall_score == pytest.approx(10.5 + 14.0)  # 24.5
    assert result.decision == Decision.REDACTED
