"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to get the list of all the files loaded in a vector store.
"""

from common import get_inference_client, print_example_summary, print_runtime_config
from config_private import PROJECT_ID, VECTOR_STORE_ID


def main() -> None:
    """List all the files in a given vector store."""
    print_runtime_config()
    print("")
    print_example_summary("List all the files in a given vector store.")
    print("")

    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = get_inference_client()

    # first we get info on the file
    _files = client.vector_stores.files.list(
        vector_store_id=VECTOR_STORE_ID, extra_headers={"OpenAI-Project": PROJECT_ID}
    )

    print("\nFiles in vector store:\n")

    for f in _files.data:
        print(f"File ID: {f.id}")
        print(f"Status: {f.status}")
        print(f"Created at: {f.created_at}")
        print(f"Usage bytes: {f.usage_bytes}")
        print("")


if __name__ == "__main__":
    main()
