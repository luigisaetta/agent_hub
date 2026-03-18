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

from common.clients import build_oci_genai_client
from config_private import COMPARTMENT_ID


def main() -> None:
    """List connectors in compartment."""
    client = build_oci_genai_client()

    response = client.list_vector_store_connectors(COMPARTMENT_ID)

    items = response.data.items

    print("")
    print(f"Total connectors in compartment: {len(items)}")
    print("")
    for item in items:
        print(f" - {item.id} [{item.lifecycle_state}] {item.display_name}")
        print(item)


if __name__ == "__main__":
    main()
