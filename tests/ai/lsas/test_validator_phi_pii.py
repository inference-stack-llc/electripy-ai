"""Tests for the PHI/PII validator."""

from __future__ import annotations

import pytest

from electripy.ai.lsas.domain import RiskDomain, Severity
from electripy.ai.lsas.validators.phi_pii import PhiPiiValidator


@pytest.fixture()
def validator() -> PhiPiiValidator:
    return PhiPiiValidator()


# ---------------------------------------------------------------------------
# Positive cases — each pattern must fire
# ---------------------------------------------------------------------------


def test_detects_email(validator: PhiPiiValidator) -> None:
    findings = validator.validate("Contact alice@example.com for help")
    codes = {f.code for f in findings}
    assert "PHI_EMAIL" in codes
    email_findings = [f for f in findings if f.code == "PHI_EMAIL"]
    assert email_findings[0].matched_text == "alice@example.com"
    assert all(f.domain == RiskDomain.HIPAA_PHI for f in findings)


def test_detects_us_phone(validator: PhiPiiValidator) -> None:
    findings = validator.validate("Call 555-123-4567 now")
    codes = {f.code for f in findings}
    assert "PHI_PHONE_US" in codes


def test_detects_ssn(validator: PhiPiiValidator) -> None:
    findings = validator.validate("SSN is 123-45-6789")
    codes = {f.code for f in findings}
    assert "PHI_SSN" in codes
    ssn = next(f for f in findings if f.code == "PHI_SSN")
    assert ssn.severity == Severity.CRITICAL


def test_detects_dob_iso(validator: PhiPiiValidator) -> None:
    findings = validator.validate("DOB: 1985-03-22")
    codes = {f.code for f in findings}
    assert "PHI_DOB_ISO" in codes


def test_detects_dob_us(validator: PhiPiiValidator) -> None:
    findings = validator.validate("Born 03/22/1985")
    codes = {f.code for f in findings}
    assert "PHI_DOB_US" in codes


def test_detects_npi(validator: PhiPiiValidator) -> None:
    findings = validator.validate("Provider NPI: 1234567890")
    codes = {f.code for f in findings}
    assert "PHI_NPI" in codes


def test_detects_mrn(validator: PhiPiiValidator) -> None:
    findings = validator.validate("Patient ID: 98765432")
    codes = {f.code for f in findings}
    assert "PHI_MRN" in codes


# ---------------------------------------------------------------------------
# Negative cases — clean text must return no findings
# ---------------------------------------------------------------------------


def test_no_findings_clean_text(validator: PhiPiiValidator) -> None:
    findings = validator.validate("The quick brown fox jumps over the lazy dog.")
    assert findings == []


def test_no_findings_url_no_email(validator: PhiPiiValidator) -> None:
    # URLs with @ would match email patterns, so use a plain URL
    findings = validator.validate("Visit https://example.com for more info.")
    # No @ in URL, should not trigger PHI_EMAIL
    phi_email = [f for f in findings if f.code == "PHI_EMAIL"]
    assert phi_email == []


# ---------------------------------------------------------------------------
# Offset correctness
# ---------------------------------------------------------------------------


def test_finding_offsets_are_correct(validator: PhiPiiValidator) -> None:
    text = "Email: bob@test.org here"
    findings = validator.validate(text)
    email_findings = [f for f in findings if f.code == "PHI_EMAIL"]
    assert len(email_findings) >= 1
    f = email_findings[0]
    assert f.start is not None and f.end is not None
    assert text[f.start : f.end] == f.matched_text


# ---------------------------------------------------------------------------
# Sorting by offset
# ---------------------------------------------------------------------------


def test_findings_sorted_by_offset(validator: PhiPiiValidator) -> None:
    text = "Call 555-123-4567, SSN 123-45-6789, email alice@x.com"
    findings = validator.validate(text)
    starts = [f.start for f in findings if f.start is not None]
    assert starts == sorted(starts)
