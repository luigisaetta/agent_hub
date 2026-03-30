"""
Author: L. Saetta
Last modified: 2026-03-30
License: MIT

Description:
    Trigger a manual connector file sync operation and print sync metadata.
"""

from __future__ import annotations

from oci.generative_ai.models import CreateVectorStoreConnectorFileSyncDetails

from common import build_oci_genai_client, print_runtime_config

CONNECTOR_ID = CONNECTOR_ID = "ocid1.generativeaivectorconnector.oc1.us-chicago-1.amaaaaaa2xxap7yall25iqlkmct364vclhhhmkc47ktj65aoyxqn53ebkq7a"
DISPLAY_NAME = "test-file-sync"


def trigger_file_sync(
    connector_id: str = CONNECTOR_ID, display_name: str = DISPLAY_NAME
) -> str:
    """Trigger a manual file sync for the given vector store connector."""
    client = build_oci_genai_client()

    details = CreateVectorStoreConnectorFileSyncDetails(
        vector_store_connector_id=connector_id,
        display_name=display_name,
    )
    response = client.create_vector_store_connector_file_sync(details)
    file_sync = response.data

    print(f"Created  id           : {file_sync.id}")
    print(f"         display_name : {file_sync.display_name}")
    print(f"         lifecycle    : {file_sync.lifecycle_state}")
    print(f"         trigger_type : {file_sync.trigger_type}")
    return file_sync.id


def main() -> None:
    """Trigger a connector file sync using script-level constants."""
    print_runtime_config()
    print("")
    trigger_file_sync()


if __name__ == "__main__":
    main()
