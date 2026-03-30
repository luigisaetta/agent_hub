"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    List all vector store connectors in a compartment.
"""

from common import build_oci_genai_client, print_runtime_config
from config_private import COMPARTMENT_ID


def main() -> None:
    """List connectors in compartment."""
    print_runtime_config()
    print("")

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
