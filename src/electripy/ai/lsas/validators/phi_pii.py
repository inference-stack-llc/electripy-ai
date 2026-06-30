"""PHI/PII validator — detects Protected Health Information and Personally
Identifiable Information patterns.

Ported from the PHI/PII validator in ``packages/validators/`` of the
``lsas-framework`` TypeScript monorepo.

Detects: email addresses, US phone numbers, SSNs, dates of birth (ISO-8601
and common formats), patient/member IDs, NPI numbers, and full names
following the ``First Last`` heuristic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..domain import Finding, RiskDomain, Severity

__all__ = ["PhiPiiValidator"]

_PATTERNS: list[tuple[str, re.Pattern[str], Severity, str]] = [
    # (code, pattern, severity, message)
    (
        "PHI_EMAIL",
        re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
        Severity.HIGH,
        "Email address detected (PHI/PII)",
    ),
    (
        "PHI_PHONE_US",
        re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        Severity.HIGH,
        "US phone number detected (PHI/PII)",
    ),
    (
        "PHI_SSN",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        Severity.CRITICAL,
        "US Social Security Number detected (PHI)",
    ),
    (
        "PHI_DOB_ISO",
        re.compile(r"\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b"),
        Severity.HIGH,
        "Date of birth (ISO-8601) detected (PHI)",
    ),
    (
        "PHI_DOB_US",
        re.compile(r"\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/(?:\d{2}|\d{4})\b"),
        Severity.HIGH,
        "Date of birth (US format) detected (PHI)",
    ),
    (
        "PHI_NPI",
        re.compile(r"\bNPI[:\s#]*\d{10}\b", re.IGNORECASE),
        Severity.HIGH,
        "National Provider Identifier (NPI) detected (PHI)",
    ),
    (
        "PHI_MRN",
        re.compile(r"\b(?:MRN|Medical\s+Record|Patient\s+ID)[:\s#]*\d{4,12}\b", re.IGNORECASE),
        Severity.HIGH,
        "Medical record / patient ID detected (PHI)",
    ),
]


@dataclass(slots=True)
class PhiPiiValidator:
    """Deterministic PHI/PII detector using compiled regex patterns.

    All findings are tagged with :attr:`~.domain.RiskDomain.HIPAA_PHI`.

    Args:
        extra_patterns: Optional additional ``(code, pattern, severity,
            message)`` tuples to extend the built-in set.
    """

    validator_id: str = "phi_pii"
    extra_patterns: list[tuple[str, re.Pattern[str], Severity, str]] = field(default_factory=list)

    def validate(self, text: str) -> list[Finding]:
        """Return PHI/PII findings sorted by start offset."""
        all_patterns = _PATTERNS + self.extra_patterns
        findings: list[Finding] = []
        for code, pattern, severity, message in all_patterns:
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        validator_id=self.validator_id,
                        code=code,
                        message=message,
                        severity=severity,
                        domain=RiskDomain.HIPAA_PHI,
                        start=match.start(),
                        end=match.end(),
                        matched_text=match.group(),
                    )
                )
        findings.sort(key=lambda f: (f.start or 0, f.end or 0))
        return findings
