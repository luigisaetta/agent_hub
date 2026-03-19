"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to query a Vector Store
    using responses API.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import (
    extract_provider_name,
    extract_text_and_refs,
    get_client,
    print_example_summary,
    print_runtime_config,
)
from config import IS_PREPROD
from config_private import PROJECT_ID

# preprod
VECTOR_STORE_ID = "vs_ord_tt8bz118czgpej8gjk70jnrg75p8eolansr5sy6jg3xgyrna"
# VECTOR_STORE_ID = "vs_fra_k2kuewsdtfc7sohca4dc97gh5qp6a7wukhpb427vt7vd70il"
# MODEL_ID = "openai.gpt-5.4"
MODEL_ID = "google.gemini-2.5-pro"


def main() -> None:
    """Query a Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Query a vector store using responses API.")
    print("")

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

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
