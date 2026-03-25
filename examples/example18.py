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

TEMPERATURE = 0.0


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

    query = (
        "Summarize the retrieved documents about the impact of AI adoption "
        "on the labor market, focusing on employment, unemployment, wages, "
        "hiring, and which occupations appear most exposed."
    )

    response = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        input=[
            {
                # cannot use system if provider is google
                "role": role_instructions,
                "content": (
                    "Answer using only information from the retrieved documents. "
                    "You may summarize or synthesize information that is explicitly supported by the retrieved text. "
                    "Do not use outside knowledge. "
                    "If the retrieved documents do not contain enough information to answer, say exactly: "
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
        tool_choice="required",
        include=["file_search_call.results"],
    )

    text, refs = extract_text_and_refs(response)

    print("")
    print("Query: ", query)
    print("")

    print(text)
    print("")
    print("References:")
    for r in refs:
        print(f"[{r['n']}] {r['filename']} (pages={r['pages']})")
    print("")

    # debug information
    if "don't have sufficient information" in text:
        print("Debug info: ")
        for i, item in enumerate(response.output):
            print(f"\n--- item {i} ---")
            print("type:", getattr(item, "type", None))
            try:
                print(item.model_dump_json(indent=2))
            except Exception:
                print(item)


if __name__ == "__main__":
    main()
