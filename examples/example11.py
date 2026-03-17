"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to create a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from openai import OpenAI

# these are needed in ppe
from oci_openai import OciOpenAI, OciUserPrincipalAuth

from config_private import KEY1, PROJECT_ID, COMPARTMENT_ID

REGION = "eu-frankfurt-1"

IS_PREPROD = True


def get_client(is_preproduction: bool = True):
    """
    Get an OpenAI client instance. If is_preproduction is True,
    it returns a client configured for the preproduction environment;
    otherwise, it returns a client configured for the production environment.
    """
    if is_preproduction:
        base_url = f"https://ppe.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"

        _client = OciOpenAI(
            base_url=base_url,
            auth=OciUserPrincipalAuth(),
            compartment_id=COMPARTMENT_ID,
        )
    else:
        base_url = (
            f"https://inference.generativeai.{REGION}.oci.oraclecloud.com/openai/v1"
        )

        _client = OpenAI(
            base_url=base_url,
            api_key=KEY1,
            project=PROJECT_ID,
        )
    return _client


client = get_client(is_preproduction=IS_PREPROD)

vector_store = client.vector_stores.create(
    name="vector-store-ls01",
    description="vector store",
    expires_after={"anchor": "last_active_at", "days": 120},
    metadata={"topic": "oci"},
)

print(vector_store)
