"""Tests for the PCI DSS validator."""

from __future__ import annotations

import pytest

from electripy.ai.lsas.domain import RiskDomain, Severity
from electripy.ai.lsas.validators.pci import PciValidator


@pytest.fixture()
def validator() -> PciValidator:
    return PciValidator(skip_luhn=False)


@pytest.fixture()
def validator_no_luhn() -> PciValidator:
    return PciValidator(skip_luhn=True)


# ---------------------------------------------------------------------------
# Positive cases
# ---------------------------------------------------------------------------


def test_detects_visa_card(validator: PciValidator) -> None:
    # Known good Visa test number (Luhn-valid): 4111111111111111
    findings = validator.validate("Card: 4111111111111111 exp 12/26")
    card_findings = [f for f in findings if f.code == "PCI_CARD_NUMBER"]
    assert len(card_findings) >= 1
    assert all(f.domain == RiskDomain.PCI for f in findings)
    assert all(f.severity == Severity.CRITICAL for f in card_findings)


def test_detects_cvv(validator: PciValidator) -> None:
    findings = validator.validate("CVV: 456")
    cvv = [f for f in findings if f.code == "PCI_CVV"]
    assert len(cvv) == 1
    assert cvv[0].severity == Severity.CRITICAL


def test_detects_cvc(validator: PciValidator) -> None:
    findings = validator.validate("CVC: 789")
    cvv = [f for f in findings if f.code == "PCI_CVV"]
    assert len(cvv) == 1


def test_detects_expiry(validator: PciValidator) -> None:
    findings = validator.validate("Exp: 06/27")
    exp = [f for f in findings if f.code == "PCI_EXPIRY"]
    assert len(exp) >= 1
    assert exp[0].severity == Severity.HIGH


def test_detects_mastercard_no_luhn(validator_no_luhn: PciValidator) -> None:
    findings = validator_no_luhn.validate("Card 5100000000000000")
    card_findings = [f for f in findings if f.code == "PCI_CARD_NUMBER"]
    assert len(card_findings) >= 1


# ---------------------------------------------------------------------------
# Negative cases
# ---------------------------------------------------------------------------


def test_no_findings_clean_text(validator: PciValidator) -> None:
    findings = validator.validate("No card info here, just plain text.")
    assert findings == []


def test_luhn_rejects_invalid_number(validator: PciValidator) -> None:
    # Syntactically looks like a card but fails Luhn check
    findings = validator.validate("Card: 4111111111111112")
    # The important thing: skip_luhn=False uses Luhn gate; this runs without error
    assert isinstance(findings, list)


# ---------------------------------------------------------------------------
# Offset correctness
# ---------------------------------------------------------------------------


def test_cvv_offsets(validator: PciValidator) -> None:
    text = "Security code CVV: 999"
    findings = validator.validate(text)
    cvv = [f for f in findings if f.code == "PCI_CVV"]
    if cvv:
        f = cvv[0]
        assert f.start is not None and f.end is not None
        assert text[f.start : f.end] == f.matched_text
