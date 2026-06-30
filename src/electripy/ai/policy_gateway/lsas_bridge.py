"""Optional bridge between :mod:`~electripy.ai.policy_gateway` and the LSAS
scoring runtime.

This module is **additive and opt-in**.  It does not change
:class:`~electripy.ai.policy_gateway.PolicyGateway`'s existing default
behavior or public types.

Usage::

    from electripy.ai.lsas.bridge import run_lsas_for_policy_input

    lsas_result = run_lsas_for_policy_input(
        text="alice@example.com",
        pack=DEMO_PACK,
    )
    print(lsas_result.decision)
"""

from __future__ import annotations

from ..lsas.domain import LsasAuditMetadata, LsasResult
from ..lsas.engine import run_decision_engine
from ..lsas.policy import PolicyPack
from ..lsas.policy_packs import DEMO_PACK
from ..lsas.validators import ValidatorPort, build_default_validators
from .domain import PolicyContext

__all__ = ["run_lsas_for_policy_input"]


def run_lsas_for_policy_input(
    text: str,
    *,
    pack: PolicyPack = DEMO_PACK,
    validators: list[ValidatorPort] | None = None,
    context: PolicyContext | None = None,
) -> LsasResult:
    """Run the LSAS scoring pipeline for a piece of policy-gateway text.

    This is the optional bridge that allows
    :class:`~electripy.ai.policy_gateway.PolicyGateway` callers to obtain a
    rich :class:`~electripy.ai.lsas.LsasResult` (with risk tier, domain scores,
    and decision) alongside the standard
    :class:`~electripy.ai.policy_gateway.PolicyDecision`.

    It **does not** modify :class:`~electripy.ai.policy_gateway.PolicyGateway`
    and **does not** affect its existing decisions.

    Args:
        text: The content to evaluate (prompt, response, …).
        pack: The :class:`~electripy.ai.lsas.PolicyPack` to use.  Defaults
            to the built-in ``DEMO_PACK``.
        validators: List of validators to run.  Defaults to the built-in set
            (PHI/PII, PCI, secrets, prompt-injection).
        context: Optional :class:`~electripy.ai.policy_gateway.PolicyContext`
            used to populate audit metadata.

    Returns:
        A frozen :class:`~electripy.ai.lsas.LsasResult`.
    """
    effective_validators: list[ValidatorPort] = (
        validators if validators is not None else build_default_validators()
    )

    audit: LsasAuditMetadata | None = None
    if context is not None:
        audit = LsasAuditMetadata(
            request_id=context.request_id,
            actor_id=context.actor_id,
            tenant_id=context.tenant_id,
        )

    return run_decision_engine(
        text=text,
        validators=effective_validators,
        pack=pack,
        audit=audit,
    )
