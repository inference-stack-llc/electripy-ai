"""Evaluation screen — live EvalAssertions quality gate demo."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, RichLog, Static, TextArea

from electripy.ai.eval_assertions import (
    AssertionCheck,
    assert_llm_output,
    contains_keywords,
    matches_regex,
    passes_predicate,
    satisfies_length,
)

from .._demo_data import EVAL_SAMPLES

# ---------------------------------------------------------------------------
# Assertion suite for "France capital" outputs
# ---------------------------------------------------------------------------


def _build_checks() -> list[AssertionCheck]:
    return [
        contains_keywords(["Paris", "capital"], case_sensitive=False),
        matches_regex(r"\bParis\b"),
        satisfies_length(min_length=20),
        passes_predicate(
            predicate=lambda s: "no capital" not in s.lower() and "no designated" not in s.lower(),
            name="no_hallucination",
            description='must not claim France has "no capital"',
        ),
    ]


class EvaluationTab(Widget):
    """Eval assertions live demo — run quality gates against LLM outputs."""

    DEFAULT_CSS = """
    EvaluationTab {
        height: 1fr;
        padding: 1 2;
    }
    EvaluationTab .section-title {
        color: #a6e3a1;
        text-style: bold;
        height: 2;
        padding: 0 0 0 1;
        content-align: left middle;
    }
    EvaluationTab .checks-box {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        height: 10;
        width: 42;
        margin-right: 2;
    }
    EvaluationTab .input-col {
        width: 1fr;
    }
    EvaluationTab TextArea {
        height: 7;
        margin-bottom: 1;
    }
    EvaluationTab .btn-row {
        height: 3;
        margin-bottom: 1;
    }
    EvaluationTab DataTable {
        height: 10;
        border: solid #313244;
        margin-bottom: 1;
    }
    EvaluationTab .summary-box {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        height: 3;
        margin-bottom: 1;
        content-align: left middle;
    }
    EvaluationTab RichLog {
        height: 1fr;
        border: solid #313244;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._sample_index = 0

    def compose(self) -> ComposeResult:
        yield Label("🟢  Evaluation — Assertion Quality Gates", classes="section-title")

        with Horizontal():
            # Checks panel
            with Vertical(classes="checks-box"):
                yield Static("[bold #a6e3a1]Assertion Suite[/bold #a6e3a1]  [dim](4 checks)[/dim]")
                checks = _build_checks()
                for check in checks:
                    yield Static(f"  [dim]►[/dim] [bold]{check.name}[/bold]")
                    yield Static(f"     [dim]{check.description}[/dim]")

            # Input column
            with Vertical(classes="input-col"):
                yield TextArea(
                    EVAL_SAMPLES[0]["output"],
                    id="eval-output",
                    show_line_numbers=False,
                )
                with Horizontal(classes="btn-row"):
                    yield Button("Run Assertions", id="btn-run", variant="primary")
                    yield Button("Next Sample ▶", id="btn-next")
                    yield Button("Sample: —", id="btn-sample-label", disabled=True)

        results_table: DataTable[str] = DataTable(id="results-table", zebra_stripes=True)
        yield results_table

        with Horizontal(classes="summary-box"):
            yield Label("", id="eval-summary")

        yield RichLog(id="eval-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        t: DataTable[str] = self.query_one("#results-table", DataTable)
        t.add_column("Check", key="name", width=22)
        t.add_column("Result", key="result", width=10)
        t.add_column("Severity", key="sev", width=10)
        t.add_column("Description", key="desc", width=60)
        self._refresh_sample_label()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _refresh_sample_label(self) -> None:
        label = EVAL_SAMPLES[self._sample_index]["label"]
        self.query_one("#btn-sample-label", Button).label = f"Sample: {label}"

    def _run_assertions(self, output: str) -> None:
        log = self.query_one("#eval-log", RichLog)
        table = self.query_one("#results-table", DataTable)
        table.clear()

        checks = _build_checks()
        passed_count = 0
        failed_count = 0

        for check in checks:
            passed = check.check_fn(output)
            if passed:
                passed_count += 1
                badge = "[bold green]✓ PASS[/bold green]"
                desc_color = "dim"
            else:
                failed_count += 1
                badge = "[bold red]✗ FAIL[/bold red]"
                desc_color = "red"

            table.add_row(
                f"[bold]{check.name}[/bold]",
                badge,
                check.severity.value.upper(),
                f"[{desc_color}]{check.description}[/{desc_color}]",
            )

        # Summary
        total = len(checks)
        if failed_count == 0:
            summary_color = "green"
            summary_icon = "✓"
            summary_verdict = "ALL CHECKS PASSED"
        else:
            summary_color = "red"
            summary_icon = "✗"
            summary_verdict = f"{failed_count}/{total} CHECKS FAILED"

        self.query_one("#eval-summary", Label).update(
            f"  [{summary_color}]{summary_icon}[/{summary_color}]  "
            f"[bold {summary_color}]{summary_verdict}[/bold {summary_color}]  "
            f"|  {passed_count} passed · {failed_count} failed  "
            f"|  output length: {len(output)} chars"
        )

        log.write(
            f"[#a6e3a1]⬡ EVAL[/#a6e3a1]  {passed_count}/{total} checks passed  "
            f"|  [{'green' if failed_count == 0 else 'red'}]{summary_verdict}[/]"
        )

        # Also demonstrate assert_llm_output raising on failure
        if failed_count > 0:
            try:
                assert_llm_output(output, checks=checks)
            except AssertionError as e:
                log.write(
                    f"[dim]AssertionError raised (pytest-compatible):\n"
                    f"  {str(e).splitlines()[0]}[/dim]"
                )

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    @on(Button.Pressed, "#btn-run")
    def _run(self, _event: Button.Pressed) -> None:
        output = self.query_one("#eval-output", TextArea).text
        self._run_assertions(output)

    @on(Button.Pressed, "#btn-next")
    def _next_sample(self, _event: Button.Pressed) -> None:
        self._sample_index = (self._sample_index + 1) % len(EVAL_SAMPLES)
        sample = EVAL_SAMPLES[self._sample_index]
        self.query_one("#eval-output", TextArea).load_text(sample["output"])
        self._refresh_sample_label()
        log = self.query_one("#eval-log", RichLog)
        log.write(f"[dim]Loaded: {sample['label']}[/dim]")
