"""
Author: L. Saetta
Last modified: 2026-05-12
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


def _get_header_case_insensitive(headers, header_name: str) -> str:
    """Read one header value with case-insensitive matching."""
    if headers is None:
        return ""

    value = headers.get(header_name)
    if value:
        return str(value)

    header_name = header_name.lower()
    for key, item_value in headers.items():
        if str(key).lower() == header_name:
            return str(item_value)
    return ""


def _extract_opc_request_id(raw_response) -> str:
    """Extract the OCI request id from a raw OpenAI-compatible response."""
    headers = getattr(raw_response, "headers", None)
    return _get_header_case_insensitive(headers, "opc-request-id") or (
        _get_header_case_insensitive(headers, "opc-requestid")
    )


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

    # query = (
    #    "Summarize the retrieved documents about the impact of AI adoption "
    #    "on the labor market, focusing on employment, unemployment, wages, "
    #    "hiring, and which occupations appear most exposed."
    # )

    query = "What is an HNSW index?"

    raw_response = client.responses.with_raw_response.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        input=[
            {
                # cannot use system if provider is google
                "role": role_instructions,
                "content": (
                    "Answer using only information from the retrieved documents. "
                    "You may summarize or synthesize information that is "
                    "explicitly supported by the retrieved text. "
                    "Do not use outside knowledge. "
                    "If the retrieved documents do not contain enough "
                    "information to answer, say exactly: "
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
    response = raw_response.parse()
    opc_request_id = _extract_opc_request_id(raw_response)

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
        print(f"opc-request-id: {opc_request_id or '<not available>'}")
        for i, item in enumerate(response.output):
            print(f"\n--- item {i} ---")
            print("type:", getattr(item, "type", None))
            model_dump_json = getattr(item, "model_dump_json", None)
            if callable(model_dump_json):
                print(model_dump_json(indent=2))
            else:
                print(item)


if __name__ == "__main__":
    main()
