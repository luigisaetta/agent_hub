"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Tests for OCI Enterprise AI deployment menu command builders.
"""

import json
import subprocess

from enterprise_ai_deployment import menu
from enterprise_ai_deployment.menu import (
    ANSI_GREEN,
    HostedApplicationCreateRequest,
    HostedApplicationJsonOptions,
    HostedDeploymentCreateRequest,
    OciCliConfig,
    _style,
    build_create_hosted_application_command,
    build_create_hosted_deployment_command,
    build_get_hosted_application_command,
    build_get_hosted_deployment_command,
    build_list_compartments_by_name_command,
    build_list_hosted_applications_command,
    normalize_file_uri,
    resolve_compartment_id,
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


def test_build_list_hosted_applications_command_uses_compartment() -> None:
    """Hosted application listing targets a compartment and includes pagination."""
    command = build_list_hosted_applications_command(
        OciCliConfig(profile="PROD", region="eu-frankfurt-1"),
        "ocid1.compartment",
    )

    assert command == [
        "oci",
        "--profile",
        "PROD",
        "--region",
        "eu-frankfurt-1",
        "--output",
        "json",
        "generative-ai",
        "hosted-application-collection",
        "list-hosted-applications",
        "--compartment-id",
        "ocid1.compartment",
        "--all",
    ]


def test_build_list_compartments_by_name_command_searches_subtree() -> None:
    """Compartment name resolution searches the tenancy subtree."""
    command = build_list_compartments_by_name_command(
        OciCliConfig(profile="PROD", region="us-chicago-1"),
        "agent-demo",
    )

    assert command == [
        "oci",
        "--profile",
        "PROD",
        "--region",
        "us-chicago-1",
        "--output",
        "json",
        "iam",
        "compartment",
        "list",
        "--name",
        "agent-demo",
        "--compartment-id-in-subtree",
        "true",
        "--access-level",
        "ANY",
        "--include-root",
        "--all",
    ]


def test_resolve_compartment_id_keeps_ocid() -> None:
    """Existing compartment OCIDs do not trigger an OCI CLI lookup."""
    assert resolve_compartment_id(OciCliConfig(), "ocid1.compartment.oc1..abc") == (
        "ocid1.compartment.oc1..abc"
    )


def test_resolve_compartment_id_from_unique_name(monkeypatch) -> None:
    """A unique compartment name is resolved from OCI CLI JSON output."""

    def fake_run(command, **_kwargs):
        assert "compartment" in command
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "data": [
                        {
                            "name": "agent-demo",
                            "id": "ocid1.compartment.oc1..resolved",
                        }
                    ]
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(menu.subprocess, "run", fake_run)

    assert resolve_compartment_id(OciCliConfig(), "agent-demo") == (
        "ocid1.compartment.oc1..resolved"
    )


def test_resolve_compartment_id_raises_when_name_is_missing(monkeypatch) -> None:
    """An unknown compartment name produces a clear error."""

    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"data": []}),
            stderr="",
        )

    monkeypatch.setattr(menu.subprocess, "run", fake_run)

    try:
        resolve_compartment_id(OciCliConfig(), "missing")
    except RuntimeError as exc:
        assert "No compartment found" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


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


def test_style_can_be_forced_and_disabled(monkeypatch) -> None:
    """Menu styling can be forced, while NO_COLOR keeps plain text."""
    monkeypatch.setenv("AGENT_HUB_MENU_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)

    assert _style("OK", ANSI_GREEN) == "\033[32mOK\033[0m"

    monkeypatch.delenv("AGENT_HUB_MENU_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")

    assert _style("OK", ANSI_GREEN) == "OK"
