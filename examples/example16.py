"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to query a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import get_client, print_example_summary, print_runtime_config
from config import IS_PREPROD
from config_private import PROJECT_ID

# here we have a problem
# files are working in production but vector stores are working only in ppe for now

# preprod
# VECTOR_STORE_ID = "vs_ord_tt8bz118czgpej8gjk70jnrg75p8eolansr5sy6jg3xgyrna"
VECTOR_STORE_ID = "vs_fra_k2kuewsdtfc7sohca4dc97gh5qp6a7wukhpb427vt7vd70il"


def main() -> None:
    """Query a Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Query a vector store and return chunks.")
    print("")

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

    # Search Vector Store
    query = "What are the main impacts of AI on labor market?"

    search_results = client.vector_stores.search(
        vector_store_id=VECTOR_STORE_ID,
        query=query,
        max_num_results=10,
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )

    for _page in search_results.data:
        print(_page)
        print("")


if __name__ == "__main__":
    main()
