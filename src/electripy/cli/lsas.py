"""LSAS subcommands for the ElectriPy CLI.

Provides offline LSAS scoring without any network calls.

Commands::

    electripy lsas score "some text to evaluate"
    electripy lsas score "some text" --pack hipaa
    electripy lsas packs
"""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from electripy.ai.lsas import run_decision_engine
from electripy.ai.lsas.policy_packs import get_pack, list_packs
from electripy.ai.lsas.validators import build_default_validators

app = typer.Typer(
    name="lsas",
    help="LSAS (Language Safety Assurance System) scoring commands.",
    no_args_is_help=True,
)

console = Console()


@app.command()
def score(
    text: Annotated[str, typer.Argument(help="Text to evaluate through the LSAS engine.")],
    pack: Annotated[
        str,
        typer.Option("--pack", "-p", help="Policy pack ID to use (demo, hipaa, pci)."),
    ] = "demo",
) -> None:
    """Score TEXT with the LSAS decision engine and print the result.

    The command runs completely offline — no network calls, no API keys.

    Examples::

        electripy lsas score "Contact alice@example.com"
        electripy lsas score "sk-abcdef1234567890abcdef" --pack demo
        electripy lsas score "Patient SSN: 123-45-6789" --pack hipaa
    """
    try:
        policy_pack = get_pack(pack)
    except KeyError:
        available = ", ".join(p.pack_id for p in list_packs())
        console.print(
            f"[red]✗[/red] Unknown pack [bold]{pack!r}[/bold]. " f"Available packs: {available}"
        )
        raise typer.Exit(1) from None

    validators = build_default_validators()

    result = run_decision_engine(
        text=text,
        validators=validators,
        pack=policy_pack,
    )

    # --- Decision panel -------------------------------------------------------
    decision_color = {
        "ALLOW": "green",
        "ALLOW_WITH_WARNINGS": "yellow",
        "REDACTED": "yellow",
        "BLOCKED": "red",
        "ESCALATE_HITL": "magenta",
    }.get(result.decision.value, "white")

    tier_color = {
        "SAFE": "green",
        "LOW": "cyan",
        "MEDIUM": "yellow",
        "HIGH": "red",
        "CRITICAL": "magenta",
    }.get(result.risk_summary.tier.value, "white")

    console.print()
    console.print(
        Panel(
            f"[bold {decision_color}]{result.decision.value}[/bold {decision_color}]",
            title="[bold]LSAS Decision[/bold]",
            expand=False,
        )
    )

    # --- Summary table --------------------------------------------------------
    summary_table = Table(show_header=False, box=None, padding=(0, 1))
    summary_table.add_column("Key", style="bold cyan")
    summary_table.add_column("Value")
    summary_table.add_row(
        "Risk Tier", f"[{tier_color}]{result.risk_summary.tier.value}[/{tier_color}]"
    )
    summary_table.add_row("Overall Score", f"{result.risk_summary.overall_score:.2f}")
    summary_table.add_row("Findings", str(result.risk_summary.finding_count))
    summary_table.add_row("Policy Pack", f"{policy_pack.pack_id} v{policy_pack.version}")
    console.print(summary_table)

    # --- Findings table -------------------------------------------------------
    if result.findings:
        console.print()
        findings_table = Table(
            title="Findings",
            show_header=True,
            header_style="bold magenta",
        )
        findings_table.add_column("Code", style="cyan", no_wrap=True)
        findings_table.add_column("Severity", no_wrap=True)
        findings_table.add_column("Domain", no_wrap=True)
        findings_table.add_column("Message")
        findings_table.add_column("Matched")

        for finding in result.findings:
            sev_color = {
                "LOW": "green",
                "MEDIUM": "yellow",
                "HIGH": "red",
                "CRITICAL": "magenta",
            }.get(finding.severity.value, "white")
            matched = (finding.matched_text or "")[:30]
            findings_table.add_row(
                finding.code,
                f"[{sev_color}]{finding.severity.value}[/{sev_color}]",
                finding.domain.value,
                finding.message,
                matched,
            )
        console.print(findings_table)

    # --- Remediations ---------------------------------------------------------
    if result.remediations:
        console.print()
        rem_table = Table(
            title="Remediations",
            show_header=True,
            header_style="bold magenta",
        )
        rem_table.add_column("Type", style="cyan", no_wrap=True)
        rem_table.add_column("Domain", no_wrap=True)
        rem_table.add_column("Description")
        for rem in result.remediations:
            rem_table.add_row(rem.remediation_type, rem.domain.value, rem.description)
        console.print(rem_table)

    # --- Sanitized text -------------------------------------------------------
    if result.sanitized_text is not None:
        console.print()
        console.print(
            Panel(
                result.sanitized_text,
                title="[bold]Sanitized Text[/bold]",
                border_style="yellow",
            )
        )

    console.print()


@app.command()
def packs() -> None:
    """List available built-in LSAS policy packs."""
    console.print()
    table = Table(
        title="Built-in LSAS Policy Packs",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Pack ID", style="cyan", no_wrap=True)
    table.add_column("Version", no_wrap=True)
    table.add_column("Thresholds (warn/redact/block/escalate)")
    table.add_column("Description")

    for p in list_packs():
        t = p.thresholds
        table.add_row(
            p.pack_id,
            p.version,
            f"{t.warn} / {t.redact} / {t.block} / {t.escalate}",
            p.description[:60],
        )

    console.print(table)
    console.print()
