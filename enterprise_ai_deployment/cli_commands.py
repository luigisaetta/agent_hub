"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Pure OCI CLI command builders for Enterprise AI hosted applications and
    deployments.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from enterprise_ai_deployment.config import DEFAULT_WAIT_STATE, OciCliConfig


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
