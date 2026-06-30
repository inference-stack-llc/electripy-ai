"""Governance screen — live PolicyGateway evaluation demo."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, RichLog, Static, TextArea

from electripy.ai.policy_gateway import (
    PolicyAction,
    PolicyDecision,
    PolicyGateway,
    PolicyRule,
    PolicySeverity,
    PolicyStage,
)

from .._demo_data import (
    POLICY_SAMPLE_CLEAN,
    POLICY_SAMPLE_DENY,
    POLICY_SAMPLE_PII,
    POLICY_SAMPLE_SSN,
)

_RULES: list[PolicyRule] = [
    PolicyRule(
        rule_id="pii-email",
        code="PII_EMAIL",
        description="Mask email addresses",
        stage=PolicyStage.PREFLIGHT,
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        severity=PolicySeverity.MEDIUM,  # MEDIUM → SANITIZE (no escalation)
        action=PolicyAction.SANITIZE,
        replacement="[EMAIL REDACTED]",
    ),
    PolicyRule(
        rule_id="pii-ssn",
        code="PII_SSN",
        description="Block SSN disclosure in prompts",
        stage=PolicyStage.PREFLIGHT,
        pattern=r"\b\d{3}-\d{2}-\d{4}\b",
        severity=PolicySeverity.CRITICAL,  # CRITICAL → DENY (deny_on_critical)
        action=PolicyAction.DENY,
        replacement="[SSN REDACTED]",
    ),
    PolicyRule(
        rule_id="pii-cc",
        code="PII_CC",
        description="Mask credit card numbers",
        stage=PolicyStage.PREFLIGHT,
        pattern=r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        severity=PolicySeverity.HIGH,  # HIGH → REQUIRE_APPROVAL (require_approval_on_high)
        action=PolicyAction.SANITIZE,
        replacement="[CARD REDACTED]",
    ),
]


_ACTION_COLORS = {
    PolicyAction.ALLOW: "green",
    PolicyAction.SANITIZE: "yellow",
    PolicyAction.DENY: "red",
    PolicyAction.REQUIRE_APPROVAL: "magenta",
}

_SEVERITY_COLORS = {
    PolicySeverity.LOW: "dim",
    PolicySeverity.MEDIUM: "blue",
    PolicySeverity.HIGH: "orange1",
    PolicySeverity.CRITICAL: "red",
}


class GovernanceTab(Widget):
    """PolicyGateway live evaluation — PREFLIGHT and POSTFLIGHT checks."""

    DEFAULT_CSS = """
    GovernanceTab {
        height: 1fr;
        padding: 1 2;
    }
    GovernanceTab .section-title {
        color: #cba6f7;
        text-style: bold;
        height: 2;
        padding: 0 0 0 1;
        content-align: left middle;
    }
    GovernanceTab .rules-box {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        height: 10;
        width: 40;
        margin-right: 2;
    }
    GovernanceTab .input-col {
        width: 1fr;
    }
    GovernanceTab TextArea {
        height: 7;
        margin-bottom: 1;
    }
    GovernanceTab .btn-row {
        height: 3;
        margin-bottom: 1;
    }
    GovernanceTab DataTable {
        height: 10;
        border: solid #313244;
        margin-bottom: 1;
    }
    GovernanceTab .decision-box {
        background: #181825;
        border: solid #313244;
        padding: 1 2;
        height: auto;
        margin-bottom: 1;
    }
    GovernanceTab RichLog {
        height: 1fr;
        border: solid #313244;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._gateway = PolicyGateway(rules=_RULES)

    def compose(self) -> ComposeResult:
        yield Label("🟣  Governance — PolicyGateway Runtime Enforcement", classes="section-title")

        with Horizontal():
            # Rules panel
            with Vertical(classes="rules-box"):
                yield Static("[bold #cba6f7]Active Rules[/bold #cba6f7]")
                for rule in _RULES:
                    sc = _SEVERITY_COLORS.get(rule.severity, "white")
                    ac = _ACTION_COLORS.get(rule.action, "white")
                    yield Static(
                        f"  [{sc}]{rule.severity.upper()}[/{sc}]  "
                        f"[bold]{rule.code}[/bold]  →  [{ac}]{rule.action}[/{ac}]"
                    )

            # Input and controls column
            with Vertical(classes="input-col"):
                yield TextArea(
                    POLICY_SAMPLE_PII,
                    id="policy-input",
                    show_line_numbers=False,
                )
                with Horizontal(classes="btn-row"):
                    yield Button("Evaluate PREFLIGHT", id="btn-preflight", variant="primary")
                    yield Button("Evaluate POSTFLIGHT", id="btn-postflight")
                    yield Button("PII sample", id="btn-pii")
                    yield Button("SSN/deny sample", id="btn-ssn")
                    yield Button("Clean sample", id="btn-clean")
                    yield Button("CC sample", id="btn-cc")

        # Findings table
        findings_table: DataTable[str] = DataTable(id="findings-table", zebra_stripes=True)
        yield findings_table

        # Decision box
        with Vertical(classes="decision-box"):
            yield Static("[bold #cba6f7]Policy Decision[/bold #cba6f7]")
            yield Label("", id="decision-action")
            yield Label("", id="decision-blocked")
            yield Label("", id="decision-sanitized")

        yield RichLog(id="gov-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        t: DataTable[str] = self.query_one("#findings-table", DataTable)
        t.add_column("Rule ID", key="rule", width=18)
        t.add_column("Code", key="code", width=14)
        t.add_column("Severity", key="sev", width=10)
        t.add_column("Action", key="action", width=14)
        t.add_column("Message", key="msg", width=50)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _evaluate(self, text: str, *, stage: PolicyStage) -> None:
        log = self.query_one("#gov-log", RichLog)
        table = self.query_one("#findings-table", DataTable)
        table.clear()

        decision: PolicyDecision = (
            self._gateway.evaluate_preflight(text)
            if stage == PolicyStage.PREFLIGHT
            else self._gateway.evaluate_postflight(text)
        )

        action_color = _ACTION_COLORS.get(decision.action, "white")

        for finding in decision.findings:
            sc = _SEVERITY_COLORS.get(finding.severity, "white")
            ac = _ACTION_COLORS.get(finding.action, "white")
            table.add_row(
                finding.rule_id,
                finding.code,
                f"[{sc}]{finding.severity.upper()}[/{sc}]",
                f"[{ac}]{finding.action}[/{ac}]",
                finding.message[:48],
            )

        # Decision summary
        action_lbl = self.query_one("#decision-action", Label)
        blocked_lbl = self.query_one("#decision-blocked", Label)
        san_lbl = self.query_one("#decision-sanitized", Label)

        action_lbl.update(
            f"  Action: [{action_color}][bold]{decision.action.upper()}[/bold][/{action_color}]  "
            f"|  Findings: {len(decision.findings)}  "
            f"|  Stage: {stage.value}"
        )
        blocked_lbl.update(
            f"  Blocked: [{'red' if decision.blocked else 'green'}]"
            f"{'YES — execution halted' if decision.blocked else 'NO — execution proceeds'}[/]"
        )
        if decision.sanitized_text:
            san_lbl.update(f"  Sanitized: [green]{decision.sanitized_text[:120]}[/green]")
        else:
            san_lbl.update("")

        verdict = f"[{action_color}]{decision.action.upper()}[/{action_color}]"
        log.write(
            f"[#cba6f7]⬡ POLICY[/#cba6f7]  {stage.value.upper()}  →  {verdict}  "
            f"|  {len(decision.findings)} finding(s)  "
            f"|  blocked={decision.blocked}"
        )

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    @on(Button.Pressed, "#btn-preflight")
    def _run_preflight(self, _event: Button.Pressed) -> None:
        text = self.query_one("#policy-input", TextArea).text
        self._evaluate(text, stage=PolicyStage.PREFLIGHT)

    @on(Button.Pressed, "#btn-postflight")
    def _run_postflight(self, _event: Button.Pressed) -> None:
        text = self.query_one("#policy-input", TextArea).text
        self._evaluate(text, stage=PolicyStage.POSTFLIGHT)

    @on(Button.Pressed, "#btn-pii")
    def _load_pii(self, _event: Button.Pressed) -> None:
        self.query_one("#policy-input", TextArea).load_text(POLICY_SAMPLE_PII)
        self._evaluate(POLICY_SAMPLE_PII, stage=PolicyStage.PREFLIGHT)

    @on(Button.Pressed, "#btn-ssn")
    def _load_ssn(self, _event: Button.Pressed) -> None:
        self.query_one("#policy-input", TextArea).load_text(POLICY_SAMPLE_SSN)
        self._evaluate(POLICY_SAMPLE_SSN, stage=PolicyStage.PREFLIGHT)

    @on(Button.Pressed, "#btn-clean")
    def _load_clean(self, _event: Button.Pressed) -> None:
        self.query_one("#policy-input", TextArea).load_text(POLICY_SAMPLE_CLEAN)
        self._evaluate(POLICY_SAMPLE_CLEAN, stage=PolicyStage.PREFLIGHT)

    @on(Button.Pressed, "#btn-cc")
    def _load_cc(self, _event: Button.Pressed) -> None:
        self.query_one("#policy-input", TextArea).load_text(POLICY_SAMPLE_DENY)
        self._evaluate(POLICY_SAMPLE_DENY, stage=PolicyStage.PREFLIGHT)
