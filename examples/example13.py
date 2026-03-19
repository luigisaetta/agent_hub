"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to get the list of all the files loaded in a vector store.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import get_client, print_example_summary, print_runtime_config
from config import IS_PREPROD
from config_private import PROJECT_ID

# here we have a problem
# files are working in production but vector stores are working only in ppe for now

# preprod
VECTOR_STORE_ID = "vs_ord_tt8bz118czgpej8gjk70jnrg75p8eolansr5sy6jg3xgyrna"


def main() -> None:
    """List all the files in a given vector store."""
    print_runtime_config()
    print("")
    print_example_summary("List all the files in a given vector store.")
    print("")

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

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
