"""
Author: L. Saetta
Last modified: 2026-04-29
License: MIT

Description:
    Render OCI CLI JSON artifacts from declarative deployment YAML.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from enterprise_ai_deployment.deployment_config import DeploymentConfig
from enterprise_ai_deployment.ocir import ImageReference


@dataclass(frozen=True)
class RenderedArtifacts:
    """Paths to generated OCI CLI JSON artifacts."""

    hosted_application_create: Path
    hosted_deployment_create: Path
    scaling_config: Path | None = None
    inbound_auth_config: Path | None = None
    networking_config: Path | None = None
    environment_variables: Path | None = None
    active_artifact: Path | None = None


def render_artifacts(
    config: DeploymentConfig,
    image_reference: ImageReference,
    output_dir: str | Path,
) -> RenderedArtifacts:
    """Render all JSON artifacts needed by the first deployment flow."""
    target_dir = Path(output_dir).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)

    scaling_path = _write_optional_json(
        target_dir / "hosted-application-scaling-config.json",
        _render_scaling(config.hosted_application.scaling),
    )
    auth_path = _write_optional_json(
        target_dir / "hosted-application-inbound-auth-config.json",
        _render_inbound_auth(config.hosted_application.security),
    )
    networking_path = _write_optional_json(
        target_dir / "hosted-application-networking-config.json",
        _render_networking(config.hosted_application.networking),
    )
    environment_path = _write_optional_json(
        target_dir / "hosted-application-environment-variables.json",
        _render_environment(config.hosted_application.environment),
    )
    active_artifact_path = _write_json(
        target_dir / "hosted-deployment-active-artifact.json",
        _render_active_artifact(image_reference),
    )

    hosted_application_payload = _render_hosted_application_payload(
        config,
        scaling_path,
        auth_path,
        networking_path,
        environment_path,
    )
    hosted_deployment_payload = _render_hosted_deployment_payload(
        config,
        image_reference,
        active_artifact_path,
    )

    return RenderedArtifacts(
        hosted_application_create=_write_json(
            target_dir / "create-hosted-application.json", hosted_application_payload
        ),
        hosted_deployment_create=_write_json(
            target_dir / "create-hosted-deployment.json", hosted_deployment_payload
        ),
        scaling_config=scaling_path,
        inbound_auth_config=auth_path,
        networking_config=networking_path,
        environment_variables=environment_path,
        active_artifact=active_artifact_path,
    )


def _render_hosted_application_payload(
    config: DeploymentConfig,
    scaling_path: Path | None,
    auth_path: Path | None,
    networking_path: Path | None,
    environment_path: Path | None,
) -> dict[str, Any]:
    """Render a command-oriented Hosted Application payload summary."""
    payload: dict[str, Any] = {
        "displayName": config.hosted_application.display_name,
        "compartmentId": config.application.compartment_id,
        "createIfMissing": config.hosted_application.create_if_missing,
        "updateIfExists": config.hosted_application.update_if_exists,
    }
    if config.hosted_application.description:
        payload["description"] = config.hosted_application.description
    json_files = {
        "scalingConfig": scaling_path,
        "inboundAuthConfig": auth_path,
        "networkingConfig": networking_path,
        "environmentVariables": environment_path,
    }
    payload["jsonFiles"] = {
        key: str(path) for key, path in json_files.items() if path is not None
    }
    return payload


def _render_hosted_deployment_payload(
    config: DeploymentConfig,
    image_reference: ImageReference,
    active_artifact_path: Path,
) -> dict[str, Any]:
    """Render a command-oriented Hosted Deployment payload summary."""
    return {
        "displayName": config.hosted_deployment.display_name,
        "compartmentId": config.application.compartment_id,
        "activeArtifact": str(active_artifact_path),
        "containerUri": image_reference.container_uri,
        "artifactTag": image_reference.tag,
        "imageUri": image_reference.image_uri,
        "createNewVersion": config.hosted_deployment.create_new_version,
        "activate": config.hosted_deployment.activate,
        "waitForState": config.hosted_deployment.wait_for_state,
    }


def _render_scaling(scaling: dict[str, Any]) -> dict[str, Any] | None:
    """Render Hosted Application scaling config."""
    if not scaling:
        return None
    scaling_type = str(scaling.get("metric", "cpu")).upper()
    if scaling_type == "RPS":
        scaling_type = "REQUESTS_PER_SECOND"
    return {
        "minReplica": scaling.get("min_instances"),
        "maxReplica": scaling.get("max_instances"),
        "scalingType": scaling_type,
        "targetCpuThreshold": scaling.get("target_cpu_threshold"),
        "targetMemoryThreshold": scaling.get("target_memory_threshold"),
        "targetConcurrencyThreshold": scaling.get("target_concurrency_threshold"),
        "targetRpsThreshold": scaling.get("target_rps_threshold"),
    }


def _render_inbound_auth(security: dict[str, Any]) -> dict[str, Any] | None:
    """Render Hosted Application inbound auth config."""
    if not security:
        return None
    auth_type = str(security.get("auth_type", "NO_AUTH")).upper()
    if auth_type == "NO_AUTH":
        return None
    return {
        "inboundAuthConfigType": auth_type,
        "idcsConfig": {
            "domainUrl": security.get("issuer_url"),
            "audience": security.get("audience"),
            "scope": _render_scope(security.get("scopes", [])),
        },
    }


def _render_networking(networking: dict[str, Any]) -> dict[str, Any] | None:
    """Render Hosted Application networking config."""
    if not networking:
        return None
    endpoint_mode = str(networking.get("mode", "public")).upper()
    outbound_mode = str(networking.get("outbound_mode", "managed")).upper()
    return {
        "inboundNetworkingConfig": {
            "endpointMode": endpoint_mode,
            "privateEndpointId": networking.get("private_endpoint_id"),
        },
        "outboundNetworkingConfig": {
            "networkMode": outbound_mode,
            "customSubnetId": networking.get("custom_subnet_id"),
            "nsgIds": networking.get("nsg_ids"),
        },
    }


def _render_environment(environment: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Render environment variables with the OCI CLI list shape."""
    if not environment:
        return None
    variables = environment.get("variables", {}) or {}
    secrets = environment.get("secrets", {}) or {}
    payload: list[dict[str, Any]] = [
        {"name": str(name), "type": "PLAINTEXT", "value": str(value)}
        for name, value in variables.items()
    ]
    for name, secret_config in secrets.items():
        source = str(secret_config.get("source", "")).upper()
        if source == "VAULT":
            payload.append(
                {
                    "name": str(name),
                    "type": "VAULT",
                    "value": secret_config.get("secret_ocid"),
                }
            )
    return payload


def _render_scope(scopes: Any) -> str:
    """Render OCI IDCS scope as the single string expected by the CLI."""
    if isinstance(scopes, list):
        return " ".join(str(scope) for scope in scopes if str(scope).strip())
    return str(scopes)


def _render_active_artifact(image_reference: ImageReference) -> dict[str, Any]:
    """Render Hosted Deployment Docker artifact config."""
    return {
        "artifactType": "SIMPLE_DOCKER_ARTIFACT",
        "containerUri": image_reference.container_uri,
        "tag": image_reference.tag,
    }


def _write_optional_json(
    path: Path, payload: dict[str, Any] | list[dict[str, Any]] | None
) -> Path | None:
    """Write JSON only when a payload is present."""
    if payload is None:
        return None
    return _write_json(path, payload)


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> Path:
    """Write formatted JSON to disk."""
    path.write_text(
        json.dumps(_drop_none_values(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _drop_none_values(value: Any) -> Any:
    """Remove None values recursively from generated JSON."""
    if isinstance(value, dict):
        return {
            key: _drop_none_values(child)
            for key, child in value.items()
            if child is not None
        }
    if isinstance(value, list):
        return [_drop_none_values(child) for child in value]
    return value
