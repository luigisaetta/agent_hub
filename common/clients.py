"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Shared client builders used across examples and connector scripts.
"""

from __future__ import annotations

import os
from typing import Callable, Any

import httpx
from oci import config as oci_config
from oci.auth.signers import SecurityTokenSigner
from oci.generative_ai import GenerativeAiClient
from oci.signer import load_private_key_from_file
from openai import OpenAI
from oci_openai import OciSessionAuth

from config import BASE_URL, CP_BASE_URL, REGION
from config_private import COMPARTMENT_ID, KEY1, PROJECT_ID

PROFILE = "DEFAULT"


def get_inference_client(*, client_class: Callable[..., Any] = OpenAI):
    """Build the standard inference OpenAI-compatible client for production."""
    return client_class(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )


def get_control_plane_client(*, client_class: Callable[..., Any] = OpenAI):
    """Build the control-plane client for vector stores/connectors operations."""
    return client_class(
        base_url=CP_BASE_URL,
        api_key="unused",
        http_client=httpx.Client(
            auth=OciSessionAuth(profile_name=PROFILE),
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
):
    """Build an OCI Generative AI client using profile auth."""
    config = oci_config.from_file(profile_name=profile)
    client_kwargs: dict[str, Any] = {
        "config": config,
        "service_endpoint": get_oci_genai_service_endpoint(region=region),
    }

    # When OCI session auth is configured, use a SecurityTokenSigner explicitly.
    token_file = config.get("security_token_file")
    key_file = config.get("key_file")
    if token_file and key_file:
        with open(os.path.expanduser(token_file), encoding="utf-8") as token_handle:
            token = token_handle.read()
        private_key = load_private_key_from_file(os.path.expanduser(key_file))
        client_kwargs["signer"] = SecurityTokenSigner(
            token,
            private_key,
        )

    return GenerativeAiClient(**client_kwargs)
