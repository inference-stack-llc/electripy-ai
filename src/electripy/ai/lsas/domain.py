"""Domain models for the LSAS (Language Safety Assurance System) scoring runtime.

Ported from ``packages/core/src/domain.ts`` in the ``lsas-framework`` TypeScript
monorepo.  All types are immutable frozen dataclasses or StrEnum members so they
can be used safely across threads and as dict keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

__all__ = [
    "Decision",
    "DecisionEvent",
    "Finding",
    "LsasAuditMetadata",
    "LsasProvenance",
    "LsasResult",
    "RemediationApplied",
    "RiskDomain",
    "RiskDomainScore",
    "RiskSummary",
    "RiskTier",
    "Severity",
]


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Decision(StrEnum):
    """Final LSAS gate decision for a scored request/response."""

    ALLOW = "ALLOW"
    ALLOW_WITH_WARNINGS = "ALLOW_WITH_WARNINGS"
    REDACTED = "REDACTED"
    BLOCKED = "BLOCKED"
    ESCALATE_HITL = "ESCALATE_HITL"


class RiskDomain(StrEnum):
    """Regulated or sensitivity domain for a risk finding."""

    HIPAA_PHI = "HIPAA_PHI"
    PCI = "PCI"
    SECURITY = "SECURITY"
    FDA = "FDA"
    ACCESSIBILITY = "ACCESSIBILITY"
    OTHER = "OTHER"


class Severity(StrEnum):
    """Severity of an individual risk finding."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskTier(StrEnum):
    """Tier bucket derived from the overall risk score."""

    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Finding:
    """A single risk finding emitted by a validator.

    Attributes:
        validator_id: Stable identifier for the originating validator.
        code: Stable violation code (e.g. ``PHI_EMAIL``).
        message: Human-readable description.
        severity: Severity level of this finding.
        domain: Risk domain this finding belongs to.
        start: Optional character start offset in the scanned text.
        end: Optional character end offset in the scanned text.
        matched_text: Optional snippet that triggered the finding.
    """

    validator_id: str
    code: str
    message: str
    severity: Severity
    domain: RiskDomain
    start: int | None = None
    end: int | None = None
    matched_text: str | None = None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RiskDomainScore:
    """Aggregated score for a single risk domain.

    Attributes:
        domain: The risk domain.
        score: Weighted numeric risk score for this domain.
        finding_count: Number of findings contributing to this score.
    """

    domain: RiskDomain
    score: float
    finding_count: int


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """Aggregated risk summary across all domains.

    Attributes:
        overall_score: Sum of all domain scores.
        domain_scores: Per-domain breakdown.
        tier: Risk tier derived from thresholds.
        finding_count: Total number of findings.
    """

    overall_score: float
    domain_scores: tuple[RiskDomainScore, ...]
    tier: RiskTier
    finding_count: int


# ---------------------------------------------------------------------------
# Remediations
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RemediationApplied:
    """A remediation action recommended or applied by the engine.

    Attributes:
        remediation_type: One of ``BLOCK``, ``REDACTION``, ``ESCALATE``, ``WARN``.
        description: Human-readable explanation.
        domain: The risk domain this remediation addresses.
    """

    remediation_type: str
    description: str
    domain: RiskDomain


# ---------------------------------------------------------------------------
# Provenance and audit
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LsasProvenance:
    """Records the policy pack and version used for scoring.

    Attributes:
        pack_id: Stable identifier for the policy pack.
        pack_version: SemVer-style version string of the policy pack.
        engine_version: Version of the LSAS scoring engine itself.
    """

    pack_id: str
    pack_version: str
    engine_version: str = "1.0.0"


@dataclass(frozen=True, slots=True)
class LsasAuditMetadata:
    """Contextual audit metadata attached to an LSAS result.

    Attributes:
        request_id: Optional correlation ID for the request.
        actor_id: Optional identifier of the actor making the request.
        tenant_id: Optional tenant identifier.
        scored_at: UTC timestamp when scoring was performed.
        tags: Arbitrary key-value pairs for routing / SIEM export.
    """

    request_id: str | None = None
    actor_id: str | None = None
    tenant_id: str | None = None
    scored_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    tags: tuple[tuple[str, str], ...] = ()


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LsasResult:
    """Complete LSAS scoring result for a piece of content.

    Attributes:
        decision: Final gate decision.
        risk_summary: Aggregated risk summary with tier and domain scores.
        findings: Ordered list of all risk findings.
        remediations: Recommended remediation actions.
        provenance: Policy pack and engine version used for scoring.
        audit: Optional audit metadata.
        sanitized_text: Redacted/sanitized version of the input text when the
            decision is ``REDACTED`` or ``ALLOW_WITH_WARNINGS``.  ``None``
            otherwise.
    """

    decision: Decision
    risk_summary: RiskSummary
    findings: tuple[Finding, ...]
    remediations: tuple[RemediationApplied, ...]
    provenance: LsasProvenance
    audit: LsasAuditMetadata | None = None
    sanitized_text: str | None = None


# ---------------------------------------------------------------------------
# Decision event (audit log record)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DecisionEvent:
    """Immutable audit log record for a single LSAS decision.

    Attributes:
        event_id: Unique identifier for this event.
        decision: The decision that was reached.
        overall_score: The overall numeric risk score.
        tier: The risk tier.
        pack_id: Policy pack used.
        request_id: Optional request correlation ID.
        tenant_id: Optional tenant identifier.
        occurred_at: UTC timestamp of the event.
    """

    event_id: str
    decision: Decision
    overall_score: float
    tier: RiskTier
    pack_id: str
    request_id: str | None = None
    tenant_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
