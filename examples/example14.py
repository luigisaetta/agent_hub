"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to add a file to a Vector Store.
"""

from common import (
    get_inference_client,
    print_example_summary,
    print_runtime_config,
)
from config_private import PROJECT_ID, VECTOR_STORE_ID

# you must put here a valid file_id
FILE_ID = "file-ord-38d78c44-aea4-40ff-aa34-b50e3409ef12"


def main() -> None:
    """Add a file to an existing Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Add an existing file to a vector store.")
    print("")

    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = get_inference_client()

    # first we get info on the file
    print("File info:")
    _file = client.files.retrieve(
        file_id=FILE_ID, extra_headers={"OpenAI-Project": PROJECT_ID}
    )

    print("File info:")
    print(_file)
    print("")

    print("Uploading file in vector store...")
    # If needed, specify chunking params here with `chunking_strategy={...}`.
    create_result = client.vector_stores.files.create(
        vector_store_id=VECTOR_STORE_ID,
        file_id=FILE_ID,
        attributes={"category": "ai_research"},
    )

    print("")
    print("File added to vector store. Result:")
    print(create_result)
    print("")


if __name__ == "__main__":
    main()
