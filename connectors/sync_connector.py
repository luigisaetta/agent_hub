"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Trigger a manual synchronization for an existing connector.
"""

from oci.generative_ai.models import CreateVectorStoreConnectorFileSyncDetails
from common import build_oci_genai_client, print_runtime_config

CONNECTOR_ID = "ocid1.generativeaivectorconnector.oc1.us-chicago-1.amaaaaaa2xxap7yall25iqlkmct364vclhhhmkc47ktj65aoyxqn53ebkq7a"


def main() -> None:
    """List connectors in compartment."""
    print_runtime_config()
    print("")

    client = build_oci_genai_client()

    details = CreateVectorStoreConnectorFileSyncDetails(
        vector_store_connector_id=CONNECTOR_ID,
        display_name="test-file-sync01",
    )

    response = client.create_vector_store_connector_file_sync(details)
    file_sync = response.data

    print(f"Created id : {file_sync.id}")
    print(f" display_name : {file_sync.display_name}")
    print(f" lifecycle : {file_sync.lifecycle_state}")
    print(f" trigger_type : {file_sync.trigger_type}")


if __name__ == "__main__":
    main()
