"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to create a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from utils import get_client

REGION = "eu-frankfurt-1"

IS_PREPROD = True


def main() -> None:
    """Create and print a vector store resource."""
    # this function is used to wrap switch from LA to GA
    client = get_client(region=REGION, is_preproduction=IS_PREPROD)

    vector_store = client.vector_stores.create(
        name="vector-store-ls01",
        description="vector store",
        expires_after={"anchor": "last_active_at", "days": 120},
        metadata={"topic": "oci"},
    )

    print(vector_store)


if __name__ == "__main__":
    main()
