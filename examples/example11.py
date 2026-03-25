"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to create a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""
import httpx
from openai import OpenAI
from oci_openai import OciSessionAuth

from common import print_example_summary, print_runtime_config
from config import PROD_CP_BASE_URL
from config_private import COMPARTMENT_ID


def main() -> None:
    """Create and print a vector store resource."""
    print_runtime_config()
    print("")
    print_example_summary("Create a vector store with metadata and expiration.")
    print("")

    # this function is used to wrap switch from LA to GA
    # this operations requires control plane
    cp_client = OpenAI(
        base_url=PROD_CP_BASE_URL,
        api_key="unused",
        http_client=httpx.Client(
            auth=OciSessionAuth(profile_name="DEFAULT"),
            headers={
               "opc-compartment-id": COMPARTMENT_ID,
            },
        )
    )

    vector_store = cp_client.vector_stores.create(
        name="vs-lsa-ord-prod01",
        description="vector store",
        expires_after={"anchor": "last_active_at", "days": 120},
        metadata={"topic": "oci"},
    )

    print(vector_store)


if __name__ == "__main__":
    main()
