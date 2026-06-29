"""LSAS decision engine.

Ported from ``packages/core/src/engine.ts`` in the ``lsas-framework``
TypeScript monorepo.

The engine ties together validators, the risk-scoring policy, and remediation
derivation into a single ``run_decision_engine`` call.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from .domain import (
    Decision,
    Finding,
    LsasAuditMetadata,
    LsasProvenance,
    LsasResult,
    RemediationApplied,
    RiskDomain,
)
from .policy import PolicyPack, compute_risk_summary, map_risk_to_decision
from .validators.base import ValidatorPort

__all__ = [
    "derive_remediations",
    "run_decision_engine",
]

_ENGINE_VERSION = "1.0.0"


def derive_remediations(
    decision: Decision,
    findings: list[Finding],
) -> tuple[RemediationApplied, ...]:
    """Map a :class:`~.domain.Decision` to the recommended remediation actions.

    Mirrors ``deriveRemediations`` in ``engine.ts``:

    - ``BLOCKED``        → ``BLOCK`` remediation per distinct domain
    - ``REDACTED``       → ``REDACTION`` remediation per distinct domain
    - ``ESCALATE_HITL``  → ``ESCALATE`` remediation per distinct domain
    - ``ALLOW_WITH_WARNINGS`` → ``WARN`` remediation per distinct domain
    - ``ALLOW``          → no remediations

    Args:
        decision: The gate decision derived from risk scoring.
        findings: The findings that contributed to the decision.

    Returns:
        A tuple of :class:`~.domain.RemediationApplied` objects (possibly empty).
    """
    if decision == Decision.ALLOW:
        return ()

    # Collect distinct domains in the order they first appear
    seen_domains: list[RiskDomain] = []
    for f in findings:
        if f.domain not in seen_domains:
            seen_domains.append(f.domain)

    remediation_type_map: dict[Decision, str] = {
        Decision.BLOCKED: "BLOCK",
        Decision.REDACTED: "REDACTION",
        Decision.ESCALATE_HITL: "ESCALATE",
        Decision.ALLOW_WITH_WARNINGS: "WARN",
    }
    remediation_type = remediation_type_map.get(decision, "WARN")

    description_map: dict[str, str] = {
        "BLOCK": "Content blocked due to policy violation",
        "REDACTION": "Sensitive content redacted before delivery",
        "ESCALATE": "Content escalated to human-in-the-loop review",
        "WARN": "Content flagged with warnings; delivery allowed",
    }
    description = description_map[remediation_type]

    return tuple(
        RemediationApplied(
            remediation_type=remediation_type,
            description=description,
            domain=domain,
        )
        for domain in seen_domains
    )


def run_decision_engine(
    text: str,
    validators: list[ValidatorPort],
    pack: PolicyPack,
    *,
    audit: LsasAuditMetadata | None = None,
    sanitize: bool = True,
) -> LsasResult:
    """Run the full LSAS pipeline for a piece of text.

    Steps:

    1. Run each *validator* against *text* to collect
       :class:`~.domain.Finding` objects.
    2. Score the findings with ``compute_risk_summary`` using *pack*.
    3. Derive a :class:`~.domain.Decision` with ``map_risk_to_decision``.
    4. Derive remediations with ``derive_remediations``.
    5. Optionally build a redacted/sanitized copy of *text*.
    6. Return a frozen :class:`~.domain.LsasResult`.

    Args:
        text: The content to evaluate (prompt, response, tool argument, …).
        validators: List of :class:`~.validators.base.ValidatorPort` instances
            to run.  They are executed in order.
        pack: The :class:`~.policy.PolicyPack` supplying weights and
            thresholds.
        audit: Optional audit metadata to embed in the result.
        sanitize: When ``True`` (default), a redacted copy of *text* is
            computed for decisions of ``REDACTED`` or ``ALLOW_WITH_WARNINGS``
            by replacing each ``matched_text`` span with ``[REDACTED]``.

    Returns:
        A frozen :class:`~.domain.LsasResult`.
    """
    all_findings: list[Finding] = []
    for validator in validators:
        all_findings.extend(validator.validate(text))

    risk_summary = compute_risk_summary(all_findings, pack)
    decision = map_risk_to_decision(risk_summary.overall_score, pack.thresholds)
    remediations = derive_remediations(decision, all_findings)

    sanitized_text: str | None = None
    if sanitize and decision in (Decision.REDACTED, Decision.ALLOW_WITH_WARNINGS):
        sanitized_text = _apply_redactions(text, all_findings)

    provenance = LsasProvenance(
        pack_id=pack.pack_id,
        pack_version=pack.version,
        engine_version=_ENGINE_VERSION,
    )

    if audit is None:
        audit = LsasAuditMetadata(
            request_id=str(uuid.uuid4()),
            scored_at=datetime.now(tz=UTC),
        )

    return LsasResult(
        decision=decision,
        risk_summary=risk_summary,
        findings=tuple(all_findings),
        remediations=remediations,
        provenance=provenance,
        audit=audit,
        sanitized_text=sanitized_text,
    )


def _apply_redactions(text: str, findings: list[Finding]) -> str:
    """Replace all finding spans with ``[REDACTED]`` markers.

    Spans are sorted and de-overlapped before replacement so that the
    output is always well-defined regardless of validator ordering.
    """
    # Collect spans where we have offset information
    spans: list[tuple[int, int]] = [
        (f.start, f.end) for f in findings if f.start is not None and f.end is not None
    ]
    if not spans:
        return text

    # Sort and merge overlapping spans
    spans.sort()
    merged: list[tuple[int, int]] = [spans[0]]
    for start, end in spans[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    # Build the redacted string from right to left to preserve offsets
    result = list(text)
    for start, end in reversed(merged):
        result[start:end] = list("[REDACTED]")

    return "".join(result)
