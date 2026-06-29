"""ElectriPy AI Playground — main Textual application.

Each tab exercises a real ElectriPy AI component with zero mocks and
zero network calls.  All demos are fully offline and deterministic.

Tabs:
    Home           LSAS Architecture overview
    Reliability    CircuitBreaker · Retry · FallbackChain live demo
    Observability  ObservabilityService · span tree · PII redaction
    Governance     PolicyGateway · PREFLIGHT / POSTFLIGHT enforcement
    Evaluation     EvalAssertions · quality gates · CI simulation
    Cost Ledger    CostLedger · token tracking · multi-label slicing
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, TabbedContent, TabPane

from .screens.cost import CostTab
from .screens.evaluation import EvaluationTab
from .screens.governance import GovernanceTab
from .screens.home import HomeTab
from .screens.observability import ObservabilityTab
from .screens.reliability import ReliabilityTab


class PlaygroundApp(App):
    """ElectriPy AI Interactive Playground."""

    TITLE = "⚡ ElectriPy AI Playground"
    SUB_TITLE = "v0.5.0 — Open Source AI Application Runtime — fully offline"

    BINDINGS = [
        ("1", "switch_tab('home')",          "Home"),
        ("2", "switch_tab('reliability')",   "Reliability"),
        ("3", "switch_tab('observability')", "Observability"),
        ("4", "switch_tab('governance')",    "Governance"),
        ("5", "switch_tab('evaluation')",    "Evaluation"),
        ("6", "switch_tab('cost')",          "Cost"),
        ("q", "quit",                        "Quit"),
    ]

    CSS = """
    Screen {
        background: #1e1e2e;
        color: #cdd6f4;
    }

    Header {
        background: #181825;
        color: #cba6f7;
    }

    Footer {
        background: #181825;
        color: #6c7086;
    }

    TabbedContent {
        height: 1fr;
    }

    TabbedContent ContentSwitcher {
        height: 1fr;
    }

    TabPane {
        height: 1fr;
        padding: 0;
    }

    /* Shared layout helpers */
    Button {
        margin: 0 1 0 0;
    }

    DataTable {
        background: #1e1e2e;
    }

    DataTable > .datatable--header {
        background: #181825;
        color: #cba6f7;
        text-style: bold;
    }

    DataTable > .datatable--odd-row {
        background: #1e1e2e;
    }

    DataTable > .datatable--even-row {
        background: #181825;
    }

    TextArea {
        background: #181825;
        color: #cdd6f4;
        border: solid #313244;
    }

    Input {
        background: #181825;
        color: #cdd6f4;
        border: solid #313244;
    }

    RichLog {
        background: #11111b;
        color: #cdd6f4;
    }

    Static {
        color: #cdd6f4;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="home"):
            with TabPane("⚡ Home",           id="home"):
                yield HomeTab()
            with TabPane("🔴 Reliability",    id="reliability"):
                yield ReliabilityTab()
            with TabPane("🔵 Observability",  id="observability"):
                yield ObservabilityTab()
            with TabPane("🟣 Governance",     id="governance"):
                yield GovernanceTab()
            with TabPane("🟢 Evaluation",     id="evaluation"):
                yield EvaluationTab()
            with TabPane("🟡 Cost Ledger",    id="cost"):
                yield CostTab()
        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a named tab via keyboard shortcut."""
        self.query_one(TabbedContent).active = tab_id


def run() -> None:
    """Launch the ElectriPy AI Playground."""
    try:
        PlaygroundApp().run()
    except ImportError as exc:
        import sys
        print(
            f"\n[ERROR] Playground requires the 'textual' package:\n"
            f"  pip install 'electripy-ai[playground]'\n\n"
            f"  (missing: {exc})\n",
            file=sys.stderr,
        )
        sys.exit(1)
