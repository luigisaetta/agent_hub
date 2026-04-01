"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Retrieve connector synchronization statistics.
"""

from common import build_oci_genai_client, print_runtime_config

# chicago
CONNECTOR_ID = "ocid1.generativeaivectorconnector.oc1.us-chicago-1.amaaaaaa2xxap7yall25iqlkmct364vclhhhmkc47ktj65aoyxqn53ebkq7a"



def main() -> None:
    """List connectors in compartment."""
    print_runtime_config()
    print("")

    client = build_oci_genai_client()

    response = client.get_vector_store_connector_stats(CONNECTOR_ID)
    
    stats = response.data
    print(f"Sync Statistics as of: {stats.time_generated}")
    print(f"Created: {stats.created.total_files_synced if stats.created else 0}")
    print(f"Updated: {stats.updated.total_files_synced if stats.updated else 0}")
    print(f"Deleted: {stats.deleted.total_files_synced if stats.deleted else 0}")
    print(f"Failed: {stats.failed.total_files_synced if stats.failed else 0}")
    print(
        f"In Progress: {stats.in_progress.total_files_synced if stats.in_progress else 0}"
    )
    print(f"Ignored: {stats.ignored.total_files_synced if stats.ignored else 0}")
    print(
        f"Unsupported: {stats.unsupported.total_files_synced if stats.unsupported else 0}"
    )
    print(
        "Metadata Updated: "
        f"{stats.metadata_updated.total_files_synced if stats.metadata_updated else 0}"
    )


if __name__ == "__main__":
    main()
