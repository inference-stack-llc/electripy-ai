"""Home screen — LSAS Architecture overview and capability map."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Static

_LSAS_PANEL = """\
[bold #cba6f7]╔══════════════════════════════════════════════════════════════╗
║      LSAS — Layered Safety and Accuracy System for AI Systems       ║
╠══════════════════════════════════════════════════════════════╣
║  [dim]L09  Application       Business logic, UX, product surface   [/dim] ║
║  [#89b4fa]L08  Orchestration     Agent routing, session flow, handoffs [/]║
║  [#89b4fa]L07  Memory            Conversation history, context mgmt    [/]║
║  [#89b4fa]L06  Knowledge         Retrieval, RAG, embeddings            [/]║
║  [#89b4fa]L05  Tool Integration  MCP, skills, function calls           [/]║
╠══════════════════════════════════════════════════════════════╣
║  [#fab387]L04  Model Runtime     LLM gateway, provider adapters        [/]║
║  [#f38ba8]L03  Reliability       Circuit breakers, retries, fallback   [/]║
║  [#89dceb]L02  Observability     Traces, spans, OTEL, cost, redaction  [/]║
║  [#cba6f7]L01  Governance        Policy engine, approvals, audit trails[/]║
╚══════════════════════════════════════════════════════════════╝[/bold #cba6f7]"""

_IMPL_NOTE = (
    "[dim]ElectriPy AI implements [bold]L01 – L06[/bold] as composable "
    "runtime primitives. Import the layers you need — leave the rest.[/dim]"
)

_CAPABILITY_MAP = """\
[bold]Runtime Domains implemented in this build:[/bold]

  [#f38ba8]⬡  Reliability[/]      CircuitBreaker · Retry · FallbackChain · RateLimiter
  [#89dceb]⬡  Observability[/]    ObservabilityService · InMemoryTracer · DefaultRedactor
  [#cba6f7]⬡  Governance[/]       PolicyGateway · PolicyEngine · AuditTrails
  [#a6e3a1]⬡  Evaluation[/]       EvalAssertions · Evals · RAGEvalRunner
  [#fab387]⬡  Model Runtime[/]    LLMGateway · StructuredOutput · LLMCache · ReplayTape
  [#89b4fa]⬡  Orchestration[/]    Realtime · AgentCollaboration · MCP · Skills

[dim]Select a tab above to explore each domain with live interactive demos.[/dim]"""

_STATS = (
    "[bold]v0.5.0[/bold]  ·  "
    "[bold]1 000+[/bold] offline tests  ·  "
    "[bold]9[/bold] LSAS layers  ·  "
    "[bold]MIT[/bold] licensed  ·  "
    "Python [bold]3.11+[/bold]"
)


class HomeTab(Widget):
    """Home tab — LSAS overview and capability map."""

    DEFAULT_CSS = """
    HomeTab {
        height: 1fr;
        padding: 1 3;
        overflow-y: auto;
    }
    HomeTab .hero-title {
        text-align: center;
        text-style: bold;
        color: #cba6f7;
        height: 3;
        content-align: center middle;
        margin-bottom: 1;
    }
    HomeTab .lsas-panel {
        margin: 0 0 1 0;
    }
    HomeTab .impl-note {
        margin: 0 0 1 2;
    }
    HomeTab .capability-map {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        margin: 0 0 1 0;
    }
    HomeTab .stats-bar {
        text-align: center;
        color: #6c7086;
        height: 2;
        content-align: center middle;
        border-top: solid #313244;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(
            "⚡  ElectriPy AI — Open Source AI Application Runtime",
            classes="hero-title",
        )
        yield Static(_LSAS_PANEL, classes="lsas-panel")
        yield Static(_IMPL_NOTE, classes="impl-note")
        yield Static(_CAPABILITY_MAP, classes="capability-map")
        yield Label(_STATS, classes="stats-bar")
