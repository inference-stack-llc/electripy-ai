"""Tests for LSAS policy packs."""

from __future__ import annotations

import pytest

from electripy.ai.lsas.policy_packs import DEMO_PACK, HIPAA_PACK, PCI_PACK, get_pack, list_packs


def test_get_pack_demo() -> None:
    pack = get_pack("demo")
    assert pack is DEMO_PACK
    assert pack.pack_id == "demo"


def test_get_pack_hipaa() -> None:
    pack = get_pack("hipaa")
    assert pack is HIPAA_PACK
    assert pack.pack_id == "hipaa"


def test_get_pack_pci() -> None:
    pack = get_pack("pci")
    assert pack is PCI_PACK
    assert pack.pack_id == "pci"


def test_get_pack_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_pack("nonexistent")


def test_list_packs_returns_all() -> None:
    packs = list_packs()
    ids = [p.pack_id for p in packs]
    assert "demo" in ids
    assert "hipaa" in ids
    assert "pci" in ids
    assert len(packs) == 3


def test_packs_are_frozen() -> None:
    for pack in list_packs():
        with pytest.raises((AttributeError, TypeError)):
            pack.pack_id = "changed"  # type: ignore[misc]


def test_hipaa_pack_has_restricted_domains() -> None:
    """HIPAA pack should restrict to PHI-relevant domains."""
    assert HIPAA_PACK.enabled_domains is not None
    from electripy.ai.lsas.domain import RiskDomain

    assert RiskDomain.HIPAA_PHI in HIPAA_PACK.enabled_domains


def test_pci_pack_has_restricted_domains() -> None:
    """PCI pack should restrict to PCI domain."""
    assert PCI_PACK.enabled_domains is not None
    from electripy.ai.lsas.domain import RiskDomain

    assert RiskDomain.PCI in PCI_PACK.enabled_domains


def test_demo_pack_all_domains_enabled() -> None:
    """Demo pack should have all domains enabled (None means all)."""
    assert DEMO_PACK.enabled_domains is None


def test_hipaa_pack_has_tighter_thresholds_than_demo() -> None:
    """HIPAA thresholds should be tighter (lower) than demo defaults."""
    assert HIPAA_PACK.thresholds.warn < DEMO_PACK.thresholds.warn


def test_pci_pack_has_tighter_block_threshold() -> None:
    """PCI block threshold should be lower than demo."""
    assert PCI_PACK.thresholds.block < DEMO_PACK.thresholds.block
