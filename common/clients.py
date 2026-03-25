"""
Shared client builders used across examples and connector scripts.
"""

from __future__ import annotations

from typing import Callable, Any

import httpx
import oci
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
    config = oci.config.from_file(profile_name=profile)
    return oci.generative_ai.GenerativeAiClient(
        config=config,
        service_endpoint=get_oci_genai_service_endpoint(region=region),
    )
