"""Tests for the secrets validator."""

from __future__ import annotations

import pytest

from electripy.ai.lsas.domain import RiskDomain, Severity
from electripy.ai.lsas.validators.secrets import SecretsValidator


@pytest.fixture()
def validator() -> SecretsValidator:
    return SecretsValidator()


# ---------------------------------------------------------------------------
# Positive cases
# ---------------------------------------------------------------------------


def test_detects_openai_key(validator: SecretsValidator) -> None:
    findings = validator.validate("Key: sk-abcdef1234567890abcdef1234567890")
    codes = {f.code for f in findings}
    assert "SECRET_OPENAI_KEY" in codes
    secret = next(f for f in findings if f.code == "SECRET_OPENAI_KEY")
    assert secret.severity == Severity.CRITICAL
    assert secret.domain == RiskDomain.SECURITY


def test_detects_anthropic_key(validator: SecretsValidator) -> None:
    findings = validator.validate("Key: sk-ant-abcdef1234567890abcdef1234567890")
    codes = {f.code for f in findings}
    assert "SECRET_ANTHROPIC_KEY" in codes


def test_detects_aws_access_key(validator: SecretsValidator) -> None:
    findings = validator.validate("AKIAIOSFODNN7EXAMPLE is the key ID")
    codes = {f.code for f in findings}
    assert "SECRET_AWS_ACCESS_KEY" in codes


def test_detects_github_token(validator: SecretsValidator) -> None:
    findings = validator.validate("Token: ghp_abcdefghijklmnopqrstuvwxyz012345678901")
    codes = {f.code for f in findings}
    assert "SECRET_GITHUB_TOKEN" in codes


def test_detects_generic_key_assignment(validator: SecretsValidator) -> None:
    findings = validator.validate("api_key=supersecretvalue12345678901234")
    codes = {f.code for f in findings}
    assert "SECRET_GENERIC_KEY" in codes


def test_detects_password_assignment(validator: SecretsValidator) -> None:
    findings = validator.validate("password = hunter2secret")
    codes = {f.code for f in findings}
    assert "SECRET_PASSWORD_ASSIGNMENT" in codes


# ---------------------------------------------------------------------------
# Negative cases
# ---------------------------------------------------------------------------


def test_no_findings_clean_text(validator: SecretsValidator) -> None:
    findings = validator.validate("Hello world, this is safe.")
    assert findings == []


def test_short_key_not_detected(validator: SecretsValidator) -> None:
    # Too short to be a real API key
    findings = validator.validate("sk-short")
    openai_findings = [f for f in findings if f.code == "SECRET_OPENAI_KEY"]
    assert openai_findings == []


# ---------------------------------------------------------------------------
# Offset correctness
# ---------------------------------------------------------------------------


def test_finding_offsets_correct(validator: SecretsValidator) -> None:
    key = "sk-abcdef1234567890abcdef1234567890"
    text = f"Use this key: {key} today"
    findings = validator.validate(text)
    openai_findings = [f for f in findings if f.code == "SECRET_OPENAI_KEY"]
    assert len(openai_findings) >= 1
    f = openai_findings[0]
    assert f.start is not None and f.end is not None
    assert text[f.start : f.end] == f.matched_text
