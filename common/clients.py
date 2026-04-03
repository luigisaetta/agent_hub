"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Shared client builders used across examples and connector scripts.

    The code available here covers also Control Plane client construction, which requires OCI authentication.
    The authentication mode can be selected via the OCI_AUTH_MODE environment variable, which can be set
    in the .env files used for examples and connectors. Two modes are supported: user_principal and session.
"""

from __future__ import annotations

import os
from typing import Callable, Any, Literal, Mapping

import httpx
from oci import config as oci_config
from oci.auth.signers import SecurityTokenSigner
from oci.generative_ai import GenerativeAiClient
from oci.signer import load_private_key_from_file
from openai import OpenAI

from oci_genai_auth import OciSessionAuth, OciUserPrincipalAuth

from config import BASE_URL, CP_BASE_URL, REGION
from config_private import COMPARTMENT_ID, KEY1, PROJECT_ID

PROFILE = "DEFAULT"
AUTH_MODE_ENV_VAR = "OCI_AUTH_MODE"


def validate_oci_auth_config(
    *,
    config: Mapping[str, Any],
    auth_mode: Literal["session", "user_principal"],
    profile: str = PROFILE,
) -> None:
    """Validate profile config coherence for the selected auth mode."""
    if auth_mode == "session":
        if not config.get("security_token_file") or not config.get("key_file"):
            raise ValueError(
                f"OCI profile '{profile}' is not valid for session auth: "
                "missing 'security_token_file' and/or 'key_file'."
            )
        return

    missing = [key for key in ("user", "tenancy", "fingerprint") if not config.get(key)]
    if missing:
        missing_keys = ", ".join(missing)
        raise ValueError(
            f"OCI profile '{profile}' is not valid for user_principal auth: "
            f"missing required key(s): {missing_keys}."
        )
    if not config.get("key_file") and not config.get("key_content"):
        raise ValueError(
            f"OCI profile '{profile}' is not valid for user_principal auth: "
            "missing 'key_file' or 'key_content'."
        )

    # Session profiles are typically created under ~/.oci/sessions and include
    # security_token_file. They are not coherent with user_principal mode.
    if config.get("security_token_file"):
        raise ValueError(
            f"OCI profile '{profile}' looks like a session-auth profile "
            "('security_token_file' is set). Use OCI_AUTH_MODE=session or switch "
            "to an API-key profile for user_principal."
        )
    key_file = str(config.get("key_file") or "")
    normalized_key_file = os.path.expanduser(key_file).replace("\\", "/")
    if "/.oci/sessions/" in normalized_key_file:
        raise ValueError(
            f"OCI profile '{profile}' key_file points to a session key "
            f"({key_file}). Use OCI_AUTH_MODE=session or configure an API-key "
            "profile for user_principal."
        )


def _resolve_auth_mode(
    auth_mode: str | None,
    *,
    allowed_modes: set[str],
) -> str:
    """Resolve auth mode from parameter or environment."""
    resolved_auth_mode = auth_mode or os.getenv(AUTH_MODE_ENV_VAR, "user_principal")
    resolved_auth_mode = resolved_auth_mode.strip().lower()
    if resolved_auth_mode not in allowed_modes:
        allowed_modes_label = "', '".join(sorted(allowed_modes))
        raise ValueError(
            f"Invalid auth mode '{resolved_auth_mode}'. Expected one of: "
            f"'{allowed_modes_label}'."
        )
    return resolved_auth_mode


def get_inference_client(*, client_class: Callable[..., Any] = OpenAI):
    """Build the standard inference OpenAI-compatible client for production."""
    return client_class(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )


def get_control_plane_client(
    *,
    profile: str = PROFILE,
    auth_mode: Literal["session", "user_principal"] | None = None,
    client_class: Callable[..., Any] = OpenAI,
):
    """Build the control-plane client for vector stores/connectors operations."""
    resolved_auth_mode = _resolve_auth_mode(
        auth_mode, allowed_modes={"session", "user_principal"}
    )

    auth = (
        OciSessionAuth(profile_name=profile)
        if resolved_auth_mode == "session"
        else OciUserPrincipalAuth(profile_name=profile)
    )
    if resolved_auth_mode == "user_principal":
        auth_config = getattr(auth, "config", None)
        if isinstance(auth_config, Mapping):
            validate_oci_auth_config(
                config=auth_config,
                auth_mode="user_principal",
                profile=profile,
            )

    return client_class(
        base_url=CP_BASE_URL,
        # here we are using OCI auth instead of API key, 
        # so we can set api_key to any non-empty value or None
        api_key="unused",
        http_client=httpx.Client(
            auth=auth,
            headers={
                "opc-compartment-id": COMPARTMENT_ID,
            },
        ),
    )


def get_oci_genai_service_endpoint(region: str = REGION) -> str:
    """Return OCI Generative AI service endpoint for production."""
    return f"https://generativeai.{region}.oci.oraclecloud.com"


def build_oci_genai_client(
    profile: str = PROFILE,
    region: str = REGION,
    auth_mode: Literal["session", "user_principal"] | None = None,
):
    """Build an OCI Generative AI client using the selected authentication mode."""
    config = oci_config.from_file(profile_name=profile)
    client_kwargs: dict[str, Any] = {
        "config": config,
        "service_endpoint": get_oci_genai_service_endpoint(region=region),
    }

    resolved_auth_mode = _resolve_auth_mode(
        auth_mode, allowed_modes={"session", "user_principal"}
    )
    validate_oci_auth_config(
        config=config,
        auth_mode=resolved_auth_mode,
        profile=profile,
    )

    if resolved_auth_mode == "session":
        token_file = config.get("security_token_file")
        key_file = config.get("key_file")
        if not token_file or not key_file:
            raise ValueError(
                "Session auth requires 'security_token_file' and 'key_file' in OCI config."
            )
        with open(os.path.expanduser(token_file), encoding="utf-8") as token_handle:
            token = token_handle.read()
        private_key = load_private_key_from_file(os.path.expanduser(key_file))
        client_kwargs["signer"] = SecurityTokenSigner(
            token,
            private_key,
        )
    else:
        client_kwargs["signer"] = OciUserPrincipalAuth(profile_name=profile).signer

    return GenerativeAiClient(**client_kwargs)
