"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to add a file to a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import get_client

REGION = "eu-frankfurt-1"

# here we have a problem
# files are working in production but vector stores are working only in ppe for now
IS_PREPROD = True

VECTOR_STORE_ID = "vs_fra_2m3tcst2vzhbb2guihs59jwonprhd0rxbtmq1zy9uxrdni52"
FILE_ID = "file-fra-2e452ed5-5a1f-418f-b991-d3caefcaf1aa"


def main() -> None:
    """Add a file to an existing Vector Store."""
    # this function is used to wrap switch from LA to GA
    client = get_client(region=REGION, is_preproduction=IS_PREPROD)

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
