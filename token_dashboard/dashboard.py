"""
Unified Token Usage Dashboard
===============================================================================
Accepts a list of usage_records (one per provider call) and renders a rich
cross-provider comparison table plus a per-provider breakdown.

Each usage_record must have the shape:
    {
        "provider": str,
        "model": str,
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int,
    }

Usage (standalone):
    from token_dashboard.dashboard import print_dashboard
    print_dashboard(usage_records)
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def print_dashboard(usage_records: list[dict]) -> None:
    """Print a unified token-usage comparison table for all provider calls."""
    if not usage_records:
        console.print("[yellow]No usage records to display.[/]")
        return

    console.print()
    console.rule("[bold white]⚡  Unified Token Usage Dashboard  ⚡[/]")

    # Main comparison table
    table = Table(
        title="Token Usage Across Providers",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on dark_blue",
        show_footer=True,
    )
    table.add_column("Provider", style="bold", footer="TOTAL")
    table.add_column("Model", style="dim")
    table.add_column("Prompt Tokens", justify="right",
                     footer=str(sum(r.get("prompt_tokens", 0) for r in usage_records)))
    table.add_column("Completion Tokens", justify="right",
                     footer=str(sum(r.get("completion_tokens", 0) for r in usage_records)))
    table.add_column("Total Tokens", justify="right", style="bold green",
                     footer=str(sum(r.get("total_tokens", 0) for r in usage_records)))

    for rec in usage_records:
        table.add_row(
            rec.get("provider", "unknown"),
            rec.get("model", "unknown"),
            str(rec.get("prompt_tokens", "N/A")),
            str(rec.get("completion_tokens", "N/A")),
            str(rec.get("total_tokens", "N/A")),
        )

    console.print(table)

    # Efficiency note
    if len(usage_records) > 1:
        best = min(usage_records, key=lambda r: r.get("total_tokens", float("inf")))
        console.print(
            Panel(
                f"[green]Most token-efficient:[/] [bold]{best['provider']}[/] "
                f"({best.get('total_tokens', '?')} total tokens)",
                expand=False,
            )
        )
