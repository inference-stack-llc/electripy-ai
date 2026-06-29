"""Observability screen — live spans, trace tree, and PII redaction demo."""

from __future__ import annotations

import time

from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Label, RichLog, Static

from electripy.ai.policy_gateway import (
    PolicyAction,
    PolicyGateway,
    PolicyRule,
    PolicySeverity,
    PolicyStage,
)
from electripy.observability.observe import (
    DefaultRedactor,
    InMemoryTracer,
    ObservabilityService,
    SpanKind,
)

from .._demo_data import OBSERVE_PROMPT_CLEAN, OBSERVE_PROMPT_PII

# Inline PII gateway used only for the redaction preview panel
_PREVIEW_RULES = [
    PolicyRule(
        rule_id="pii-email",
        code="PII_EMAIL",
        description="Mask email addresses",
        stage=PolicyStage.PREFLIGHT,
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        severity=PolicySeverity.MEDIUM,
        action=PolicyAction.SANITIZE,
        replacement="[EMAIL REDACTED]",
    ),
    PolicyRule(
        rule_id="pii-name",
        code="PII_NAME",
        description="Flag potential personal names (DOB pattern)",
        stage=PolicyStage.PREFLIGHT,
        pattern=r"\b\d{4}-\d{2}-\d{2}\b",
        severity=PolicySeverity.MEDIUM,
        action=PolicyAction.SANITIZE,
        replacement="[DATE REDACTED]",
    ),
]
_preview_gateway = PolicyGateway(rules=_PREVIEW_RULES)


class ObservabilityTab(Widget):
    """Live span tree and PII-redaction demo using real ObservabilityService."""

    DEFAULT_CSS = """
    ObservabilityTab {
        height: 1fr;
        padding: 1 2;
    }
    ObservabilityTab .section-title {
        color: #89dceb;
        text-style: bold;
        height: 2;
        padding: 0 0 0 1;
        content-align: left middle;
    }
    ObservabilityTab .prompt-row {
        height: 5;
        margin-bottom: 1;
    }
    ObservabilityTab Input {
        width: 1fr;
        margin-right: 1;
    }
    ObservabilityTab .btn-col {
        width: 26;
    }
    ObservabilityTab DataTable {
        height: 14;
        border: solid #313244;
        margin-bottom: 1;
    }
    ObservabilityTab .redact-box {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        height: auto;
        margin-bottom: 1;
    }
    ObservabilityTab RichLog {
        height: 1fr;
        border: solid #313244;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._tracer = InMemoryTracer(redactor=DefaultRedactor())
        self._svc = ObservabilityService(tracer=self._tracer)

    def compose(self) -> ComposeResult:
        yield Label("🔵  Observability — Span Tree & PII Redaction", classes="section-title")

        with Horizontal(classes="prompt-row"):
            yield Input(
                value=OBSERVE_PROMPT_PII,
                placeholder="Enter a prompt (try one with PII)…",
                id="obs-prompt",
            )
            with Vertical(classes="btn-col"):
                yield Button("Run Workflow", id="btn-workflow", variant="primary")
                yield Button("Load PII sample", id="btn-pii-sample")
                yield Button("Load clean sample", id="btn-clean-sample")

        # Span tree table
        table: DataTable[str] = DataTable(id="span-table", zebra_stripes=True)
        yield table

        # Redaction preview
        with Vertical(classes="redact-box"):
            yield Static(
                "[bold #89dceb]PII Redaction Preview[/bold #89dceb]  "
                "[dim](DefaultRedactor — redacts email, phone, SSN, credit card)[/dim]"
            )
            yield Label("", id="redact-before")
            yield Label("", id="redact-after")

        yield RichLog(id="obs-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#span-table", DataTable)
        table.add_column("Span Name",   key="name",     width=30)
        table.add_column("Kind",        key="kind",     width=12)
        table.add_column("Duration",    key="dur",      width=10)
        table.add_column("Status",      key="status",   width=8)
        table.add_column("Key Attribute", key="attr",   width=40)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _run_spans(self, prompt: str) -> None:
        log = self.query_one("#obs-log", RichLog)
        table = self.query_one("#span-table", DataTable)

        # Clear previous spans from the in-memory tracer
        self._tracer.finished_spans.clear()
        table.clear()

        t0 = time.monotonic()

        # Workflow span wraps everything
        with self._svc.start_workflow_span("ai.workflow.summarise") as wf_span:
            wf_span.set_attribute("workflow.prompt_length", len(prompt))

            # Nested: policy check span
            with self._svc.start_span("policy.preflight", kind=SpanKind.POLICY) as pol_span:
                pol_span.set_attribute("policy.rules_evaluated", 3)
                pol_span.set_attribute("policy.action", "allow")
                time.sleep(0.002)

            # Nested: LLM call span
            with self._svc.start_llm_span(provider="openai", model="gpt-4o") as llm_span:
                llm_span.set_attribute("gen_ai.usage.input_tokens", len(prompt.split()))
                llm_span.set_attribute("gen_ai.usage.output_tokens", 42)
                llm_span.set_attribute("gen_ai.request.model", "gpt-4o")
                time.sleep(0.008)

            # Nested: tool call span
            with self._svc.start_tool_span("retrieval.context_fetch") as tool_span:
                tool_span.set_attribute("tool.name", "retrieval.context_fetch")
                tool_span.set_attribute("retrieval.docs_fetched", 5)
                time.sleep(0.003)

        elapsed_ms = (time.monotonic() - t0) * 1000

        # Populate table with finished spans
        for record in self._tracer.finished_spans:
            dur_ms = (
                (record.end_time - record.start_time).total_seconds() * 1000
                if record.end_time
                else 0
            )
            key_attr = ""
            for k, v in record.attributes.items():
                if not k.startswith("observe."):
                    key_attr = f"{k}={v}"
                    break

            status_code = record.status.code.value if record.status else "ok"

            kind_colors = {
                "workflow": "cyan",
                "llm": "blue",
                "policy": "magenta",
                "tool": "yellow",
                "agent": "green",
                "internal": "white",
            }
            kind_str = str(record.kind.value).lower()
            color = kind_colors.get(kind_str, "white")

            table.add_row(
                f"  {record.name}",
                f"[{color}]{kind_str}[/{color}]",
                f"{dur_ms:.1f}ms",
                status_code,
                key_attr[:38],
            )

        log.write(
            f"[cyan]◎ TRACED[/cyan]  —  {len(self._tracer.finished_spans)} spans in "
            f"[bold]{elapsed_ms:.1f}ms[/bold]  |  "
            f"tracer: [dim]InMemoryTracer + DefaultRedactor[/dim]"
        )

        # Show inline PII redaction preview using PolicyGateway sanitize
        decision = _preview_gateway.evaluate_preflight(prompt)
        sanitized = decision.sanitized_text or prompt
        before_lbl = self.query_one("#redact-before", Label)
        after_lbl = self.query_one("#redact-after", Label)
        before_lbl.update(f"[dim]Before:[/dim]  {escape(prompt[:120])}")
        after_lbl.update(f"[bold]After: [/bold]  [green]{escape(sanitized[:120])}[/green]")

        if sanitized != prompt:
            log.write("[green]✓ REDACTION[/green]  —  PII detected and masked before span export")
        else:
            log.write("[dim]· No PII patterns matched in this prompt[/dim]")

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    @on(Button.Pressed, "#btn-workflow")
    def _run_workflow(self, _event: Button.Pressed) -> None:
        prompt = self.query_one("#obs-prompt", Input).value
        self._run_spans(prompt)

    @on(Button.Pressed, "#btn-pii-sample")
    def _load_pii(self, _event: Button.Pressed) -> None:
        self.query_one("#obs-prompt", Input).value = OBSERVE_PROMPT_PII

    @on(Button.Pressed, "#btn-clean-sample")
    def _load_clean(self, _event: Button.Pressed) -> None:
        self.query_one("#obs-prompt", Input).value = OBSERVE_PROMPT_CLEAN
