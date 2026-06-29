"""Validator registry — maps stable IDs to validator instances.

Provides a single place to look up or enumerate all built-in LSAS validators,
and helpers to build the default validator set used by the built-in policy packs.
"""

from __future__ import annotations

from .base import ValidatorPort
from .pci import PciValidator
from .phi_pii import PhiPiiValidator
from .prompt_injection import PromptInjectionValidator
from .secrets import SecretsValidator

__all__ = [
    "ValidatorRegistry",
    "build_default_validators",
    "get_validator",
]

# Singleton instances of all built-in validators
_REGISTRY: dict[str, ValidatorPort] = {
    "phi_pii": PhiPiiValidator(),
    "pci": PciValidator(),
    "secrets": SecretsValidator(),
    "prompt_injection": PromptInjectionValidator(),
}


class ValidatorRegistry:
    """Read-only view over the built-in validator registry.

    Usage::

        registry = ValidatorRegistry()
        validators = registry.get_all()
        phi = registry.get("phi_pii")
    """

    def get(self, validator_id: str) -> ValidatorPort:
        """Return the validator for *validator_id*.

        Raises:
            KeyError: if no validator with *validator_id* is registered.
        """
        return _REGISTRY[validator_id]

    def get_all(self) -> list[ValidatorPort]:
        """Return all registered validators in stable registration order."""
        return list(_REGISTRY.values())

    def ids(self) -> list[str]:
        """Return the stable IDs of all registered validators."""
        return list(_REGISTRY.keys())


def get_validator(validator_id: str) -> ValidatorPort:
    """Module-level shortcut for :meth:`ValidatorRegistry.get`."""
    return _REGISTRY[validator_id]


def build_default_validators() -> list[ValidatorPort]:
    """Return the standard set of validators used by the built-in policy packs.

    The set includes PHI/PII, PCI, secrets, and prompt-injection validators.
    """
    return [
        PhiPiiValidator(),
        PciValidator(),
        SecretsValidator(),
        PromptInjectionValidator(),
    ]
