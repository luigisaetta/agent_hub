"""
Author: L. Saetta
Last modified: 2026-04-29
License: MIT

Description:
    OCIR image tag and URI helpers for Enterprise AI deployments.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime

from enterprise_ai_deployment.deployment_config import DeploymentConfig


@dataclass(frozen=True)
class ImageReference:
    """Calculated image reference values."""

    container_uri: str
    tag: str

    @property
    def image_uri(self) -> str:
        """Return the complete image URI including tag."""
        return f"{self.container_uri}:{self.tag}"


def build_image_reference(
    config: DeploymentConfig, namespace: str | None = None
) -> ImageReference:
    """Build the OCIR image URI and tag from deployment configuration."""
    resolved_namespace = namespace or config.container.ocir_namespace
    if resolved_namespace == "auto":
        resolved_namespace = "<resolved-ocir-namespace>"
    tag = resolve_image_tag(config)
    container_uri = (
        f"{config.application.region_key}.ocir.io/"
        f"{resolved_namespace}/{config.container.repository}/{config.container.image_name}"
    )
    return ImageReference(container_uri=container_uri, tag=tag)


def resolve_image_tag(config: DeploymentConfig) -> str:
    """Resolve the Docker image tag strategy."""
    if config.container.tag:
        return config.container.tag
    if config.container.tag_strategy == "timestamp":
        return datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    if config.container.tag_strategy == "git_sha":
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return "unknown-git-sha"
    return config.container.tag_strategy
