"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Interactive workflows for OCI Enterprise AI hosted application and
    deployment operations.
"""

from __future__ import annotations

import json
import subprocess

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
)
from enterprise_ai_deployment.config import COMPARTMENT_OCID_PREFIX, OciCliConfig
from enterprise_ai_deployment.rendering import (
    confirm,
    console,
    copyable_text,
    print_box,
    prompt,
    show_hosted_application_details,
    show_hosted_applications,
)

_COMPARTMENT_CACHE: dict[tuple[str | None, str | None, str], str] = {}


def run_oci_command(command: list[str]) -> int:
    """Run one OCI CLI command and print a readable result."""
    rich_console = console()
    rich_console.print()
    print_box("OCI Command")
    rich_console.print(copyable_text(" ".join(command), style="cyan"), soft_wrap=True)
    rich_console.print()
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        rich_console.print(copyable_text(_pretty_json(result.stdout)), soft_wrap=True)
    if result.stderr:
        rich_console.print(
            copyable_text(result.stderr.strip(), style="yellow"),
            soft_wrap=True,
        )
    rich_console.print()
    style = "green" if result.returncode == 0 else "red"
    rich_console.print(f"Exit code: {result.returncode}", style=style)
    return result.returncode


def run_hosted_applications_list(command: list[str]) -> int:
    """Run hosted application listing and optionally inspect one result."""
    rich_console = console()
    rich_console.print()
    print_box("OCI Command")
    rich_console.print(copyable_text(" ".join(command), style="cyan"), soft_wrap=True)
    rich_console.print()
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            rich_console.print(copyable_text(result.stdout.strip()), soft_wrap=True)
        else:
            items = _extract_items(payload)
            show_hosted_applications(items)
            if confirm("Show raw JSON response?", default=False):
                rich_console.print()
                print_box("Raw JSON")
                rich_console.print(
                    copyable_text(_pretty_json(result.stdout)), soft_wrap=True
                )
            selected_id = _select_hosted_application_id(items)
            if selected_id:
                run_hosted_application_details(
                    build_get_hosted_application_command_from_list(command, selected_id)
                )
    if result.stderr:
        rich_console.print(
            copyable_text(result.stderr.strip(), style="yellow"),
            soft_wrap=True,
        )
    rich_console.print()
    style = "green" if result.returncode == 0 else "red"
    rich_console.print(f"Exit code: {result.returncode}", style=style)
    return result.returncode


def run_hosted_application_details(command: list[str]) -> int:
    """Run hosted application get and print table plus optional raw JSON."""
    rich_console = console()
    rich_console.print()
    print_box("OCI Command")
    rich_console.print(copyable_text(" ".join(command), style="cyan"), soft_wrap=True)
    rich_console.print()
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            rich_console.print(copyable_text(result.stdout.strip()), soft_wrap=True)
        else:
            data = payload.get("data")
            if isinstance(data, dict):
                show_hosted_application_details(data)
            else:
                rich_console.print(
                    copyable_text(_pretty_json(result.stdout)), soft_wrap=True
                )
            if confirm("Show raw JSON response?", default=False):
                rich_console.print()
                print_box("Raw JSON")
                rich_console.print(
                    copyable_text(_pretty_json(result.stdout)), soft_wrap=True
                )
    if result.stderr:
        rich_console.print(
            copyable_text(result.stderr.strip(), style="yellow"),
            soft_wrap=True,
        )
    rich_console.print()
    style = "green" if result.returncode == 0 else "red"
    rich_console.print(f"Exit code: {result.returncode}", style=style)
    return result.returncode


def build_get_hosted_application_command_from_list(
    list_command: list[str], hosted_application_id: str
) -> list[str]:
    """Build a get command using global options from a list command."""
    generative_ai_index = list_command.index("generative-ai")
    return [
        *list_command[: generative_ai_index + 1],
        "hosted-application",
        "get",
        "--hosted-application-id",
        hosted_application_id,
    ]


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


def _select_hosted_application_id(items: list[dict[str, object]]) -> str | None:
    """Optionally select one hosted application from the latest list."""
    selectable_items = [item for item in items if item.get("id")]
    if not selectable_items:
        return None
    if not confirm("Get details for one hosted application?", default=False):
        return None

    rich_console = console()
    while True:
        selection = prompt(
            f"Select hosted application number [1-{len(selectable_items)}]",
            required=True,
        )
        if selection.isdigit() and 1 <= int(selection) <= len(selectable_items):
            return str(selectable_items[int(selection) - 1]["id"])
        rich_console.print("Invalid selection.", style="red")


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

    cache_key = (config.profile, config.region, value)
    cached_id = _COMPARTMENT_CACHE.get(cache_key)
    if cached_id:
        console().print(
            f"Using cached compartment OCID for {value}: {cached_id}",
            style="dim",
        )
        return cached_id

    command = build_list_compartments_by_name_command(config, value)
    rich_console = console()
    rich_console.print()
    print_box("Resolve Compartment")
    rich_console.print(copyable_text(" ".join(command), style="cyan"), soft_wrap=True)
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if result.stderr:
            rich_console.print(
                copyable_text(result.stderr.strip(), style="yellow"),
                soft_wrap=True,
            )
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
        compartment_id = str(matches[0]["id"])
        _COMPARTMENT_CACHE[cache_key] = compartment_id
        return compartment_id

    rich_console.print()
    rich_console.print("Multiple compartments matched this name:", style="bold yellow")
    for index, compartment in enumerate(matches, start=1):
        rich_console.print(f" {index}. {_compartment_label(compartment)}")
    while True:
        selection = prompt("Select compartment", required=True)
        if selection.isdigit() and 1 <= int(selection) <= len(matches):
            compartment_id = str(matches[int(selection) - 1]["id"])
            _COMPARTMENT_CACHE[cache_key] = compartment_id
            return compartment_id
        rich_console.print("Invalid selection.", style="red")


def clear_compartment_cache() -> None:
    """Clear cached compartment name resolutions."""
    _COMPARTMENT_CACHE.clear()


def handle_get_hosted_application(config: OciCliConfig) -> None:
    """Handle hosted application details lookup."""
    app_id = prompt("Hosted application OCID", required=True)
    run_hosted_application_details(build_get_hosted_application_command(config, app_id))


def handle_get_hosted_deployment(config: OciCliConfig) -> None:
    """Handle hosted deployment details lookup."""
    deployment_id = prompt("Hosted deployment OCID", required=True)
    run_oci_command(build_get_hosted_deployment_command(config, deployment_id))


def handle_list_hosted_applications(config: OciCliConfig) -> None:
    """Handle hosted application listing."""
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
    run_hosted_applications_list(
        build_list_hosted_applications_command(effective_config, compartment_id)
    )


def handle_create_hosted_application(config: OciCliConfig) -> None:
    """Handle hosted application creation."""
    display_name = prompt("Display name", required=True)
    compartment_name_or_ocid = prompt(
        "Compartment name or OCID", default=config.compartment_id, required=True
    )
    compartment_id = resolve_compartment_id(config, compartment_name_or_ocid)
    description = prompt("Description", required=False)
    console().print()
    console().print(
        "Optional JSON files: leave empty to skip them for now.",
        style="dim",
    )
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
        console().print("Operation cancelled.", style="yellow")


def handle_create_hosted_deployment(config: OciCliConfig) -> None:
    """Handle hosted deployment creation."""
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
    console().print()
    console().print(
        "Use a full active-artifact JSON file or the guided Docker image path.",
        style="dim",
    )
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
        console().print("Operation cancelled.", style="yellow")
