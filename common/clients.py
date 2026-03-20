"""
Shared client builders used across examples and connector scripts.
"""

from __future__ import annotations

import oci
from openai import OpenAI
from oci_openai import OciOpenAI, OciUserPrincipalAuth

from config import IS_PREPROD, REGION
from config_private import COMPARTMENT_ID, KEY1, PROJECT_ID

PROFILE = "DEFAULT"


def get_openai_base_url(
    *,
    region: str = REGION,
    use_preprod: bool = IS_PREPROD,
    is_control_plane: bool = False,
) -> str:
    """Return OpenAI-compatible data/control plane URL for selected environment."""
    if is_control_plane:
        if use_preprod:
            return f"https://ppe.generativeai.{region}.oci.oraclecloud.com/20231130/openai/v1"
        return f"https://generativeai.{region}.oci.oraclecloud.com/20231130/openai/v1"

    if use_preprod:
        return f"https://ppe.inference.generativeai.{region}.oci.oraclecloud.com/20231130/openai/v1"
    return f"https://inference.generativeai.{region}.oci.oraclecloud.com/20231130/openai/v1"


def get_client(
    is_preproduction: bool | None = None,
    is_control_plane: bool = False,
):
    """
    Get an OpenAI-compatible client for production or OCI preproduction.
    """
    if is_preproduction is None:
        is_preproduction = IS_PREPROD

    url = get_openai_base_url(
        region=REGION,
        use_preprod=is_preproduction,
        is_control_plane=is_control_plane,
    )

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
