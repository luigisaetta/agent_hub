"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    This example shows how-to query a Vector Store.
"""

from common import get_inference_client, print_example_summary, print_runtime_config
from config_private import PROJECT_ID, VECTOR_STORE_ID


def main() -> None:
    """Query a Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Query a vector store and return chunks.")
    print("")

    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = get_inference_client()

    # Search Vector Store
    query = "What are the main impacts of AI on labor market?"
    # query = "what is PSG?"

    search_results = client.vector_stores.search(
        vector_store_id=VECTOR_STORE_ID,
        query=query,
        max_num_results=10,
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )

    sorted_results = sorted(
        search_results.data,
        key=lambda item: getattr(item, "score", 0.0) or 0.0,
        reverse=True,
    )

    for item in sorted_results:
        print(item)
        print("")

    print("References:")
    for idx, item in enumerate(sorted_results, start=1):
        additional_properties = getattr(item, "additional_properties", {}) or {}
        if not isinstance(additional_properties, dict):
            additional_properties = {}

        chunk_id = additional_properties.get("chunk_id", "N/A")
        pages = additional_properties.get("page_numbers") or []
        if not isinstance(pages, list):
            pages = [pages]

        print(f"{idx}. chunk_id={chunk_id} pages={pages}")
    print("")


if __name__ == "__main__":
    main()
