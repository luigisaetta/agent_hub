"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to create a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import get_client, print_example_summary, print_runtime_config
from config import IS_PREPROD


def main() -> None:
    """Create and print a vector store resource."""
    print_runtime_config()
    print("")
    print_example_summary("Create a vector store with metadata and expiration.")
    print("")

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

    vector_store = client.vector_stores.create(
        name="vs-lsa02",
        description="vector store",
        expires_after={"anchor": "last_active_at", "days": 120},
        metadata={"topic": "oci"},
    )

    print(vector_store)


if __name__ == "__main__":
    main()
