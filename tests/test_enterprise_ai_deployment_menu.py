"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Tests for OCI Enterprise AI deployment menu command builders.
"""

from enterprise_ai_deployment.menu import (
    HostedApplicationCreateRequest,
    HostedApplicationJsonOptions,
    HostedDeploymentCreateRequest,
    OciCliConfig,
    build_create_hosted_application_command,
    build_create_hosted_deployment_command,
    build_get_hosted_application_command,
    build_get_hosted_deployment_command,
    normalize_file_uri,
)


def test_build_get_hosted_application_command_includes_global_options() -> None:
    """The hosted application get command includes profile and region."""
    config = OciCliConfig(profile="PROD", region="us-chicago-1")

    command = build_get_hosted_application_command(config, "ocid1.hostedapp")

    assert command == [
        "oci",
        "--profile",
        "PROD",
        "--region",
        "us-chicago-1",
        "--output",
        "json",
        "generative-ai",
        "hosted-application",
        "get",
        "--hosted-application-id",
        "ocid1.hostedapp",
    ]


def test_build_get_hosted_deployment_command() -> None:
    """The hosted deployment get command targets the expected OCI CLI group."""
    command = build_get_hosted_deployment_command(
        OciCliConfig(output="table"), "ocid1.deployment"
    )

    assert command == [
        "oci",
        "--output",
        "table",
        "generative-ai",
        "hosted-deployment",
        "get",
        "--hosted-deployment-id",
        "ocid1.deployment",
    ]


def test_create_hosted_application_command_adds_optional_json_files() -> None:
    """Hosted application creation accepts optional JSON file parameters."""
    command = build_create_hosted_application_command(
        OciCliConfig(),
        HostedApplicationCreateRequest(
            display_name="my-app",
            compartment_id="ocid1.compartment",
            description="demo",
            json_options=HostedApplicationJsonOptions(
                scaling_config="scaling.json",
                environment_variables="file://env.json",
            ),
            wait=True,
        ),
    )

    assert command == [
        "oci",
        "--output",
        "json",
        "generative-ai",
        "hosted-application",
        "create",
        "--display-name",
        "my-app",
        "--compartment-id",
        "ocid1.compartment",
        "--description",
        "demo",
        "--scaling-config",
        "file://scaling.json",
        "--environment-variables",
        "file://env.json",
        "--wait-for-state",
        "SUCCEEDED",
    ]


def test_create_hosted_deployment_command_uses_single_docker_shortcut() -> None:
    """Docker guided mode uses the dedicated OCI CLI shortcut command."""
    command = build_create_hosted_deployment_command(
        OciCliConfig(),
        HostedDeploymentCreateRequest(
            hosted_application_id="ocid1.app",
            display_name="v1",
            compartment_id="ocid1.compartment",
            container_uri="iad.ocir.io/ns/repo/app",
            artifact_tag="latest",
            wait=False,
        ),
    )

    assert command == [
        "oci",
        "--output",
        "json",
        "generative-ai",
        "hosted-deployment",
        "create-hosted-deployment-single-docker-artifact",
        "--hosted-application-id",
        "ocid1.app",
        "--active-artifact-container-uri",
        "iad.ocir.io/ns/repo/app",
        "--active-artifact-tag",
        "latest",
        "--display-name",
        "v1",
        "--compartment-id",
        "ocid1.compartment",
    ]


def test_create_hosted_deployment_command_accepts_active_artifact_json() -> None:
    """Advanced deployment creation can pass a full active-artifact JSON."""
    command = build_create_hosted_deployment_command(
        OciCliConfig(),
        HostedDeploymentCreateRequest(
            hosted_application_id="ocid1.app",
            active_artifact_json="artifact.json",
        ),
    )

    assert "--active-artifact" in command
    assert "file://artifact.json" in command
    assert "create-hosted-deployment-single-docker-artifact" not in command


def test_normalize_file_uri_keeps_existing_file_uri() -> None:
    """Existing file URIs are preserved."""
    assert normalize_file_uri("file://payload.json") == "file://payload.json"
