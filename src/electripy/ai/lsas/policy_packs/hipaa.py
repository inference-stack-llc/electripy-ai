"""HIPAA / Protected Health Information policy pack.

A stricter pack tuned for workloads that handle HIPAA-regulated PHI data.
The HIPAA_PHI domain carries an elevated multiplier, and the thresholds are
tighter than the demo baseline so that even a single PHI finding triggers at
least a warning.
"""

from __future__ import annotations

from ..domain import RiskDomain
from ..policy import DomainWeights, PolicyPack, RiskThresholds, SeverityWeights

__all__ = ["HIPAA_PACK"]

HIPAA_PACK = PolicyPack(
    pack_id="hipaa",
    version="1.0.0",
    description=(
        "HIPAA/PHI policy pack — elevated sensitivity for Protected Health "
        "Information.  Tighter thresholds ensure even a single medium PHI "
        "finding triggers a warning."
    ),
    severity_weights=SeverityWeights(
        low=2.0,
        medium=5.0,
        high=10.0,
        critical=20.0,
    ),
    domain_weights=DomainWeights(
        hipaa_phi=3.0,  # amplified
        pci=2.0,
        security=2.0,
        fda=2.0,
        accessibility=1.0,
        other=1.0,
    ),
    thresholds=RiskThresholds(
        warn=3.0,  # a single MEDIUM PHI finding scores 5 × 3 = 15, far exceeding warn (3) → warns
        redact=10.0,
        block=25.0,
        escalate=40.0,
    ),
    # Restrict to PHI-relevant domains only; security included for tokens
    enabled_domains=(
        RiskDomain.HIPAA_PHI,
        RiskDomain.SECURITY,
        RiskDomain.OTHER,
    ),
)
