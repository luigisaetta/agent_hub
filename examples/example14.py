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

# here we have a problem
# files are working in production but vector stores are working only in ppe for now

VECTOR_STORE_ID = "vs_fra_2m3tcst2vzhbb2guihs59jwonprhd0rxbtmq1zy9uxrdni52"
FILE_ID = "file-fra-1596879d-f1ca-4831-9502-bd44770a4664"


def main() -> None:
    """Add a file to an existing Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Attach an existing file to a vector store.")
    print("")

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

    # first we get info on the file
    print("File info:")
    _file = client.files.retrieve(file_id=FILE_ID)

    print(_file)
    print("")

    create_result = client.vector_stores.files.create(
        vector_store_id=VECTOR_STORE_ID,
        file_id=FILE_ID,
        attributes={"category": "ai_research"},
    )

    print("")
    print(create_result)
    print("")


if __name__ == "__main__":
    main()
