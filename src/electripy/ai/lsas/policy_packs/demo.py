"""Demo baseline policy pack.

A broadly scoped pack suitable for development, demos, and as a starting
point for custom configurations.  It uses the default severity weights and
domain weights with moderate thresholds.
"""

from __future__ import annotations

from ..policy import DomainWeights, PolicyPack, RiskThresholds, SeverityWeights

__all__ = ["DEMO_PACK"]

DEMO_PACK = PolicyPack(
    pack_id="demo",
    version="1.0.0",
    description=(
        "Demo baseline pack — broadly scoped, moderate thresholds. "
        "Suitable for development and demos."
    ),
    severity_weights=SeverityWeights(
        low=1.0,
        medium=3.0,
        high=7.0,
        critical=15.0,
    ),
    domain_weights=DomainWeights(
        hipaa_phi=2.0,
        pci=2.0,
        security=1.5,
        fda=1.5,
        accessibility=1.0,
        other=1.0,
    ),
    thresholds=RiskThresholds(
        warn=5.0,
        redact=15.0,
        block=30.0,
        escalate=50.0,
    ),
    # All domains active
    enabled_domains=None,
)
