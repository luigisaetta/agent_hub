"""
Author: L. Saetta
Last modified: 2026-04-29
License: MIT

Description:
    YAML and environment loading for the OCI Enterprise AI deployment CLI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class DeploymentConfigError(ValueError):
    """Raised when the deployment configuration cannot be loaded."""


@dataclass(frozen=True)
class ApplicationConfig:
    """Top-level application identity and OCI region settings."""

    name: str
    compartment_id: str
    region: str
    region_key: str


@dataclass(frozen=True)
class ContainerConfig:
    """Container build and OCIR publication settings."""

    context: str
    dockerfile: str
    image_name: str
    repository: str
    tag_strategy: str
    ocir_namespace: str
    tag: str | None = None


@dataclass(frozen=True)
class HostedApplicationConfig:  # pylint: disable=too-many-instance-attributes
    """Hosted Application settings rendered for OCI CLI."""

    display_name: str
    description: str | None = None
    create_if_missing: bool = True
    update_if_exists: bool = False
    scaling: dict[str, Any] = field(default_factory=dict)
    networking: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HostedDeploymentConfig:
    """Hosted Deployment settings rendered for OCI CLI."""

    display_name: str
    create_new_version: bool = True
    activate: bool = True
    wait_for_state: str | None = "SUCCEEDED"


@dataclass(frozen=True)
class DeploymentConfig:
    """Complete deployment configuration read from YAML."""

    application: ApplicationConfig
    container: ContainerConfig
    hosted_application: HostedApplicationConfig
    hosted_deployment: HostedDeploymentConfig
    source_path: Path


def load_deployment_config(
    path: str | Path, env_file: str | Path | None = None
) -> DeploymentConfig:
    """Load deployment YAML and optional local .env references."""
    config_path = Path(path).expanduser()
    if not config_path.exists():
        raise DeploymentConfigError(f"Configuration file not found: {config_path}")
    if env_file:
        env_path = Path(env_file).expanduser()
        if not env_path.exists():
            raise DeploymentConfigError(f"Environment file not found: {env_path}")
        load_dotenv(env_path, override=False)

    try:
        with config_path.open("r", encoding="utf-8") as file_handle:
            raw_config = yaml.safe_load(file_handle)
    except yaml.YAMLError as exc:
        raise DeploymentConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise DeploymentConfigError(
            "Deployment YAML must contain a mapping at the top level."
        )

    return _parse_deployment_config(raw_config, config_path)


def _parse_deployment_config(
    raw_config: dict[str, Any], source_path: Path
) -> DeploymentConfig:
    """Convert a raw YAML mapping into typed configuration objects."""
    application = _required_mapping(raw_config, "application")
    container = _required_mapping(raw_config, "container")
    hosted_application = _required_mapping(raw_config, "hosted_application")
    hosted_deployment = _required_mapping(raw_config, "hosted_deployment")

    return DeploymentConfig(
        application=ApplicationConfig(
            name=_required_text(application, "name"),
            compartment_id=_required_text(application, "compartment_id"),
            region=_required_text(application, "region"),
            region_key=_required_text(application, "region_key"),
        ),
        container=ContainerConfig(
            context=_required_text(container, "context"),
            dockerfile=_required_text(container, "dockerfile"),
            image_name=_required_text(container, "image_name"),
            repository=_required_text(container, "repository"),
            tag_strategy=_required_text(container, "tag_strategy"),
            ocir_namespace=_required_text(container, "ocir_namespace"),
            tag=_optional_text(container, "tag"),
        ),
        hosted_application=HostedApplicationConfig(
            display_name=_required_text(hosted_application, "display_name"),
            description=_optional_text(hosted_application, "description"),
            create_if_missing=bool(hosted_application.get("create_if_missing", True)),
            update_if_exists=bool(hosted_application.get("update_if_exists", False)),
            scaling=_optional_mapping(hosted_application, "scaling"),
            networking=_optional_mapping(hosted_application, "networking"),
            security=_optional_mapping(hosted_application, "security"),
            environment=_optional_mapping(hosted_application, "environment"),
        ),
        hosted_deployment=HostedDeploymentConfig(
            display_name=_required_text(hosted_deployment, "display_name"),
            create_new_version=bool(hosted_deployment.get("create_new_version", True)),
            activate=bool(hosted_deployment.get("activate", True)),
            wait_for_state=_optional_text(hosted_deployment, "wait_for_state"),
        ),
        source_path=source_path,
    )


def _required_mapping(parent: dict[str, Any], key: str) -> dict[str, Any]:
    """Read a required child mapping."""
    value = parent.get(key)
    if not isinstance(value, dict):
        raise DeploymentConfigError(f"Missing or invalid mapping: {key}")
    return value


def _optional_mapping(parent: dict[str, Any], key: str) -> dict[str, Any]:
    """Read an optional child mapping."""
    value = parent.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DeploymentConfigError(f"Invalid mapping: {key}")
    return value


def _required_text(parent: dict[str, Any], key: str) -> str:
    """Read a required non-empty string-like value."""
    value = parent.get(key)
    if value is None or str(value).strip() == "":
        raise DeploymentConfigError(f"Missing required field: {key}")
    return str(value).strip()


def _optional_text(parent: dict[str, Any], key: str) -> str | None:
    """Read an optional non-empty string-like value."""
    value = parent.get(key)
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()
