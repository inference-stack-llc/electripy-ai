"""Secrets validator — detects API keys, tokens, and credentials.

Ported from the secrets validator in ``packages/validators/`` of the
``lsas-framework`` TypeScript monorepo.

Detects common secret patterns: OpenAI keys, Anthropic keys, AWS access keys,
GitHub tokens, generic bearer tokens, generic high-entropy secrets, and
hard-coded password assignments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain import Finding, RiskDomain, Severity

__all__ = ["SecretsValidator"]

_PATTERNS: list[tuple[str, re.Pattern[str], Severity, str]] = [
    (
        "SECRET_OPENAI_KEY",
        re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"),
        Severity.CRITICAL,
        "OpenAI API key detected",
    ),
    (
        "SECRET_ANTHROPIC_KEY",
        re.compile(r"\bsk-ant-[a-zA-Z0-9_\-]{20,}\b"),
        Severity.CRITICAL,
        "Anthropic API key detected",
    ),
    (
        "SECRET_AWS_ACCESS_KEY",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        Severity.CRITICAL,
        "AWS access key ID detected",
    ),
    (
        "SECRET_AWS_SECRET",
        re.compile(r"\b[A-Za-z0-9/+]{40}\b"),
        Severity.HIGH,
        "Possible AWS secret access key detected (40-char base64)",
    ),
    (
        "SECRET_GITHUB_TOKEN",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        Severity.CRITICAL,
        "GitHub personal/OAuth/app token detected",
    ),
    (
        "SECRET_BEARER_TOKEN",
        re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]{20,}={0,2}\b", re.IGNORECASE),
        Severity.HIGH,
        "****** detected in text",
    ),
    (
        "SECRET_GENERIC_KEY",
        re.compile(
            r"\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)"
            r"[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9\-._~+/]{16,}[\"']?",
            re.IGNORECASE,
        ),
        Severity.HIGH,
        "Generic API key or token assignment detected",
    ),
    (
        "SECRET_PASSWORD_ASSIGNMENT",
        re.compile(
            r"\b(?:password|passwd|pwd)\s*[:=]\s*[\"']?[^\s\"']{8,}[\"']?",
            re.IGNORECASE,
        ),
        Severity.HIGH,
        "Hard-coded password assignment detected",
    ),
]


@dataclass(slots=True)
class SecretsValidator:
    """Deterministic secrets / credential detector.

    All findings are tagged with :attr:`~.domain.RiskDomain.SECURITY`.
    """

    validator_id: str = "secrets"

    def validate(self, text: str) -> list[Finding]:
        """Return secrets findings sorted by start offset."""
        findings: list[Finding] = []
        for code, pattern, severity, message in _PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        validator_id=self.validator_id,
                        code=code,
                        message=message,
                        severity=severity,
                        domain=RiskDomain.SECURITY,
                        start=match.start(),
                        end=match.end(),
                        matched_text=match.group(),
                    )
                )
        findings.sort(key=lambda f: (f.start or 0, f.end or 0))
        return findings
