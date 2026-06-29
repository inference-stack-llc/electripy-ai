"""LSAS policy scoring functions and PolicyPack definition.

Ported from ``packages/core/src/policy.ts`` in the ``lsas-framework``
TypeScript monorepo.

Scoring maths (preserved exactly):
  weighted_score(finding) = severity_weight(finding.severity)
                            × domain_weight(finding.domain)
  domain_score             = Σ weighted_scores  for that domain
  overall_score            = Σ domain_scores

Tier / decision are then derived by comparing ``overall_score`` against the
``RiskThresholds`` of the active ``PolicyPack``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .domain import Decision, Finding, RiskDomain, RiskDomainScore, RiskSummary, RiskTier, Severity

__all__ = [
    "DEFAULT_DOMAIN_WEIGHTS",
    "DEFAULT_SEVERITY_WEIGHTS",
    "DEFAULT_THRESHOLDS",
    "DomainWeights",
    "PolicyPack",
    "RiskThresholds",
    "SeverityWeights",
    "classify_tier",
    "compute_risk_summary",
    "map_risk_to_decision",
    "severity_to_score",
]


# ---------------------------------------------------------------------------
# Weight tables
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SeverityWeights:
    """Numeric weight assigned to each severity level.

    Higher values increase the contribution of findings at that severity to
    the overall risk score.
    """

    low: float = 1.0
    medium: float = 3.0
    high: float = 7.0
    critical: float = 15.0


@dataclass(frozen=True, slots=True)
class DomainWeights:
    """Numeric multiplier applied per risk domain.

    Allows policy authors to amplify or dampen the score contribution from
    specific regulated domains relative to each other.
    """

    hipaa_phi: float = 2.0
    pci: float = 2.0
    security: float = 1.5
    fda: float = 1.5
    accessibility: float = 1.0
    other: float = 1.0


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RiskThresholds:
    """Score thresholds that gate decisions and tier classification.

    Attributes:
        warn: Score at or above which the decision becomes
            ``ALLOW_WITH_WARNINGS``.
        redact: Score at or above which the decision becomes ``REDACTED``.
        block: Score at or above which the decision becomes ``BLOCKED``.
        escalate: Score at or above which the decision becomes
            ``ESCALATE_HITL``.
    """

    warn: float = 5.0
    redact: float = 15.0
    block: float = 30.0
    escalate: float = 50.0


# ---------------------------------------------------------------------------
# PolicyPack
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PolicyPack:
    """Named, versioned collection of weights and thresholds.

    Attributes:
        pack_id: Stable identifier used in provenance records.
        version: SemVer-style version string.
        description: Human-readable description.
        severity_weights: Per-severity score weights.
        domain_weights: Per-domain score multipliers.
        thresholds: Decision gate thresholds.
        enabled_domains: Domains to score; ``None`` means all domains.
    """

    pack_id: str
    version: str
    description: str
    severity_weights: SeverityWeights = field(default_factory=SeverityWeights)
    domain_weights: DomainWeights = field(default_factory=DomainWeights)
    thresholds: RiskThresholds = field(default_factory=RiskThresholds)
    enabled_domains: tuple[RiskDomain, ...] | None = None


# ---------------------------------------------------------------------------
# Module-level defaults (used by the demo pack and as fallback)
# ---------------------------------------------------------------------------

DEFAULT_SEVERITY_WEIGHTS = SeverityWeights()
DEFAULT_DOMAIN_WEIGHTS = DomainWeights()
DEFAULT_THRESHOLDS = RiskThresholds()


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------


def severity_to_score(severity: Severity, weights: SeverityWeights) -> float:
    """Convert a :class:`~.domain.Severity` to its numeric weight.

    Args:
        severity: The severity level of a finding.
        weights: The severity weight table from the active policy pack.

    Returns:
        The numeric weight for *severity*.
    """
    mapping: dict[Severity, float] = {
        Severity.LOW: weights.low,
        Severity.MEDIUM: weights.medium,
        Severity.HIGH: weights.high,
        Severity.CRITICAL: weights.critical,
    }
    return mapping[severity]


def _domain_weight(domain: RiskDomain, weights: DomainWeights) -> float:
    """Return the numeric multiplier for *domain*."""
    mapping: dict[RiskDomain, float] = {
        RiskDomain.HIPAA_PHI: weights.hipaa_phi,
        RiskDomain.PCI: weights.pci,
        RiskDomain.SECURITY: weights.security,
        RiskDomain.FDA: weights.fda,
        RiskDomain.ACCESSIBILITY: weights.accessibility,
        RiskDomain.OTHER: weights.other,
    }
    return mapping[domain]


def compute_risk_summary(
    findings: list[Finding],
    pack: PolicyPack,
) -> RiskSummary:
    """Aggregate findings into a :class:`~.domain.RiskSummary`.

    Scoring algorithm (mirrors ``computeRiskSummary`` in ``policy.ts``):

    1. For each finding compute ``severity_weight × domain_weight``.
    2. Accumulate into a per-domain bucket.
    3. Sum domain buckets to produce ``overall_score``.
    4. Classify ``overall_score`` into a :class:`~.domain.RiskTier`.

    Args:
        findings: Ordered list of :class:`~.domain.Finding` objects to score.
        pack: Active :class:`PolicyPack` supplying weights and thresholds.

    Returns:
        A :class:`~.domain.RiskSummary` with per-domain and overall scores.
    """
    # Filter to enabled domains when the pack restricts them
    active_findings: list[Finding]
    if pack.enabled_domains is not None:
        active_findings = [f for f in findings if f.domain in pack.enabled_domains]
    else:
        active_findings = list(findings)

    # Accumulate per-domain
    domain_buckets: dict[RiskDomain, float] = {}
    domain_counts: dict[RiskDomain, int] = {}
    for finding in active_findings:
        sev_score = severity_to_score(finding.severity, pack.severity_weights)
        dom_weight = _domain_weight(finding.domain, pack.domain_weights)
        weighted = sev_score * dom_weight
        domain_buckets[finding.domain] = domain_buckets.get(finding.domain, 0.0) + weighted
        domain_counts[finding.domain] = domain_counts.get(finding.domain, 0) + 1

    overall_score = sum(domain_buckets.values())

    domain_scores = tuple(
        RiskDomainScore(
            domain=domain,
            score=score,
            finding_count=domain_counts[domain],
        )
        for domain, score in sorted(domain_buckets.items(), key=lambda kv: kv[1], reverse=True)
    )

    tier = classify_tier(overall_score, pack.thresholds)

    return RiskSummary(
        overall_score=overall_score,
        domain_scores=domain_scores,
        tier=tier,
        finding_count=len(active_findings),
    )


def classify_tier(score: float, thresholds: RiskThresholds) -> RiskTier:
    """Map a numeric risk score to a :class:`~.domain.RiskTier`.

    Args:
        score: Aggregated overall risk score.
        thresholds: Threshold configuration from the active policy pack.

    Returns:
        The appropriate :class:`~.domain.RiskTier`.
    """
    if score >= thresholds.escalate:
        return RiskTier.CRITICAL
    if score >= thresholds.block:
        return RiskTier.HIGH
    if score >= thresholds.redact:
        return RiskTier.MEDIUM
    if score >= thresholds.warn:
        return RiskTier.LOW
    return RiskTier.SAFE


def map_risk_to_decision(score: float, thresholds: RiskThresholds) -> Decision:
    """Convert an overall risk score to a :class:`~.domain.Decision`.

    Mirrors ``mapRiskToDecision`` in ``policy.ts``::

        if score >= escalate → ESCALATE_HITL
        if score >= block    → BLOCKED
        if score >= redact   → REDACTED
        if score >= warn     → ALLOW_WITH_WARNINGS
        else                 → ALLOW

    Args:
        score: Aggregated overall risk score.
        thresholds: Threshold configuration from the active policy pack.

    Returns:
        The appropriate :class:`~.domain.Decision`.
    """
    if score >= thresholds.escalate:
        return Decision.ESCALATE_HITL
    if score >= thresholds.block:
        return Decision.BLOCKED
    if score >= thresholds.redact:
        return Decision.REDACTED
    if score >= thresholds.warn:
        return Decision.ALLOW_WITH_WARNINGS
    return Decision.ALLOW
