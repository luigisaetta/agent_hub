"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Retrieve connector ingestion logs.
"""

from common import build_oci_genai_client, print_runtime_config

CONNECTOR_ID = "ocid1.generativeaivectorconnector.oc1.us-chicago-1.amaaaaaa2xxap7yall25iqlkmct364vclhhhmkc47ktj65aoyxqn53ebkq7a"


def main() -> None:
    """List connectors in compartment."""
    print_runtime_config()
    print("")

    client = build_oci_genai_client()

    response = client.list_vector_store_connector_ingestion_logs(CONNECTOR_ID)

    items = response.data.items
    print(f"Total connector ingestion log entries: {len(items)}")
    for entry in items[:10]:  # print first 10
        print(f" {entry}")


if __name__ == "__main__":
    main()
