"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Character-based menu for OCI Enterprise AI hosted applications and
    deployments, backed by the OCI CLI.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

MENU_WIDTH = 72
DEFAULT_WAIT_STATE = "SUCCEEDED"


@dataclass(frozen=True)
class OciCliConfig:
    """Global OCI CLI options shared by all menu operations."""

    profile: str | None = None
    region: str | None = None
    compartment_id: str | None = None
    output: str = "json"


@dataclass(frozen=True)
class HostedApplicationJsonOptions:
    """Optional JSON files for hosted application creation."""

    scaling_config: str | None = None
    inbound_auth_config: str | None = None
    networking_config: str | None = None
    storage_configs: str | None = None
    environment_variables: str | None = None


@dataclass(frozen=True)
class HostedApplicationCreateRequest:
    """Values needed to create a hosted application."""

    display_name: str
    compartment_id: str
    description: str | None = None
    json_options: HostedApplicationJsonOptions | None = None
    wait: bool = True


@dataclass(frozen=True)
class HostedDeploymentCreateRequest:
    """Values needed to create a hosted deployment."""

    hosted_application_id: str
    display_name: str | None = None
    compartment_id: str | None = None
    container_uri: str | None = None
    artifact_tag: str | None = None
    active_artifact_json: str | None = None
    wait: bool = True


def _env(name: str) -> str | None:
    """Return a stripped environment value or None."""
    value = os.getenv(name, "").strip()
    return value or None


def load_config_from_env() -> OciCliConfig:
    """Load optional OCI CLI defaults from environment variables."""
    return OciCliConfig(
        profile=_env("OCI_CLI_PROFILE") or _env("OCI_PROFILE"),
        region=_env("OCI_CLI_REGION") or _env("OCI_REGION"),
        compartment_id=_env("OCI_COMPARTMENT_ID") or _env("COMPARTMENT_ID"),
        output=_env("OCI_CLI_OUTPUT") or "json",
    )


def build_base_command(config: OciCliConfig) -> list[str]:
    """Build the common OCI CLI command prefix."""
    command = ["oci"]
    if config.profile:
        command.extend(["--profile", config.profile])
    if config.region:
        command.extend(["--region", config.region])
    if config.output:
        command.extend(["--output", config.output])
    command.extend(["generative-ai"])
    return command


def normalize_file_uri(path_or_uri: str) -> str:
    """Return an OCI CLI file URI for a local JSON path."""
    value = path_or_uri.strip()
    if value.startswith("file://"):
        return value
    return f"file://{Path(value).expanduser()}"


def build_get_hosted_application_command(
    config: OciCliConfig, hosted_application_id: str
) -> list[str]:
    """Build command for hosted application details."""
    return [
        *build_base_command(config),
        "hosted-application",
        "get",
        "--hosted-application-id",
        hosted_application_id,
    ]


def build_get_hosted_deployment_command(
    config: OciCliConfig, hosted_deployment_id: str
) -> list[str]:
    """Build command for hosted deployment details."""
    return [
        *build_base_command(config),
        "hosted-deployment",
        "get",
        "--hosted-deployment-id",
        hosted_deployment_id,
    ]


def build_create_hosted_application_command(
    config: OciCliConfig, request: HostedApplicationCreateRequest
) -> list[str]:
    """Build command for hosted application creation."""
    command = [
        *build_base_command(config),
        "hosted-application",
        "create",
        "--display-name",
        request.display_name,
        "--compartment-id",
        request.compartment_id,
    ]
    if request.description:
        command.extend(["--description", request.description])
    json_options = request.json_options or HostedApplicationJsonOptions()
    optional_json_args = {
        "--scaling-config": json_options.scaling_config,
        "--inbound-auth-config": json_options.inbound_auth_config,
        "--networking-config": json_options.networking_config,
        "--storage-configs": json_options.storage_configs,
        "--environment-variables": json_options.environment_variables,
    }
    for option, value in optional_json_args.items():
        if value:
            command.extend([option, normalize_file_uri(value)])
    if request.wait:
        command.extend(["--wait-for-state", DEFAULT_WAIT_STATE])
    return command


def build_create_hosted_deployment_command(
    config: OciCliConfig, request: HostedDeploymentCreateRequest
) -> list[str]:
    """Build command for hosted deployment creation."""
    if request.active_artifact_json:
        command = [
            *build_base_command(config),
            "hosted-deployment",
            "create",
            "--hosted-application-id",
            request.hosted_application_id,
            "--active-artifact",
            normalize_file_uri(request.active_artifact_json),
        ]
    else:
        command = [
            *build_base_command(config),
            "hosted-deployment",
            "create-hosted-deployment-single-docker-artifact",
            "--hosted-application-id",
            request.hosted_application_id,
        ]
        if request.container_uri:
            command.extend(["--active-artifact-container-uri", request.container_uri])
        if request.artifact_tag:
            command.extend(["--active-artifact-tag", request.artifact_tag])

    if request.display_name:
        command.extend(["--display-name", request.display_name])
    if request.compartment_id:
        command.extend(["--compartment-id", request.compartment_id])
    if request.wait:
        command.extend(["--wait-for-state", DEFAULT_WAIT_STATE])
    return command


def run_oci_command(command: list[str]) -> int:
    """Run one OCI CLI command and print a readable result."""
    print("")
    print_box("OCI Command")
    print(" ".join(command))
    print("")
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(_pretty_json(result.stdout))
    if result.stderr:
        print(result.stderr.strip())
    print("")
    print(f"Exit code: {result.returncode}")
    return result.returncode


def _pretty_json(text: str) -> str:
    """Pretty-print JSON output when possible."""
    try:
        return json.dumps(json.loads(text), indent=2, sort_keys=True)
    except json.JSONDecodeError:
        return text.strip()


def print_box(title: str) -> None:
    """Print a compact ASCII title box."""
    safe_title = f" {title.strip()} "
    side = max(0, MENU_WIDTH - len(safe_title) - 2)
    left = side // 2
    right = side - left
    print("+" + "-" * left + safe_title + "-" * right + "+")


def read_input(label: str) -> str:
    """Read one input line and exit cleanly on EOF."""
    try:
        return input(label)
    except EOFError as exc:
        print("")
        raise SystemExit(0) from exc


def prompt(label: str, default: str | None = None, required: bool = False) -> str:
    """Prompt for a value, optionally with a default."""
    suffix = f" [{default}]" if default else ""
    while True:
        value = read_input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print("Required value.")


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
    print("")
    print_box("OCI Enterprise AI Deployment Menu")
    print(" 1. Get hosted application details")
    print(" 2. Get hosted deployment details")
    print(" 3. Create a hosted application")
    print(" 4. Create a hosted deployment in a hosted application")
    print(" 5. Show detected CLI configuration")
    print(" 0. Exit")
    print("-" * MENU_WIDTH)
    print(f" Profile:     {config.profile or '<default OCI CLI>'}")
    print(f" Region:      {config.region or '<default OCI CLI>'}")
    print(f" Compartment: {config.compartment_id or '<not set>'}")
    print("-" * MENU_WIDTH)


def handle_get_hosted_application(config: OciCliConfig) -> None:
    """Handle menu option 1."""
    app_id = prompt("Hosted application OCID", required=True)
    run_oci_command(build_get_hosted_application_command(config, app_id))


def handle_get_hosted_deployment(config: OciCliConfig) -> None:
    """Handle menu option 2."""
    deployment_id = prompt("Hosted deployment OCID", required=True)
    run_oci_command(build_get_hosted_deployment_command(config, deployment_id))


def handle_create_hosted_application(config: OciCliConfig) -> None:
    """Handle menu option 3."""
    display_name = prompt("Display name", required=True)
    compartment_id = prompt(
        "Compartment OCID", default=config.compartment_id, required=True
    )
    description = prompt("Description", required=False)
    print("")
    print("Optional JSON files: leave empty to skip them for now.")
    scaling_config = prompt("Scaling config JSON path", required=False)
    inbound_auth_config = prompt("Inbound auth config JSON path", required=False)
    networking_config = prompt("Networking config JSON path", required=False)
    storage_configs = prompt("Storage configs JSON path", required=False)
    environment_variables = prompt("Environment variables JSON path", required=False)
    wait = confirm("Wait for the work request to finish?", default=True)
    command = build_create_hosted_application_command(
        config,
        HostedApplicationCreateRequest(
            display_name=display_name,
            compartment_id=compartment_id,
            description=description or None,
            json_options=HostedApplicationJsonOptions(
                scaling_config=scaling_config or None,
                inbound_auth_config=inbound_auth_config or None,
                networking_config=networking_config or None,
                storage_configs=storage_configs or None,
                environment_variables=environment_variables or None,
            ),
            wait=wait,
        ),
    )
    if confirm("Confirm hosted application creation?", default=False):
        run_oci_command(command)
    else:
        print("Operation cancelled.")


def handle_create_hosted_deployment(config: OciCliConfig) -> None:
    """Handle menu option 4."""
    app_id = prompt("Hosted application OCID", required=True)
    display_name = prompt("Deployment display name", required=False)
    compartment_id = prompt("Compartment OCID", default=config.compartment_id)
    print("")
    print("Use a full active-artifact JSON file or the guided Docker image path.")
    active_artifact_json = prompt("Active artifact JSON path", required=False)
    container_uri = None
    artifact_tag = None
    if not active_artifact_json:
        container_uri = prompt("Docker image/container URI", required=True)
        artifact_tag = prompt("Docker image tag", required=False)
    wait = confirm("Wait for the work request to finish?", default=True)
    command = build_create_hosted_deployment_command(
        config,
        HostedDeploymentCreateRequest(
            hosted_application_id=app_id,
            display_name=display_name or None,
            compartment_id=compartment_id or None,
            container_uri=container_uri,
            artifact_tag=artifact_tag or None,
            active_artifact_json=active_artifact_json or None,
            wait=wait,
        ),
    )
    if confirm("Confirm deployment creation?", default=False):
        run_oci_command(command)
    else:
        print("Operation cancelled.")


def show_config(config: OciCliConfig) -> None:
    """Print detected configuration."""
    print_box("Configuration")
    print(f"OCI_CLI_PROFILE / OCI_PROFILE:       {config.profile or '<default>'}")
    print(f"OCI_CLI_REGION / OCI_REGION:         {config.region or '<default>'}")
    print(f"OCI_COMPARTMENT_ID / COMPARTMENT_ID: {config.compartment_id or '<empty>'}")
    print(f"OCI_CLI_OUTPUT:                      {config.output}")


def main() -> None:
    """Run the interactive menu."""
    config = load_config_from_env()
    handlers = {
        "1": handle_get_hosted_application,
        "2": handle_get_hosted_deployment,
        "3": handle_create_hosted_application,
        "4": handle_create_hosted_deployment,
    }
    while True:
        show_menu(config)
        choice = read_input("Selection: ").strip()
        if choice == "0":
            print("Bye.")
            return
        if choice == "5":
            show_config(config)
            pause()
            continue
        handler = handlers.get(choice)
        if handler is None:
            print("Invalid selection.")
            pause()
            continue
        handler(config)
        pause()


if __name__ == "__main__":
    main()
