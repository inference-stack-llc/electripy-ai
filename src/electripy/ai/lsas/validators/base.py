"""Base interface (Protocol) for LSAS validators.

All validators implement :class:`ValidatorPort` so they can be composed and
swapped without subclassing.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..domain import Finding

__all__ = ["ValidatorPort"]


@runtime_checkable
class ValidatorPort(Protocol):
    """Structural interface every LSAS validator must satisfy.

    Implementations should be **stateless** and **deterministic**: given the
    same *text* they must always return the same sequence of findings.
    """

    #: Stable identifier used in :attr:`~.domain.Finding.validator_id`.
    validator_id: str

    def validate(self, text: str) -> list[Finding]:
        """Scan *text* and return zero or more :class:`~.domain.Finding` objects.

        Args:
            text: The content to scan (prompt, response, tool argument, …).

        Returns:
            A (possibly empty) list of findings, ordered by ``start`` offset
            when offset information is available.
        """
        ...  # pragma: no cover
