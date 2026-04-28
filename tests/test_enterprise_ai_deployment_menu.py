"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Tests for OCI Enterprise AI deployment menu command builders.
"""

import json
import subprocess

from enterprise_ai_deployment import workflows
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
from enterprise_ai_deployment.config import OciCliConfig
from enterprise_ai_deployment.rendering import show_hosted_applications
from enterprise_ai_deployment.workflows import (
    build_get_hosted_application_command_from_list,
    clear_compartment_cache,
    run_hosted_application_details,
    run_hosted_applications_list,
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
    clear_compartment_cache()

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

    monkeypatch.setattr(workflows.subprocess, "run", fake_run)

    assert resolve_compartment_id(OciCliConfig(), "agent-demo") == (
        "ocid1.compartment.oc1..resolved"
    )


def test_resolve_compartment_id_raises_when_name_is_missing(monkeypatch) -> None:
    """An unknown compartment name produces a clear error."""
    clear_compartment_cache()

    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"data": []}),
            stderr="",
        )

    monkeypatch.setattr(workflows.subprocess, "run", fake_run)

    try:
        resolve_compartment_id(OciCliConfig(), "missing")
    except RuntimeError as exc:
        assert "No compartment found" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_resolve_compartment_id_uses_session_cache(monkeypatch) -> None:
    """Repeated compartment name resolution reuses the in-memory cache."""
    clear_compartment_cache()
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "data": [
                        {
                            "name": "agent-demo",
                            "id": "ocid1.compartment.oc1..cached",
                        }
                    ]
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(workflows.subprocess, "run", fake_run)

    config = OciCliConfig(profile="PROD", region="us-chicago-1")

    assert resolve_compartment_id(config, "agent-demo") == (
        "ocid1.compartment.oc1..cached"
    )
    assert resolve_compartment_id(config, "agent-demo") == (
        "ocid1.compartment.oc1..cached"
    )
    assert len(calls) == 1


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


def test_show_hosted_applications_includes_description(capsys) -> None:
    """Hosted applications table includes a description column."""
    show_hosted_applications(
        [
            {
                "display-name": "demo-app",
                "lifecycle-state": "ACTIVE",
                "time-created": "2026-04-28T10:00:00Z",
                "description": "Demo hosted application",
                "id": "ocid1.hostedapp",
            }
        ]
    )

    captured = capsys.readouterr()

    assert "Description" in captured.out
    assert "Demo hosted application" in captured.out


def test_hosted_applications_list_raw_json_is_optional(monkeypatch, capsys) -> None:
    """Hosted application listing does not print raw JSON unless requested."""
    payload = {
        "data": [
            {
                "display-name": "demo-app",
                "lifecycle-state": "ACTIVE",
                "description": "Demo hosted application",
                "id": "ocid1.hostedapp",
            }
        ]
    }

    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(workflows.subprocess, "run", fake_run)
    monkeypatch.setattr(workflows, "confirm", lambda *_args, **_kwargs: False)

    run_hosted_applications_list(["oci", "generative-ai"])

    captured = capsys.readouterr()

    assert "Hosted Applications" in captured.out
    assert "Raw JSON" not in captured.out


def test_build_get_hosted_application_command_from_list_reuses_global_options() -> None:
    """A selected hosted application can reuse list command global options."""
    command = build_get_hosted_application_command_from_list(
        [
            "oci",
            "--profile",
            "PROD",
            "--region",
            "us-chicago-1",
            "--output",
            "json",
            "generative-ai",
            "hosted-application-collection",
            "list-hosted-applications",
        ],
        "ocid1.hostedapp",
    )

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


def test_hosted_application_details_render_table_without_raw_json(
    monkeypatch, capsys
) -> None:
    """Hosted application details render as a table and raw JSON is optional."""
    payload = {
        "data": {
            "display-name": "demo-app",
            "lifecycle-state": "ACTIVE",
            "description": "Demo hosted application",
            "id": "ocid1.hostedapp",
        }
    }

    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(workflows.subprocess, "run", fake_run)
    monkeypatch.setattr(workflows, "confirm", lambda *_args, **_kwargs: False)

    run_hosted_application_details(["oci", "generative-ai"])

    captured = capsys.readouterr()

    assert "Hosted Application Details" in captured.out
    assert "Demo hosted application" in captured.out
    assert "Raw JSON" not in captured.out


def test_hosted_applications_list_can_open_selected_details(
    monkeypatch, capsys
) -> None:
    """After listing hosted applications, a selected item can show details."""
    calls = []
    list_payload = {
        "data": [
            {
                "display-name": "demo-app",
                "lifecycle-state": "ACTIVE",
                "id": "ocid1.hostedapp",
            }
        ]
    }
    details_payload = {
        "data": {
            "display-name": "demo-app",
            "lifecycle-state": "ACTIVE",
            "description": "Selected details",
            "id": "ocid1.hostedapp",
        }
    }

    def fake_run(command, **_kwargs):
        calls.append(command)
        payload = details_payload if "get" in command else list_payload
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload),
            stderr="",
        )

    confirm_answers = iter([False, True, False])

    monkeypatch.setattr(workflows.subprocess, "run", fake_run)
    monkeypatch.setattr(
        workflows,
        "confirm",
        lambda *_args, **_kwargs: next(confirm_answers),
    )
    monkeypatch.setattr(workflows, "prompt", lambda *_args, **_kwargs: "1")

    run_hosted_applications_list(
        [
            "oci",
            "--region",
            "us-chicago-1",
            "--output",
            "json",
            "generative-ai",
            "hosted-application-collection",
            "list-hosted-applications",
        ]
    )

    captured = capsys.readouterr()

    assert len(calls) == 2
    assert "Hosted Application Details" in captured.out
    assert "Selected details" in captured.out
