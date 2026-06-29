"""Cost screen — live CostLedger token tracking and cost breakdown."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, RichLog, Static

from electripy.ai.cost_ledger import CostLedger, LedgerTotal

from .._demo_data import COST_PER_1K, COST_SCENARIOS


class CostTab(Widget):
    """CostLedger live demo — accumulate, slice, and visualise token costs."""

    DEFAULT_CSS = """
    CostTab {
        height: 1fr;
        padding: 1 2;
    }
    CostTab .section-title {
        color: #fab387;
        text-style: bold;
        height: 2;
        padding: 0 0 0 1;
        content-align: left middle;
    }
    CostTab .btn-row {
        height: 4;
        margin-bottom: 1;
    }
    CostTab DataTable {
        height: 14;
        border: solid #313244;
        margin-bottom: 1;
    }
    CostTab .totals-box {
        background: #181825;
        border: solid #fab387;
        padding: 1 2;
        height: 4;
        margin-bottom: 1;
    }
    CostTab .sparkline-box {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        height: auto;
        margin-bottom: 1;
    }
    CostTab RichLog {
        height: 1fr;
        border: solid #313244;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        # One ledger per model
        self._ledgers: dict[str, CostLedger] = {
            model: CostLedger(cost_per_1k_tokens=cpm)
            for model, cpm in COST_PER_1K.items()
        }
        self._scenario_index = 0
        self._call_history: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Label("🟡  Cost Ledger — Token Cost Accumulation", classes="section-title")

        with Horizontal(classes="btn-row"):
            yield Button("Add Next Call",   id="btn-add",    variant="primary")
            yield Button("Add All Calls",   id="btn-add-all")
            yield Button("Reset",           id="btn-reset")

        cost_table: DataTable[str] = DataTable(id="cost-table", zebra_stripes=True)
        yield cost_table

        with Vertical(classes="totals-box"):
            yield Label("", id="totals-line")
            yield Label("", id="totals-line2")

        with Vertical(classes="sparkline-box"):
            yield Static("[bold #fab387]Token Accumulation[/bold #fab387]  [dim](per call)[/dim]")
            yield Label("", id="sparkline")

        yield RichLog(id="cost-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        t: DataTable[str] = self.query_one("#cost-table", DataTable)
        t.add_column("Model",      key="model",   width=18)
        t.add_column("Calls",      key="calls",   width=8)
        t.add_column("Tokens",     key="tokens",  width=12)
        t.add_column("Est. Cost",  key="cost",    width=12)
        t.add_column("Cost/1k",    key="rate",    width=10)
        t.add_column("Tenant",     key="tenant",  width=12)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _refresh_table(self) -> None:
        table = self.query_one("#cost-table", DataTable)
        table.clear()

        all_tokens = 0
        all_cost = 0.0
        all_calls = 0

        for model, ledger in self._ledgers.items():
            total: LedgerTotal = ledger.total()
            if total.call_count == 0:
                continue
            by_tenant = ledger.by_label("tenant")
            tenant_str = ", ".join(
                f"{k}({v.call_count})" for k, v in sorted(by_tenant.items())
            )
            rate = COST_PER_1K.get(model, 0.0)
            table.add_row(
                f"[bold]{model}[/bold]",
                str(total.call_count),
                f"{total.tokens:,}",
                f"[yellow]${total.estimated_cost:.4f}[/yellow]",
                f"${rate:.4f}",
                tenant_str or "—",
            )
            all_tokens += total.tokens
            all_cost += total.estimated_cost
            all_calls += total.call_count

        # Totals
        self.query_one("#totals-line", Label).update(
            f"  [bold]TOTAL[/bold]  |  "
            f"Calls: [bold]{all_calls}[/bold]  |  "
            f"Tokens: [bold]{all_tokens:,}[/bold]  |  "
            f"Estimated Cost: [bold yellow]${all_cost:.4f}[/bold yellow]"
        )
        self.query_one("#totals-line2", Label).update(
            f"  Ledger slices by: [dim]model, tenant, feature[/dim]  |  "
            f"Thread-safe accumulation  |  No external services"
        )

        # Sparkline — ASCII bar chart of tokens per call in history
        if self._call_history:
            bar_chars = "▁▂▃▄▅▆▇█"
            max_tok = max(c["tokens"] for c in self._call_history)
            bars = ""
            for call in self._call_history[-40:]:
                idx = min(
                    int((call["tokens"] / max_tok) * (len(bar_chars) - 1)),
                    len(bar_chars) - 1,
                )
                bars += f"[yellow]{bar_chars[idx]}[/yellow]"
            self.query_one("#sparkline", Label).update(
                f"  {bars}  [dim]{len(self._call_history)} calls[/dim]"
            )

    def _add_call(self, scenario: dict) -> None:
        model = scenario["model"]
        tokens = scenario["tokens"]
        labels = scenario["labels"]

        if model not in self._ledgers:
            self._ledgers[model] = CostLedger(
                cost_per_1k_tokens=COST_PER_1K.get(model, 0.0)
            )

        self._ledgers[model].record(tokens=tokens, labels=labels)
        self._call_history.append(scenario)

        cost = tokens / 1000.0 * COST_PER_1K.get(model, 0.0)
        log = self.query_one("#cost-log", RichLog)
        log.write(
            f"[#fab387]⬡ RECORD[/#fab387]  [bold]{model}[/bold]  "
            f"{tokens:,} tokens  →  [yellow]${cost:.4f}[/yellow]  "
            f"|  tenant=[dim]{labels.get('tenant', '?')}[/dim]  "
            f"feature=[dim]{labels.get('feature', '?')}[/dim]"
        )
        self._refresh_table()

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    @on(Button.Pressed, "#btn-add")
    def _add_next(self, _event: Button.Pressed) -> None:
        if self._scenario_index < len(COST_SCENARIOS):
            self._add_call(COST_SCENARIOS[self._scenario_index])
            self._scenario_index += 1
        else:
            log = self.query_one("#cost-log", RichLog)
            log.write("[dim]All scenarios added. Click Reset to start over.[/dim]")

    @on(Button.Pressed, "#btn-add-all")
    def _add_all(self, _event: Button.Pressed) -> None:
        remaining = COST_SCENARIOS[self._scenario_index:]
        for scenario in remaining:
            self._add_call(scenario)
        self._scenario_index = len(COST_SCENARIOS)

    @on(Button.Pressed, "#btn-reset")
    def _reset(self, _event: Button.Pressed) -> None:
        self._ledgers = {
            model: CostLedger(cost_per_1k_tokens=cpm)
            for model, cpm in COST_PER_1K.items()
        }
        self._scenario_index = 0
        self._call_history.clear()
        self.query_one("#cost-table", DataTable).clear()
        self.query_one("#totals-line", Label).update("")
        self.query_one("#totals-line2", Label).update("")
        self.query_one("#sparkline", Label).update("")
        log = self.query_one("#cost-log", RichLog)
        log.write("[cyan]↺ RESET[/cyan]  —  all ledgers cleared")
