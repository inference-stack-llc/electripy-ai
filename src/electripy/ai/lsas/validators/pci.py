"""PCI DSS validator — detects Payment Card Industry sensitive data.

Ported from the PCI validator in ``packages/validators/`` of the
``lsas-framework`` TypeScript monorepo.

Detects: credit/debit card numbers (Visa, Mastercard, Amex, Discover, Maestro),
CVV/CVC codes, and card expiry dates.

Note: card number detection uses a heuristic digit-group pattern followed
by a Luhn check to reduce false positives.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain import Finding, RiskDomain, Severity

__all__ = ["PciValidator"]

# Matches 13-19 contiguous digit groups with optional spaces or dashes as
# separators (covers Visa 13/16, MC 16, Amex 15, Discover 16, Maestro 12-19).
_CARD_NUMBER_RE = re.compile(
    r"\b(?:4[\d -]{11,18}|5[1-5][\d -]{13,16}|3[47][\d -]{12,15}"
    r"|6(?:011|5\d{2})[\d -]{11,14}|(?:2131|1800|35\d{3})[\d -]{10,14}"
    r"|\d[\d -]{11,17})\b"
)

# CVV: 3–4 digits often preceded by CVV/CVC/CSC keyword
_CVV_RE = re.compile(
    r"\b(?:CVV|CVC|CSC|CID)[:\s]*\d{3,4}\b",
    re.IGNORECASE,
)

# Expiry: MM/YY or MM/YYYY
_EXPIRY_RE = re.compile(
    r"\b(?:0[1-9]|1[0-2])/(?:\d{2}|\d{4})\b",
)


def _luhn_check(digits: str) -> bool:
    """Return True if *digits* passes the Luhn check."""
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _strip_separators(raw: str) -> str:
    """Remove spaces and dashes to get only digits."""
    return re.sub(r"[\s\-]", "", raw)


@dataclass(slots=True)
class PciValidator:
    """Deterministic PCI DSS sensitive-data detector.

    All findings are tagged with :attr:`~.domain.RiskDomain.PCI`.

    Args:
        skip_luhn: When ``True`` skip the Luhn check on card numbers (useful
            for testing with synthetic card numbers).
    """

    validator_id: str = "pci"
    skip_luhn: bool = False

    def validate(self, text: str) -> list[Finding]:
        """Return PCI findings sorted by start offset."""
        findings: list[Finding] = []

        # Card numbers
        for match in _CARD_NUMBER_RE.finditer(text):
            raw = match.group()
            digits = _strip_separators(raw)
            if len(digits) < 13:
                continue
            if not self.skip_luhn and not _luhn_check(digits):
                continue
            findings.append(
                Finding(
                    validator_id=self.validator_id,
                    code="PCI_CARD_NUMBER",
                    message="Payment card number detected (PCI DSS)",
                    severity=Severity.CRITICAL,
                    domain=RiskDomain.PCI,
                    start=match.start(),
                    end=match.end(),
                    matched_text=raw,
                )
            )

        # CVV / CVC codes
        for match in _CVV_RE.finditer(text):
            findings.append(
                Finding(
                    validator_id=self.validator_id,
                    code="PCI_CVV",
                    message="Card security code (CVV/CVC) detected (PCI DSS)",
                    severity=Severity.CRITICAL,
                    domain=RiskDomain.PCI,
                    start=match.start(),
                    end=match.end(),
                    matched_text=match.group(),
                )
            )

        # Expiry dates (only flag when near card-number context; here we flag all)
        for match in _EXPIRY_RE.finditer(text):
            findings.append(
                Finding(
                    validator_id=self.validator_id,
                    code="PCI_EXPIRY",
                    message="Card expiry date detected (PCI DSS)",
                    severity=Severity.HIGH,
                    domain=RiskDomain.PCI,
                    start=match.start(),
                    end=match.end(),
                    matched_text=match.group(),
                )
            )

        findings.sort(key=lambda f: (f.start or 0, f.end or 0))
        return findings
