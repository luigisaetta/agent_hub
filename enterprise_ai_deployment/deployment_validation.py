"""
Author: L. Saetta
Last modified: 2026-04-29
License: MIT

Description:
    Validation rules for declarative OCI Enterprise AI deployments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from enterprise_ai_deployment.config import COMPARTMENT_OCID_PREFIX
from enterprise_ai_deployment.deployment_config import DeploymentConfig

SENSITIVE_TOKENS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "client_secret",
    "authorization",
)
SUPPORTED_AUTH_TYPES = {"IDCS_AUTH_CONFIG", "NO_AUTH"}


class DeploymentValidationError(ValueError):
    """Raised when deployment configuration validation fails."""


def validate_deployment_config(config: DeploymentConfig) -> None:
    """Validate a loaded deployment configuration."""
    errors: list[str] = []

    if not config.application.compartment_id.startswith(COMPARTMENT_OCID_PREFIX):
        errors.append("application.compartment_id must be a compartment OCID.")
    if not config.application.region:
        errors.append("application.region is required.")
    if not config.application.region_key:
        errors.append("application.region_key is required.")

    dockerfile = _resolve_path(
        config.source_path, config.container.context, config.container.dockerfile
    )
    if not dockerfile.exists():
        errors.append(f"container.dockerfile does not exist: {dockerfile}")

    if config.container.tag_strategy not in {"git_sha", "timestamp", "explicit"}:
        errors.append(
            "container.tag_strategy must be one of: git_sha, timestamp, explicit."
        )
    if config.container.tag_strategy == "explicit" and not config.container.tag:
        errors.append("container.tag is required when tag_strategy is explicit.")

    _validate_security(config.hosted_application.security, errors)
    _validate_environment(config.hosted_application.environment, errors)

    if errors:
        raise DeploymentValidationError("\n".join(f"- {error}" for error in errors))


def _resolve_path(source_path: Path, context: str, dockerfile: str) -> Path:
    """Resolve Dockerfile relative to YAML location and build context."""
    base_dir = source_path.parent
    context_path = Path(context).expanduser()
    if not context_path.is_absolute():
        context_path = base_dir / context_path
    dockerfile_path = Path(dockerfile).expanduser()
    if dockerfile_path.is_absolute():
        return dockerfile_path
    return context_path / dockerfile_path


def _validate_security(security: dict[str, Any], errors: list[str]) -> None:
    """Validate supported inbound auth settings."""
    auth_type = str(security.get("auth_type", "NO_AUTH")).upper()
    if auth_type not in SUPPORTED_AUTH_TYPES:
        errors.append(
            "hosted_application.security.auth_type must be one of: "
            "IDCS_AUTH_CONFIG, NO_AUTH."
        )
        return
    if auth_type == "NO_AUTH":
        return
    for field_name in ("issuer_url", "audience"):
        if not str(security.get(field_name, "")).strip():
            errors.append(
                "hosted_application.security."
                f"{field_name} is required for IDCS_AUTH_CONFIG."
            )
    scopes = security.get("scopes")
    if not isinstance(scopes, list) or not any(str(scope).strip() for scope in scopes):
        errors.append(
            "hosted_application.security.scopes must contain at least one "
            "scope for IDCS_AUTH_CONFIG."
        )


def _validate_environment(environment: dict[str, Any], errors: list[str]) -> None:
    """Validate environment variables and secret references."""
    variables = environment.get("variables", {})
    if variables is not None and not isinstance(variables, dict):
        errors.append("hosted_application.environment.variables must be a mapping.")
    if isinstance(variables, dict):
        for name, value in variables.items():
            if _looks_sensitive(str(name)):
                errors.append(
                    "hosted_application.environment.variables must not contain "
                    f"sensitive-looking key {name!r}; use secrets instead."
                )
            if isinstance(value, str) and _looks_like_hardcoded_secret(
                str(name), value
            ):
                errors.append(
                    "hosted_application.environment.variables."
                    f"{name} looks like a hardcoded secret."
                )

    secrets = environment.get("secrets", {})
    if secrets is None:
        return
    if not isinstance(secrets, dict):
        errors.append("hosted_application.environment.secrets must be a mapping.")
        return
    for secret_name, secret_config in secrets.items():
        if not isinstance(secret_config, dict):
            errors.append(
                "hosted_application.environment.secrets."
                f"{secret_name} must reference a secret source."
            )
            continue
        source = str(secret_config.get("source", "")).lower()
        if source == "vault":
            if not str(secret_config.get("secret_ocid", "")).startswith("ocid1."):
                errors.append(
                    "hosted_application.environment.secrets."
                    f"{secret_name}.secret_ocid is required."
                )
        elif source == "local_env":
            env_name = str(secret_config.get("env_name", "")).strip()
            if not env_name:
                errors.append(
                    "hosted_application.environment.secrets."
                    f"{secret_name}.env_name is required."
                )
            elif env_name not in os.environ:
                errors.append(
                    f"local_env secret {secret_name!r} references missing "
                    f"environment variable {env_name!r}."
                )
        else:
            errors.append(
                "hosted_application.environment.secrets."
                f"{secret_name}.source must be vault or local_env."
            )


def _looks_sensitive(name: str) -> bool:
    """Return True for names that should be represented as secret references."""
    lowered = name.lower()
    return any(token in lowered for token in SENSITIVE_TOKENS)


def _looks_like_hardcoded_secret(name: str, value: str) -> bool:
    """Detect obvious secret-like inline values."""
    if _looks_sensitive(name):
        return True
    stripped = value.strip()
    return (
        len(stripped) >= 24
        and " " not in stripped
        and not stripped.startswith("ocid1.")
    )
