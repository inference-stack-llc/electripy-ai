"""LSAS policy packs sub-package.

Public surface::

    from electripy.ai.lsas.policy_packs import DEMO_PACK, HIPAA_PACK, PCI_PACK
    from electripy.ai.lsas.policy_packs import get_pack, list_packs
"""

from __future__ import annotations

from ..policy import PolicyPack
from .demo import DEMO_PACK
from .hipaa import HIPAA_PACK
from .pci import PCI_PACK

__all__ = [
    "DEMO_PACK",
    "HIPAA_PACK",
    "PCI_PACK",
    "get_pack",
    "list_packs",
]

_REGISTRY: dict[str, PolicyPack] = {
    DEMO_PACK.pack_id: DEMO_PACK,
    HIPAA_PACK.pack_id: HIPAA_PACK,
    PCI_PACK.pack_id: PCI_PACK,
}


def get_pack(pack_id: str) -> PolicyPack:
    """Return the built-in :class:`~.policy.PolicyPack` with *pack_id*.

    Args:
        pack_id: One of ``"demo"``, ``"hipaa"``, or ``"pci"``.

    Raises:
        KeyError: If no pack with *pack_id* is registered.
    """
    return _REGISTRY[pack_id]


def list_packs() -> list[PolicyPack]:
    """Return all registered policy packs in stable registration order."""
    return list(_REGISTRY.values())
