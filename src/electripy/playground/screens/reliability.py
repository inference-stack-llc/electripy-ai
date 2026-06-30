"""Reliability screen — live CircuitBreaker, Retry, and FallbackChain demo."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, RichLog, Static

from electripy.concurrency.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
)
from electripy.concurrency.retry import retry
from electripy.core.errors import RetryError


def _provider_fail() -> str:
    raise ConnectionError("Provider timeout: connection refused (simulated)")


def _provider_ok() -> str:
    return "Provider response: {'choices': [{'text': 'The capital of France is Paris.'}]}"


class ReliabilityTab(Widget):
    """Interactive circuit breaker state machine demo."""

    DEFAULT_CSS = """
    ReliabilityTab {
        height: 1fr;
        padding: 1 2;
    }
    ReliabilityTab .section-title {
        color: #f38ba8;
        text-style: bold;
        height: 2;
        padding: 0 0 0 1;
        content-align: left middle;
    }
    ReliabilityTab .state-row {
        height: 5;
        margin: 0 0 1 0;
        align: center middle;
    }
    ReliabilityTab .state-box {
        width: 20;
        height: 5;
        content-align: center middle;
        text-style: bold;
        border: solid #313244;
        color: #6c7086;
    }
    ReliabilityTab .state-active-closed {
        background: #1a3327;
        color: #a6e3a1;
        border: solid #a6e3a1;
    }
    ReliabilityTab .state-active-open {
        background: #3b1219;
        color: #f38ba8;
        border: solid #f38ba8;
    }
    ReliabilityTab .state-active-half-open {
        background: #2e2419;
        color: #f9e2af;
        border: solid #f9e2af;
    }
    ReliabilityTab .arrow {
        width: 5;
        content-align: center middle;
        color: #585b70;
    }
    ReliabilityTab .status-line {
        height: 2;
        color: #a6a8b4;
        padding: 0 1;
        content-align: left middle;
    }
    ReliabilityTab .btn-row {
        height: 4;
        margin: 0 0 1 0;
    }
    ReliabilityTab .retry-section {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        margin-top: 1;
        height: auto;
    }
    ReliabilityTab RichLog {
        height: 1fr;
        border: solid #313244;
        margin-top: 1;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            success_threshold=1,
        )
        self._call_count = 0
        self._trip_count = 0

    def compose(self) -> ComposeResult:
        yield Label("🔴  Reliability — Circuit Breaker Live Demo", classes="section-title")

        # State machine visualisation
        with Horizontal(classes="state-row"):
            yield Static(
                "CLOSED\n\n✓ Calls pass through",
                id="box-closed",
                classes="state-box state-active-closed",
            )
            yield Static("───▶", classes="arrow")
            yield Static("OPEN\n\n⚡ Fast-fail, no calls", id="box-open", classes="state-box")
            yield Static("───▶", classes="arrow")
            yield Static("HALF-OPEN\n\nProbe allowed", id="box-half", classes="state-box")
            yield Static(" ◀──\n back on success", classes="arrow")

        yield Label(self._status_text(), id="cb-status", classes="status-line")

        # Controls
        with Horizontal(classes="btn-row"):
            yield Button("Inject Failure", id="btn-fail", variant="error")
            yield Button("Successful Call", id="btn-success", variant="success")
            yield Button("Reset", id="btn-reset")
            yield Button("Retry (3× backoff)", id="btn-retry")

        # Retry demo note
        with Vertical(classes="retry-section"):
            yield Static(
                "[dim]Retry demo: calls [bold]retry(max_attempts=3, delay=0.05)[/bold] "
                "with exponential backoff. Watch failures accumulate, then circuit trips.[/dim]"
            )

        yield RichLog(id="cb-log", highlight=True, markup=True)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _status_text(self) -> str:
        state = self._breaker.state
        color = {
            CircuitState.CLOSED: "#a6e3a1",
            CircuitState.OPEN: "#f38ba8",
            CircuitState.HALF_OPEN: "#f9e2af",
        }.get(state, "#cdd6f4")
        return (
            f"  State: [{color}]{state.upper()}[/]  |  "
            f"Failures: [bold]{self._breaker.failure_count}[/bold]/3  |  "
            f"Recovery timeout: 5.0s  |  "
            f"Total calls: {self._call_count}  |  Trips: {self._trip_count}"
        )

    def _update_display(self) -> None:
        state = self._breaker.state

        # Status label
        self.query_one("#cb-status", Label).update(self._status_text())

        # State boxes — reset all, highlight current
        closed = self.query_one("#box-closed", Static)
        open_box = self.query_one("#box-open", Static)
        half_box = self.query_one("#box-half", Static)

        for box in (closed, open_box, half_box):
            box.remove_class("state-active-closed", "state-active-open", "state-active-half-open")

        if state == CircuitState.CLOSED:
            closed.add_class("state-active-closed")
        elif state == CircuitState.OPEN:
            open_box.add_class("state-active-open")
        else:
            half_box.add_class("state-active-half-open")

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    @on(Button.Pressed, "#btn-fail")
    def _inject_failure(self, _event: Button.Pressed) -> None:
        log = self.query_one("#cb-log", RichLog)
        self._call_count += 1
        prev_state = self._breaker.state
        try:
            self._breaker.call(_provider_fail)
        except CircuitOpenError:
            log.write(
                "[yellow]⚡ FAST FAIL[/yellow]  —  circuit is [bold]OPEN[/bold], "
                "provider call skipped entirely"
            )
        except ConnectionError as e:
            if prev_state != CircuitState.OPEN and self._breaker.state == CircuitState.OPEN:
                self._trip_count += 1
                log.write(
                    f"[red]✗ TRIPPED[/red]  failure {self._breaker.failure_count}/3 → "
                    f"[bold red]circuit OPENED[/bold red]  (recovery in 5s)"
                )
            else:
                log.write(
                    f"[red]✗ FAILURE[/red]  {self._breaker.failure_count}/3 consecutive  —  {e}"
                )
        self._update_display()

    @on(Button.Pressed, "#btn-success")
    def _success_call(self, _event: Button.Pressed) -> None:
        log = self.query_one("#cb-log", RichLog)
        self._call_count += 1
        prev_state = self._breaker.state
        try:
            result = self._breaker.call(_provider_ok)
            if prev_state == CircuitState.HALF_OPEN:
                log.write(
                    "[green]✓ RECOVERED[/green]  probe succeeded → "
                    "[bold green]circuit CLOSED[/bold green]"
                )
            else:
                log.write(f"[green]✓ SUCCESS[/green]  —  {result[:60]}…")
        except CircuitOpenError:
            log.write(
                "[yellow]⚡ FAST FAIL[/yellow]  —  circuit still [bold]OPEN[/bold]  "
                "(check recovery timer)"
            )
        self._update_display()

    @on(Button.Pressed, "#btn-reset")
    def _reset(self, _event: Button.Pressed) -> None:
        log = self.query_one("#cb-log", RichLog)
        self._breaker.reset()
        self._call_count = 0
        self._trip_count = 0
        log.write("[cyan]↺ RESET[/cyan]  —  circuit restored to [bold]CLOSED[/bold] state")
        self._update_display()

    @on(Button.Pressed, "#btn-retry")
    def _retry_demo(self, _event: Button.Pressed) -> None:
        log = self.query_one("#cb-log", RichLog)

        attempt_log: list[str] = []

        @retry(max_attempts=3, delay=0.05, backoff=2.0, exceptions=(ConnectionError,))
        def _retried_call() -> str:
            attempt_log.append("attempt")
            return self._breaker.call(_provider_fail)

        self._call_count += 1
        try:
            _retried_call()
        except (RetryError, CircuitOpenError) as exc:
            attempts = len(attempt_log)
            log.write(
                f"[orange1]↻ RETRY[/orange1]  —  {attempts} attempt(s) exhausted  →  "
                f"[red]{type(exc).__name__}[/red]  (circuit failures: {self._breaker.failure_count}/3)"
            )
        except ConnectionError:
            # Retry exhausted but caught by circuit breaker first
            pass
        self._update_display()
