"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Rich rendering and terminal input helpers for the Enterprise AI menu.
"""

from __future__ import annotations

import os

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from enterprise_ai_deployment.config import DEFAULT_MENU_WIDTH, OciCliConfig, env


def menu_width() -> int:
    """Return the configured Rich console width."""
    value = env("AGENT_HUB_MENU_WIDTH")
    if value and value.isdigit():
        return max(DEFAULT_MENU_WIDTH, int(value))
    return DEFAULT_MENU_WIDTH


def console() -> Console:
    """Build a Rich console honoring local color preferences."""
    forced = (env("AGENT_HUB_MENU_COLOR") or "").lower()
    force_terminal = forced in {"1", "true", "yes", "always"} or None
    return Console(
        force_terminal=force_terminal,
        no_color=os.getenv("NO_COLOR") is not None,
        highlight=False,
        width=menu_width(),
    )


def status_text(value: str | None, missing_label: str) -> Text:
    """Format a config value for Rich display."""
    if value:
        return Text(value, style="green")
    return Text(missing_label, style="yellow")


def copyable_text(text: str, style: str | None = None) -> Text:
    """Return text that Rich should not hard-wrap or truncate."""
    return Text(text, style=style, no_wrap=True, overflow="ignore")


def print_box(title: str) -> None:
    """Print a compact Rich title rule."""
    console().rule(f"[bold cyan]{title.strip()}[/bold cyan]", style="blue")


def read_input(label: str) -> str:
    """Read one input line and exit cleanly on EOF."""
    try:
        return console().input(label)
    except EOFError as exc:
        console().print()
        raise SystemExit(0) from exc


def prompt(label: str, default: str | None = None, required: bool = False) -> str:
    """Prompt for a value, optionally with a default."""
    suffix = f" [{default}]" if default else ""
    while True:
        value = read_input(f"[bold]{label}{suffix}:[/bold] ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        console().print("Required value.", style="red")


def confirm(label: str, default: bool = False) -> bool:
    """Ask for a yes/no confirmation."""
    suffix = "Y/n" if default else "y/N"
    value = read_input(f"{label} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes"}


def pause() -> None:
    """Wait before returning to the menu."""
    read_input("\nPress Enter to continue...")


def show_menu(config: OciCliConfig) -> None:
    """Print the main menu."""
    rich_console = console()
    rich_console.print()
    entries = [
        ("1", "List hosted applications by region and compartment"),
        ("2", "Get hosted application details"),
        ("3", "Get hosted deployment details"),
        ("4", "Create a hosted application"),
        ("5", "Create a hosted deployment in a hosted application"),
        ("6", "Show detected CLI configuration"),
        ("0", "Exit"),
    ]
    menu_table = Table.grid(padding=(0, 1))
    menu_table.add_column(justify="right", style="bold green", no_wrap=True)
    menu_table.add_column(style="white")
    for key, label in entries:
        menu_table.add_row(f"[{key}]", label)

    config_table = Table.grid(padding=(0, 1))
    config_table.add_column(style="bold", no_wrap=True)
    config_table.add_column()
    config_table.add_row("Profile", status_text(config.profile, "<default OCI CLI>"))
    config_table.add_row("Region", status_text(config.region, "<default OCI CLI>"))
    config_table.add_row("Compartment", status_text(config.compartment_id, "<not set>"))

    rich_console.print(
        Panel(
            Group(menu_table, Text(""), config_table),
            title="[bold cyan]OCI Enterprise AI Deployment Menu[/bold cyan]",
            border_style="blue",
            padding=(1, 2),
        )
    )


def show_config(config: OciCliConfig) -> None:
    """Print detected configuration."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()
    table.add_row(
        "OCI_CLI_PROFILE / OCI_PROFILE", status_text(config.profile, "<default>")
    )
    table.add_row(
        "OCI_CLI_REGION / OCI_REGION", status_text(config.region, "<default>")
    )
    table.add_row(
        "OCI_COMPARTMENT_ID / COMPARTMENT_ID",
        status_text(config.compartment_id, "<empty>"),
    )
    table.add_row("OCI_CLI_OUTPUT", Text(config.output, style="green"))
    console().print(
        Panel(
            table,
            title="[bold cyan]Configuration[/bold cyan]",
            border_style="blue",
        )
    )


def show_hosted_applications(items: list[dict[str, object]]) -> None:
    """Render a compact hosted applications table."""
    rich_console = console()
    if not items:
        rich_console.print("No hosted applications found.", style="yellow")
        return

    table = Table(
        title="Hosted Applications",
        border_style="blue",
        show_lines=False,
    )
    table.add_column("Name", style="bold")
    table.add_column("State", style="green")
    table.add_column("Created", style="dim")
    table.add_column("Description")
    table.add_column("OCID", style="cyan")

    for item in items:
        table.add_row(
            _string_value(item, "display-name", "name"),
            _string_value(item, "lifecycle-state", "lifecycleState"),
            _string_value(item, "time-created", "timeCreated"),
            _short_text(_string_value(item, "description")),
            _short_ocid(_string_value(item, "id")),
        )

    rich_console.print(table)


def show_hosted_application_details(item: dict[str, object]) -> None:
    """Render hosted application details in a compact table."""
    table = Table(
        title="Hosted Application Details",
        border_style="blue",
        show_header=False,
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    rows = [
        ("Name", _string_value(item, "display-name", "name")),
        ("State", _string_value(item, "lifecycle-state", "lifecycleState")),
        ("Created", _string_value(item, "time-created", "timeCreated")),
        ("Updated", _string_value(item, "time-updated", "timeUpdated")),
        ("Description", _string_value(item, "description")),
        ("Compartment", _string_value(item, "compartment-id", "compartmentId")),
        ("OCID", _string_value(item, "id")),
    ]
    for label, value in rows:
        if value:
            table.add_row(label, copyable_text(value))

    console().print(table)


def _string_value(item: dict[str, object], *keys: str) -> str:
    """Return the first non-empty string value from a JSON object."""
    for key in keys:
        value = item.get(key)
        if value is not None:
            return str(value)
    return ""


def _short_ocid(value: str) -> str:
    """Return an OCID preview suitable for compact tables."""
    if len(value) <= 36:
        return value
    return f"{value[:24]}...{value[-12:]}"


def _short_text(value: str, max_length: int = 48) -> str:
    """Return a compact text preview suitable for terminal tables."""
    if len(value) <= max_length:
        return value
    return f"{value[: max_length - 3]}..."
