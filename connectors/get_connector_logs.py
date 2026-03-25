"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Retrieve connector ingestion logs.
"""

from common.clients import build_oci_genai_client

CONNECTOR_ID = (
    "ocid1.generativeaivectorconnector.oc1.eu-frankfurt-1."
    "amaaaaaa2xxap7yahtzwclcsmcvayhtpow52ws2ddhk7l5xbg5rnzolm63qq"
)


def main() -> None:
    """List connectors in compartment."""
    client = build_oci_genai_client()

    response = client.list_vector_store_connector_ingestion_logs(CONNECTOR_ID)

    items = response.data.items
    print(f"Total connector ingestion log entries: {len(items)}")
    for entry in items[:10]:  # print first 10
        print(f" {entry}")


if __name__ == "__main__":
    main()
