"""PCI DSS policy pack.

A stricter pack tuned for workloads that handle payment card data.  The PCI
domain carries an elevated multiplier, and thresholds ensure that any card
number triggers an immediate block.
"""

from __future__ import annotations

from ..domain import RiskDomain
from ..policy import DomainWeights, PolicyPack, RiskThresholds, SeverityWeights

__all__ = ["PCI_PACK"]

PCI_PACK = PolicyPack(
    pack_id="pci",
    version="1.0.0",
    description=(
        "PCI DSS policy pack — elevated sensitivity for payment card data.  "
        "A single CRITICAL PCI finding triggers an immediate block."
    ),
    severity_weights=SeverityWeights(
        low=2.0,
        medium=5.0,
        high=10.0,
        critical=20.0,
    ),
    domain_weights=DomainWeights(
        hipaa_phi=1.5,
        pci=3.0,  # amplified
        security=2.0,
        fda=1.0,
        accessibility=1.0,
        other=1.0,
    ),
    thresholds=RiskThresholds(
        warn=5.0,
        redact=10.0,
        block=20.0,  # a CRITICAL PCI finding scores 20 × 3 = 60, which exceeds escalate (45); block threshold is set for lesser violations
        escalate=45.0,
    ),
    # Restrict to payment-relevant domains only
    enabled_domains=(
        RiskDomain.PCI,
        RiskDomain.SECURITY,
        RiskDomain.OTHER,
    ),
)
