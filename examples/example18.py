"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to query a Vector Store
    using responses API.
"""

from common import (
    extract_provider_name,
    extract_text_and_refs,
    get_inference_client,
    print_example_summary,
    print_runtime_config,
)
from config import MODEL_ID
from config_private import PROJECT_ID, VECTOR_STORE_ID


def main() -> None:
    """Query a Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Query a vector store using responses API.")
    print("")

    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = get_inference_client()

    # tho handle the issue with Gemini-2.5-pro that does not allow
    # to use system role, we need to set the role of the instructions based on the provider
    provider_name = extract_provider_name(MODEL_ID)

    if provider_name == "google":
        role_instructions = "user"
    else:
        role_instructions = "system"

    query = "Create a complete report on the impact of AI adoption on the labor market?"

    response = client.responses.create(
        model=MODEL_ID,
        input=[
            {
                # cannot use system if provider is google
                "role": role_instructions,
                "content": (
                    "Answer ONLY using the retrieved documents. "
                    "If the answer is not found, say: "
                    "'I don't have sufficient information in the documents.'"
                ),
            },
            {"role": "user", "content": query},
        ],
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID],
                "max_num_results": 10,
            }
        ],
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )

    text, refs = extract_text_and_refs(response)

    print(text)
    print("")
    print("References:")
    for r in refs:
        print(f"[{r['n']}] {r['filename']} (pages={r['pages']})")
    print("")


if __name__ == "__main__":
    main()
