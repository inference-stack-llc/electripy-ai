"""LSAS — Language Safety Assurance System scoring runtime.

This module ports the LSAS scoring engine from the TypeScript
``lsas-framework`` monorepo (``packages/core``, ``packages/validators``,
``packages/policy-packs``) into idiomatic, fully-typed Python.

Quickstart::

    from electripy.ai.lsas import run_decision_engine
    from electripy.ai.lsas.policy_packs import DEMO_PACK
    from electripy.ai.lsas.validators import build_default_validators

    result = run_decision_engine(
        text="Contact me at alice@example.com",
        validators=build_default_validators(),
        pack=DEMO_PACK,
    )
    print(result.decision)        # Decision.ALLOW_WITH_WARNINGS
    print(result.risk_summary.tier)  # RiskTier.LOW
"""

from __future__ import annotations

from .domain import (
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
from .engine import derive_remediations, run_decision_engine
from .policy import (
    DEFAULT_DOMAIN_WEIGHTS,
    DEFAULT_SEVERITY_WEIGHTS,
    DEFAULT_THRESHOLDS,
    DomainWeights,
    PolicyPack,
    RiskThresholds,
    SeverityWeights,
    classify_tier,
    compute_risk_summary,
    map_risk_to_decision,
    severity_to_score,
)

__all__ = [
    # domain
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
    # policy
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
    # engine
    "derive_remediations",
    "run_decision_engine",
]
