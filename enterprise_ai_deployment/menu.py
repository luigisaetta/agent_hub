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
import sys
from dataclasses import dataclass
from pathlib import Path

MENU_WIDTH = 72
DEFAULT_WAIT_STATE = "SUCCEEDED"
COMPARTMENT_OCID_PREFIX = "ocid1.compartment."
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"


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


def _supports_color() -> bool:
    """Return whether ANSI colors should be emitted."""
    forced = (_env("AGENT_HUB_MENU_COLOR") or "").lower()
    if forced in {"1", "true", "yes", "always"}:
        return True
    if os.getenv("NO_COLOR") is not None:
        return False
    if (_env("TERM") or "").lower() == "dumb":
        return False
    return sys.stdout.isatty()


def _style(text: str, *codes: str) -> str:
    """Style text with ANSI codes when supported by the current terminal."""
    if not codes or not _supports_color():
        return text
    return f"{''.join(codes)}{text}{ANSI_RESET}"


def _rule(char: str = "-") -> str:
    """Return a styled horizontal rule."""
    return _style(char * MENU_WIDTH, ANSI_DIM, ANSI_BLUE)


def _status_value(value: str | None, missing_label: str) -> str:
    """Format a config value for menu display."""
    if value:
        return _style(value, ANSI_GREEN)
    return _style(missing_label, ANSI_YELLOW)


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


def build_iam_base_command(config: OciCliConfig) -> list[str]:
    """Build the common OCI IAM CLI command prefix."""
    command = ["oci"]
    if config.profile:
        command.extend(["--profile", config.profile])
    if config.region:
        command.extend(["--region", config.region])
    command.extend(["--output", "json", "iam"])
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


def build_list_hosted_applications_command(
    config: OciCliConfig, compartment_id: str
) -> list[str]:
    """Build command for hosted application listing."""
    return [
        *build_base_command(config),
        "hosted-application-collection",
        "list-hosted-applications",
        "--compartment-id",
        compartment_id,
        "--all",
    ]


def build_list_compartments_by_name_command(
    config: OciCliConfig, compartment_name: str
) -> list[str]:
    """Build command for resolving a compartment name to OCID."""
    return [
        *build_iam_base_command(config),
        "compartment",
        "list",
        "--name",
        compartment_name,
        "--compartment-id-in-subtree",
        "true",
        "--access-level",
        "ANY",
        "--include-root",
        "--all",
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
    print(_style(" ".join(command), ANSI_CYAN))
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


def _extract_items(payload: dict[str, object]) -> list[dict[str, object]]:
    """Extract OCI CLI list items from common response shapes."""
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _compartment_label(compartment: dict[str, object]) -> str:
    """Return a compact display label for one compartment."""
    name = str(compartment.get("name") or "<unnamed>")
    compartment_id = str(compartment.get("id") or "<missing id>")
    lifecycle_state = compartment.get("lifecycle-state")
    state_suffix = f", {lifecycle_state}" if lifecycle_state else ""
    return f"{name} ({compartment_id}{state_suffix})"


def resolve_compartment_id(config: OciCliConfig, name_or_ocid: str) -> str:
    """Resolve a compartment OCID from either an OCID or a display name."""
    value = name_or_ocid.strip()
    if value.startswith(COMPARTMENT_OCID_PREFIX):
        return value

    command = build_list_compartments_by_name_command(config, value)
    print("")
    print_box("Resolve Compartment")
    print(_style(" ".join(command), ANSI_CYAN))
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip())
        raise RuntimeError(f"Unable to resolve compartment name: {value}")

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "OCI CLI returned invalid JSON while resolving compartment."
        ) from exc

    matches = [
        item
        for item in _extract_items(payload)
        if str(item.get("name") or "") == value and item.get("id")
    ]
    if not matches:
        raise RuntimeError(f"No compartment found with name: {value}")
    if len(matches) == 1:
        return str(matches[0]["id"])

    print("")
    print("Multiple compartments matched this name:")
    for index, compartment in enumerate(matches, start=1):
        print(f" {index}. {_compartment_label(compartment)}")
    while True:
        selection = prompt("Select compartment", required=True)
        if selection.isdigit() and 1 <= int(selection) <= len(matches):
            return str(matches[int(selection) - 1]["id"])
        print("Invalid selection.")


def print_box(title: str) -> None:
    """Print a compact ASCII title box."""
    safe_title = f" {title.strip()} "
    side = max(0, MENU_WIDTH - len(safe_title) - 2)
    left = side // 2
    right = side - left
    border = "+" + "-" * left
    tail = "-" * right + "+"
    print(
        _style(border, ANSI_BLUE)
        + _style(safe_title, ANSI_BOLD, ANSI_CYAN)
        + _style(tail, ANSI_BLUE)
    )


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
        value = read_input(_style(f"{label}{suffix}: ", ANSI_BOLD)).strip()
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
    entries = [
        ("1", "List hosted applications by region and compartment"),
        ("2", "Get hosted application details"),
        ("3", "Get hosted deployment details"),
        ("4", "Create a hosted application"),
        ("5", "Create a hosted deployment in a hosted application"),
        ("6", "Show detected CLI configuration"),
        ("0", "Exit"),
    ]
    for key, label in entries:
        print(f" {_style(f'[{key}]', ANSI_BOLD, ANSI_GREEN)} {label}")
    print(_rule())
    print(
        f" {_style('Profile:', ANSI_BOLD)}     "
        f"{_status_value(config.profile, '<default OCI CLI>')}"
    )
    print(
        f" {_style('Region:', ANSI_BOLD)}      "
        f"{_status_value(config.region, '<default OCI CLI>')}"
    )
    print(
        f" {_style('Compartment:', ANSI_BOLD)} {_status_value(config.compartment_id, '<not set>')}"
    )
    print(_rule())


def handle_get_hosted_application(config: OciCliConfig) -> None:
    """Handle menu option 1."""
    app_id = prompt("Hosted application OCID", required=True)
    run_oci_command(build_get_hosted_application_command(config, app_id))


def handle_get_hosted_deployment(config: OciCliConfig) -> None:
    """Handle menu option 2."""
    deployment_id = prompt("Hosted deployment OCID", required=True)
    run_oci_command(build_get_hosted_deployment_command(config, deployment_id))


def handle_list_hosted_applications(config: OciCliConfig) -> None:
    """Handle menu option 1."""
    region = prompt("Region", default=config.region, required=True)
    compartment_name_or_ocid = prompt(
        "Compartment name or OCID", default=config.compartment_id, required=True
    )
    effective_config = OciCliConfig(
        profile=config.profile,
        region=region,
        compartment_id=config.compartment_id,
        output=config.output,
    )
    compartment_id = resolve_compartment_id(effective_config, compartment_name_or_ocid)
    run_oci_command(
        build_list_hosted_applications_command(effective_config, compartment_id)
    )


def handle_create_hosted_application(config: OciCliConfig) -> None:
    """Handle menu option 4."""
    display_name = prompt("Display name", required=True)
    compartment_name_or_ocid = prompt(
        "Compartment name or OCID", default=config.compartment_id, required=True
    )
    compartment_id = resolve_compartment_id(config, compartment_name_or_ocid)
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
    """Handle menu option 5."""
    app_id = prompt("Hosted application OCID", required=True)
    display_name = prompt("Deployment display name", required=False)
    compartment_name_or_ocid = prompt(
        "Compartment name or OCID", default=config.compartment_id
    )
    compartment_id = (
        resolve_compartment_id(config, compartment_name_or_ocid)
        if compartment_name_or_ocid
        else None
    )
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
            compartment_id=compartment_id,
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
    print(
        f"{_style('OCI_CLI_PROFILE / OCI_PROFILE:', ANSI_BOLD)}       "
        f"{_status_value(config.profile, '<default>')}"
    )
    print(
        f"{_style('OCI_CLI_REGION / OCI_REGION:', ANSI_BOLD)}         "
        f"{_status_value(config.region, '<default>')}"
    )
    print(
        f"{_style('OCI_COMPARTMENT_ID / COMPARTMENT_ID:', ANSI_BOLD)} "
        f"{_status_value(config.compartment_id, '<empty>')}"
    )
    print(
        f"{_style('OCI_CLI_OUTPUT:', ANSI_BOLD)}                      "
        f"{_style(config.output, ANSI_GREEN)}"
    )


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
        choice = read_input(_style("Selection: ", ANSI_BOLD, ANSI_CYAN)).strip()
        if choice == "0":
            print(_style("Bye.", ANSI_CYAN))
            return
        if choice == "6":
            show_config(config)
            pause()
            continue
        handler = handlers.get(choice)
        if handler is None:
            print("Invalid selection.")
            pause()
            continue
        try:
            handler(config)
        except RuntimeError as exc:
            print(_style(f"Error: {exc}", ANSI_YELLOW))
        pause()


if __name__ == "__main__":
    main()
