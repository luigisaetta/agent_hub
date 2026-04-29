"""
Author: L. Saetta
Last modified: 2026-04-29
License: MIT

Description:
    Tests for the non-interactive OCI Enterprise AI deployment CLI.
"""

from __future__ import annotations

import json
import subprocess

from enterprise_ai_deployment.deployment_config import load_deployment_config
from enterprise_ai_deployment.deployment_renderer import render_artifacts
from enterprise_ai_deployment.deployment_runner import format_command, main
from enterprise_ai_deployment.deployment_validation import (
    DeploymentValidationError,
    validate_deployment_config,
)
from enterprise_ai_deployment.ocir import ImageReference, build_image_reference


def test_load_deployment_config_reads_yaml_and_env_file(tmp_path, monkeypatch) -> None:
    """Deployment YAML is parsed and local_env references can come from .env."""
    monkeypatch.delenv("MY_AGENT_API_KEY", raising=False)
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM python:3.11-slim\n", encoding="utf-8")
    config_path = tmp_path / "deploy.yaml"
    env_path = tmp_path / ".env"
    env_path.write_text("MY_AGENT_API_KEY=local-secret-value\n", encoding="utf-8")
    config_path.write_text(_valid_yaml(tmp_path), encoding="utf-8")

    config = load_deployment_config(config_path, env_file=env_path)

    assert config.application.name == "demo-agent"
    assert config.hosted_application.environment["secrets"]["API_KEY"]["env_name"] == (
        "MY_AGENT_API_KEY"
    )
    validate_deployment_config(config)


def test_render_artifacts_do_not_write_local_secret_values(
    tmp_path, monkeypatch
) -> None:
    """Generated JSON contains secret references but not clear-text local secrets."""
    monkeypatch.setenv("MY_AGENT_API_KEY", "super-secret-local-value")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
    config_path = tmp_path / "deploy.yaml"
    config_path.write_text(_valid_yaml(tmp_path), encoding="utf-8")
    config = load_deployment_config(config_path)

    artifacts = render_artifacts(
        config,
        ImageReference(
            container_uri="fra.ocir.io/ns/ai-agents/demo-agent",
            tag="abc1234",
        ),
        tmp_path / "generated",
    )

    environment_payload = json.loads(
        artifacts.environment_variables.read_text(encoding="utf-8")
    )
    auth_payload = json.loads(artifacts.inbound_auth_config.read_text(encoding="utf-8"))
    scaling_payload = json.loads(artifacts.scaling_config.read_text(encoding="utf-8"))
    networking_payload = json.loads(
        artifacts.networking_config.read_text(encoding="utf-8")
    )
    artifact_payload = json.loads(artifacts.active_artifact.read_text(encoding="utf-8"))
    deployment_payload = json.loads(
        artifacts.hosted_deployment_create.read_text(encoding="utf-8")
    )

    assert {
        "name": "LOG_LEVEL",
        "type": "PLAINTEXT",
        "value": "INFO",
    } in environment_payload
    assert all(item["name"] != "API_KEY" for item in environment_payload)
    assert auth_payload["inboundAuthConfigType"] == "IDCS_AUTH_CONFIG"
    assert auth_payload["idcsConfig"]["scope"] == "demo-agent/.default"
    assert "jwksUrl" not in auth_payload
    assert scaling_payload["minReplica"] == 1
    assert scaling_payload["maxReplica"] == 2
    assert scaling_payload["scalingType"] == "CPU"
    assert networking_payload["inboundNetworkingConfig"]["endpointMode"] == "PUBLIC"
    assert networking_payload["outboundNetworkingConfig"]["networkMode"] == "MANAGED"
    assert artifact_payload == {
        "artifactType": "SIMPLE_DOCKER_ARTIFACT",
        "containerUri": "fra.ocir.io/ns/ai-agents/demo-agent",
        "tag": "abc1234",
    }
    assert "super-secret-local-value" not in artifacts.environment_variables.read_text(
        encoding="utf-8"
    )
    assert (
        deployment_payload["imageUri"] == "fra.ocir.io/ns/ai-agents/demo-agent:abc1234"
    )


def test_build_image_reference_uses_explicit_tag(tmp_path, monkeypatch) -> None:
    """Explicit tags build stable OCIR image references."""
    monkeypatch.setenv("MY_AGENT_API_KEY", "local-secret-value")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
    config_path = tmp_path / "deploy.yaml"
    config_path.write_text(_valid_yaml(tmp_path), encoding="utf-8")
    config = load_deployment_config(config_path)

    image_reference = build_image_reference(config, namespace="mytenancy")

    assert image_reference.container_uri == "fra.ocir.io/mytenancy/ai-agents/demo-agent"
    assert image_reference.tag == "20260429"
    assert (
        image_reference.image_uri
        == "fra.ocir.io/mytenancy/ai-agents/demo-agent:20260429"
    )


def test_validate_rejects_unsupported_auth_type(tmp_path, monkeypatch) -> None:
    """Only OCI-supported auth types are accepted."""
    monkeypatch.setenv("MY_AGENT_API_KEY", "local-secret-value")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
    config_path = tmp_path / "deploy.yaml"
    config_path.write_text(
        _valid_yaml(tmp_path).replace("IDCS_AUTH_CONFIG", "oauth2"),
        encoding="utf-8",
    )
    config = load_deployment_config(config_path)

    try:
        validate_deployment_config(config)
    except DeploymentValidationError as exc:
        assert "IDCS_AUTH_CONFIG, NO_AUTH" in str(exc)
    else:
        raise AssertionError("Expected DeploymentValidationError")


def test_create_application_dry_run_renders_command(
    tmp_path, monkeypatch, capsys
) -> None:
    """Dry-run create-application renders artifacts and never calls OCI CLI."""
    monkeypatch.setenv("MY_AGENT_API_KEY", "local-secret-value")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
    config_path = tmp_path / "deploy.yaml"
    config_path.write_text(_valid_yaml(tmp_path), encoding="utf-8")

    def fail_run(*_args, **_kwargs):
        raise AssertionError("subprocess.run must not be called in dry-run mode")

    monkeypatch.setattr(subprocess, "run", fail_run)

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--output-dir",
            str(tmp_path / "generated"),
            "--dry-run",
            "create-application",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "\nOCI CLI command:\n\noci " in captured.out
    assert "--wait-for-state SUCCEEDED\n\nDry run" in captured.out
    assert "hosted-application create" in captured.out
    assert "Dry run: command not executed." in captured.out


def test_cli_help_lists_required_commands(capsys) -> None:
    """CLI help exposes the first supported command set."""
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()

    assert "create-application" in captured.out
    assert "create-deployment" in captured.out
    assert "--env-file" in captured.out


def test_format_command_quotes_description_with_comma_and_spaces() -> None:
    """Displayed commands remain copy/paste-safe for descriptive text."""
    command = [
        "oci",
        "generative-ai",
        "hosted-application",
        "create",
        "--description",
        "Agent application, test 01",
    ]

    formatted = format_command(command)

    assert "--description 'Agent application, test 01'" in formatted


def _valid_yaml(tmp_path) -> str:
    """Return a minimal valid deployment YAML."""
    return f"""
application:
  name: demo-agent
  compartment_id: ocid1.compartment.oc1..example
  region: eu-frankfurt-1
  region_key: fra

container:
  context: {tmp_path}
  dockerfile: Dockerfile
  image_name: demo-agent
  repository: ai-agents
  tag_strategy: explicit
  tag: "20260429"
  ocir_namespace: auto

hosted_application:
  display_name: demo-agent
  description: Demo agent
  create_if_missing: true
  update_if_exists: false
  scaling:
    min_instances: 1
    max_instances: 2
    metric: cpu
  networking:
    mode: public
  security:
    auth_type: IDCS_AUTH_CONFIG
    issuer_url: https://issuer.example.com
    audience: demo-agent
    scopes:
      - demo-agent/.default
  environment:
    variables:
      LOG_LEVEL: INFO
      MCP_SERVER_PORT: "8080"
    secrets:
      API_KEY:
        source: local_env
        env_name: MY_AGENT_API_KEY

hosted_deployment:
  display_name: demo-agent-deployment
  create_new_version: true
  activate: true
  wait_for_state: SUCCEEDED
"""
