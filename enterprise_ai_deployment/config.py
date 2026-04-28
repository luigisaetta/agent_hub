"""
Author: L. Saetta
Last modified: 2026-04-28
License: MIT

Description:
    Configuration helpers for the OCI Enterprise AI deployment menu.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MENU_WIDTH = 96
DEFAULT_WAIT_STATE = "SUCCEEDED"
COMPARTMENT_OCID_PREFIX = "ocid1.compartment."


@dataclass(frozen=True)
class OciCliConfig:
    """Global OCI CLI options shared by all menu operations."""

    profile: str | None = None
    region: str | None = None
    compartment_id: str | None = None
    output: str = "json"


def env(name: str) -> str | None:
    """Return a stripped environment value or None."""
    value = os.getenv(name, "").strip()
    return value or None


def load_config_from_env() -> OciCliConfig:
    """Load optional OCI CLI defaults from environment variables."""
    return OciCliConfig(
        profile=env("OCI_CLI_PROFILE") or env("OCI_PROFILE"),
        region=env("OCI_CLI_REGION") or env("OCI_REGION"),
        compartment_id=env("OCI_COMPARTMENT_ID") or env("COMPARTMENT_ID"),
        output=env("OCI_CLI_OUTPUT") or "json",
    )
