"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Entry point for the character-based OCI Enterprise AI deployment menu.
"""

from __future__ import annotations

from enterprise_ai_deployment.cli_commands import (
    HostedApplicationCreateRequest,
    HostedApplicationJsonOptions,
    HostedDeploymentCreateRequest,
    build_create_hosted_application_command,
    build_create_hosted_deployment_command,
    build_get_hosted_application_command,
    build_get_hosted_deployment_command,
    build_list_compartments_by_name_command,
    build_list_hosted_applications_command,
    normalize_file_uri,
)
from enterprise_ai_deployment.config import OciCliConfig, load_config_from_env
from enterprise_ai_deployment.rendering import (
    console,
    pause,
    read_input,
    show_config,
    show_menu,
)
from enterprise_ai_deployment.workflows import (
    handle_create_hosted_application,
    handle_create_hosted_deployment,
    handle_get_hosted_application,
    handle_get_hosted_deployment,
    handle_list_hosted_applications,
    resolve_compartment_id,
)

__all__ = [
    "HostedApplicationCreateRequest",
    "HostedApplicationJsonOptions",
    "HostedDeploymentCreateRequest",
    "OciCliConfig",
    "build_create_hosted_application_command",
    "build_create_hosted_deployment_command",
    "build_get_hosted_application_command",
    "build_get_hosted_deployment_command",
    "build_list_compartments_by_name_command",
    "build_list_hosted_applications_command",
    "load_config_from_env",
    "main",
    "normalize_file_uri",
    "resolve_compartment_id",
]


def main() -> None:
    """Run the interactive menu."""
    config = load_config_from_env()
    handlers = {
        "1": handle_list_hosted_applications,
        "2": handle_get_hosted_application,
        "3": handle_get_hosted_deployment,
        "4": handle_create_hosted_application,
        "5": handle_create_hosted_deployment,
    }
    while True:
        show_menu(config)
        choice = read_input("[bold cyan]Selection:[/bold cyan] ").strip()
        if choice == "0":
            console().print("Bye.", style="cyan")
            return
        if choice == "6":
            show_config(config)
            pause()
            continue
        handler = handlers.get(choice)
        if handler is None:
            console().print("Invalid selection.", style="red")
            pause()
            continue
        try:
            handler(config)
        except RuntimeError as exc:
            console().print(f"Error: {exc}", style="yellow")
        pause()


if __name__ == "__main__":
    main()
