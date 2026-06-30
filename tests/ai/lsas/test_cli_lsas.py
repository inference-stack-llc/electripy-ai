"""Tests for the ``electripy lsas score`` and ``electripy lsas packs`` CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from electripy.cli.app import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# lsas score
# ---------------------------------------------------------------------------


def test_lsas_score_clean_text() -> None:
    result = runner.invoke(app, ["lsas", "score", "Hello safe world"])
    assert result.exit_code == 0
    assert "ALLOW" in result.output


def test_lsas_score_email_warns() -> None:
    result = runner.invoke(app, ["lsas", "score", "Contact alice@example.com"])
    assert result.exit_code == 0
    assert "ALLOW_WITH_WARNINGS" in result.output


def test_lsas_score_ssn_blocks() -> None:
    result = runner.invoke(app, ["lsas", "score", "SSN: 123-45-6789"])
    assert result.exit_code == 0
    # BLOCKED or ESCALATE_HITL depending on total score
    assert any(word in result.output for word in ("BLOCKED", "ESCALATE_HITL"))


def test_lsas_score_with_demo_pack() -> None:
    result = runner.invoke(app, ["lsas", "score", "--pack", "demo", "safe text"])
    assert result.exit_code == 0
    assert "ALLOW" in result.output


def test_lsas_score_with_hipaa_pack() -> None:
    result = runner.invoke(app, ["lsas", "score", "--pack", "hipaa", "Patient SSN: 123-45-6789"])
    assert result.exit_code == 0
    assert any(word in result.output for word in ("BLOCKED", "ESCALATE_HITL"))


def test_lsas_score_with_pci_pack() -> None:
    result = runner.invoke(app, ["lsas", "score", "--pack", "pci", "Card 4111111111111111"])
    assert result.exit_code == 0
    assert any(word in result.output for word in ("BLOCKED", "ESCALATE_HITL"))


def test_lsas_score_unknown_pack_exits_nonzero() -> None:
    result = runner.invoke(app, ["lsas", "score", "--pack", "unknown", "text"])
    assert result.exit_code != 0


def test_lsas_score_shows_risk_tier() -> None:
    result = runner.invoke(app, ["lsas", "score", "hello world"])
    assert result.exit_code == 0
    assert "SAFE" in result.output


def test_lsas_score_shows_overall_score() -> None:
    result = runner.invoke(app, ["lsas", "score", "safe text here"])
    assert result.exit_code == 0
    # The output should contain a numeric score like "0.00"
    assert "0.00" in result.output or "Score" in result.output


def test_lsas_score_shows_findings_when_present() -> None:
    result = runner.invoke(app, ["lsas", "score", "alice@example.com"])
    assert result.exit_code == 0
    assert "PHI_EMAIL" in result.output


# ---------------------------------------------------------------------------
# lsas packs
# ---------------------------------------------------------------------------


def test_lsas_packs_lists_all_packs() -> None:
    result = runner.invoke(app, ["lsas", "packs"])
    assert result.exit_code == 0
    assert "demo" in result.output
    assert "hipaa" in result.output
    assert "pci" in result.output


def test_lsas_packs_shows_thresholds() -> None:
    result = runner.invoke(app, ["lsas", "packs"])
    assert result.exit_code == 0
    # Demo pack thresholds: 5.0 / 15.0 / 30.0 / 50.0
    assert "5.0" in result.output
