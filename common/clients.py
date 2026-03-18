"""
Shared client builders used across examples and connector scripts.
"""

from __future__ import annotations

import oci
from openai import OpenAI
from oci_openai import OciOpenAI, OciUserPrincipalAuth

from config import BASE_URL, CP_BASE_URL, IS_PREPROD, REGION
from config_private import COMPARTMENT_ID, KEY1, PROJECT_ID

PROFILE = "DEFAULT"


def get_client(
    is_preproduction: bool = IS_PREPROD,
    is_control_plane: bool = False,
):
    """
    Get an OpenAI-compatible client for production or OCI preproduction.
    """
    if is_control_plane:
        url = CP_BASE_URL
    else:
        url = BASE_URL

    # we need also to use a different client
    if is_preproduction:
        return OciOpenAI(
            base_url=url,
            auth=OciUserPrincipalAuth(),
            compartment_id=COMPARTMENT_ID,
        )

    return OpenAI(
        base_url=url,
        api_key=KEY1,
        project=PROJECT_ID,
    )


def get_oci_genai_service_endpoint(
    region: str = REGION, use_preprod: bool = IS_PREPROD
) -> str:
    """Return OCI Generative AI service endpoint for selected environment."""
    if use_preprod:
        return f"https://ppe.generativeai.{region}.oci.oraclecloud.com"
    return f"https://generativeai.{region}.oci.oraclecloud.com"


def build_oci_genai_client(
    profile: str = PROFILE,
    region: str = REGION,
    use_preprod: bool = IS_PREPROD,
):
    """Build an OCI Generative AI client using profile auth."""

    config = oci.config.from_file(profile_name=profile)
    return oci.generative_ai.GenerativeAiClient(
        config=config,
        service_endpoint=get_oci_genai_service_endpoint(
            region=region, use_preprod=use_preprod
        ),
    )
