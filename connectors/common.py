"""
Shared connector configuration and OCI Generative AI client builder.
"""

from __future__ import annotations

import oci

PROFILE = "DEFAULT"
REGION = "eu-frankfurt-1"
USE_PREPROD = True


def get_service_endpoint(region: str = REGION, use_preprod: bool = USE_PREPROD) -> str:
    """Return OCI Generative AI service endpoint for selected environment."""
    if use_preprod:
        return f"https://ppe.generativeai.{region}.oci.oraclecloud.com"
    return f"https://generativeai.{region}.oci.oraclecloud.com"


def build_client(
    profile: str = PROFILE,
    region: str = REGION,
    use_preprod: bool = USE_PREPROD,
):
    """Build an OCI Generative AI client using profile auth."""
    config = oci.config.from_file(profile_name=profile)
    return oci.generative_ai.GenerativeAiClient(
        config=config,
        service_endpoint=get_service_endpoint(region=region, use_preprod=use_preprod),
    )
