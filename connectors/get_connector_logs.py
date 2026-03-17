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

from connectors.common import build_client

CONNECTOR_ID = "ocid1.generativeaivectorconnectorppe.oc1.eu-frankfurt-1.amaaaaaa2xxap7yahtzwclcsmcvayhtpow52ws2ddhk7l5xbg5rnzolm63qq"


def main() -> None:
    """List connectors in compartment."""
    client = build_client()

    response = client.list_vector_store_connector_ingestion_logs(CONNECTOR_ID)

    items = response.data.items
    print(f"Total connector ingestion log entries: {len(items)}")
    for entry in items[:10]:  # print first 10
        print(f" {entry}")


if __name__ == "__main__":
    main()
