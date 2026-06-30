"""Prompt-injection validator — detects adversarial instruction-override attempts.

Ported from the prompt-injection validator in ``packages/validators/`` of the
``lsas-framework`` TypeScript monorepo.

Detects common prompt-injection attack patterns: instruction-override phrases,
jailbreak roleplay setups, ignore-previous-instructions variants, and
attempts to leak the system prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain import Finding, RiskDomain, Severity

__all__ = ["PromptInjectionValidator"]

# Each entry: (code, pattern, severity, message)
_PATTERNS: list[tuple[str, re.Pattern[str], Severity, str]] = [
    (
        "INJECT_IGNORE_INSTRUCTIONS",
        re.compile(
            r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions?",
            re.IGNORECASE,
        ),
        Severity.CRITICAL,
        "Prompt injection: ignore-previous-instructions attempt detected",
    ),
    (
        "INJECT_OVERRIDE_SYSTEM",
        re.compile(
            r"(?:new\s+)?(?:system|developer|admin)\s+(?:prompt|instruction|command|mode)"
            r"|override\s+(?:system|instructions?|prompt)",
            re.IGNORECASE,
        ),
        Severity.HIGH,
        "Prompt injection: system/developer instruction override attempt detected",
    ),
    (
        "INJECT_ROLEPLAY_JAILBREAK",
        re.compile(
            r"\b(?:jailbreak|DAN|do\s+anything\s+now|pretend\s+you(?:'re|\s+are)\s+(?:an?\s+)?AI\s+without)"
            r"|(?:act\s+as|roleplay\s+as)\s+(?:an?\s+)?(?:evil|uncensored|unfiltered|unrestricted)\b",
            re.IGNORECASE,
        ),
        Severity.HIGH,
        "Prompt injection: jailbreak/roleplay override attempt detected",
    ),
    (
        "INJECT_LEAK_PROMPT",
        re.compile(
            r"(?:repeat|print|show|reveal|output|tell\s+me)\s+(?:your\s+)?(?:system\s+prompt"
            r"|initial\s+instructions?|hidden\s+instructions?|full\s+prompt)",
            re.IGNORECASE,
        ),
        Severity.HIGH,
        "Prompt injection: system prompt extraction attempt detected",
    ),
    (
        "INJECT_DELIMITER_ESCAPE",
        re.compile(
            r"(?:```\s*(?:system|prompt|instruction)|<\|(?:im_start|system)\|>)",
            re.IGNORECASE,
        ),
        Severity.MEDIUM,
        "Prompt injection: delimiter/escape sequence detected",
    ),
    (
        "INJECT_TRANSLATE_IGNORE",
        re.compile(
            r"translate\s+the\s+following.*?ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?",
            re.IGNORECASE | re.DOTALL,
        ),
        Severity.HIGH,
        "Prompt injection: translate-then-ignore instructions pattern detected",
    ),
]


@dataclass(slots=True)
class PromptInjectionValidator:
    """Deterministic prompt-injection detector.

    All findings are tagged with :attr:`~.domain.RiskDomain.SECURITY`.
    """

    validator_id: str = "prompt_injection"

    def validate(self, text: str) -> list[Finding]:
        """Return prompt-injection findings sorted by start offset."""
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
