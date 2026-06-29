"""ElectriPy AI Interactive Playground.

An interactive Textual TUI that demonstrates every major ElectriPy AI
capability domain using real production components — no mocks.

Launch with::

    electripy playground

Or from Python::

    from electripy.playground import run
    run()

Requires the ``playground`` optional dependency group::

    pip install electripy-ai[playground]
"""

from __future__ import annotations


def run() -> None:
    """Launch the ElectriPy AI Playground (requires textual)."""
    from .app import run as _run  # noqa: PLC0415  # lazy — textual is optional

    _run()


__all__ = ["run"]
