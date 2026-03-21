"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to add a file to a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import get_client, print_example_summary, print_runtime_config
from config import IS_PREPROD
from config_private import PROJECT_ID, VECTOR_STORE_ID

# here we have a problem
# files are working in production but vector stores are working only in ppe for now

FILE_ID = "file-ord-f3c2b7a8-f0ae-4561-b5b7-cbe7feed3700"


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

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

    # first we get info on the file
    print("File info:")
    _file = client.files.retrieve(
        file_id=FILE_ID, extra_headers={"OpenAI-Project": PROJECT_ID}
    )

    print("File info:")
    print(_file)
    print("")

    print("Uploading file in vector store...")
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
