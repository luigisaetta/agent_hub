"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Cteate a connector between an OCI Object Storage bucket and a Vector Store.
    This example is currently working only in preproduction environment,
    as the connector API is not yet available in production.

    LA (17/03/2026): to run this code we need an update to OCI Python SDK.
"""

import oci

from config_private import COMPARTMENT_ID

# ── Config
PROFILE = "DEFAULT"
REGION = "eu-frankfurt-1"

# for now we should work in ppe
SERVICE_ENDPOINT = f"https://ppe.generativeai.{REGION}.oci.oraclecloud.com"
VECTOR_STORE_ID = "vs_fra_qa4kr3kodsiobau3521kqqxky6l2dunnlxju6dpplppmyw9i"

# OCI Object Storage source for the connector
OS_NAMESPACE = "frpj5kvxryk1"
OS_BUCKET = "agent_hub_files"
# entire bucket
OS_PREFIX = ""


def build_client():
    """
    Build an OCI Generative AI client using standard API-key profile auth.
    """
    config = oci.config.from_file(profile_name=PROFILE)

    # build the client
    return oci.generative_ai.GenerativeAiClient(
        config=config,
        service_endpoint=SERVICE_ENDPOINT,
    )


def main() -> None:
    """List connectors in compartment."""
    client = build_client()

    response = client.list_vector_store_connectors(COMPARTMENT_ID)

    items = response.data.items

    print("")
    print(f"Total connectors in compartment: {len(items)}")
    print("")
    for item in items:
        print(f" - {item.id} [{item.lifecycle_state}] {item.display_name}")


if __name__ == "__main__":
    main()
