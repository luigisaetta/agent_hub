"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to retrieve the status of a file ingested into a Vector Store.
"""

from common import get_inference_client, print_example_summary, print_runtime_config
from config_private import PROJECT_ID, VECTOR_STORE_ID

FILE_ID = "file-ord-38d78c44-aea4-40ff-aa34-b50e3409ef12"


def main() -> None:
    """Retrieve the status of a file ingested into a Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Retrieve the status of a file ingested into a Vector Store.")
    print("")

    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = get_inference_client()

    file_status = client.vector_stores.files.retrieve(
        vector_store_id=VECTOR_STORE_ID,
        file_id=FILE_ID,
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )

    print(f"File ID: {file_status.id}")
    print(f"Status: {file_status.status}")
    print(f"Created at: {file_status.created_at}")
    print(f"Usage bytes: {file_status.usage_bytes}")


if __name__ == "__main__":
    main()
