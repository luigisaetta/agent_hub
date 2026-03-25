"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to create a Vector Store.
"""

from common import get_control_plane_client, print_example_summary, print_runtime_config


def main() -> None:
    """Create and print a vector store resource."""
    print_runtime_config()
    print("")
    print_example_summary("Create a vector store with metadata and expiration.")
    print("")

    cp_client = get_control_plane_client()

    vector_store = cp_client.vector_stores.create(
        name="vs-lsa-ord-prod01",
        description="vector store",
        expires_after={"anchor": "last_active_at", "days": 120},
        metadata={"topic": "oci"},
    )

    print(vector_store)


if __name__ == "__main__":
    main()
