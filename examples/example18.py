"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to query a Vector Store
    using responses API.

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import get_client, print_example_summary, print_runtime_config
from config import IS_PREPROD
from config_private import PROJECT_ID

# preprod
VECTOR_STORE_ID = "vs_ord_tt8bz118czgpej8gjk70jnrg75p8eolansr5sy6jg3xgyrna"
MODEL_ID = "openai.gpt-5.2"


def extract_text_and_refs(response):
    """
    Utility function to get text + annotations directly
    """
    text_obj = response.output[1].content[0]

    text = text_obj.text
    annotations = text_obj.annotations

    # Sort annotations by position
    annotations = sorted(annotations, key=lambda a: a.index)

    refs = {}
    ref_list = []
    counter = 1
    offset = 0

    for ann in annotations:
        file_id = ann.file_id

        if file_id not in refs:
            refs[file_id] = counter
            ref_list.append(
                {
                    "n": counter,
                    "filename": ann.filename,
                    "pages": ann.additional_properties.get("page_numbers"),
                }
            )
            counter += 1

        # add a marker for the references in the text
        marker = f"[{refs[file_id]}] "
        pos = ann.index + offset

        text = text[:pos] + marker + text[pos:]
        offset += len(marker)

    return text, ref_list


def main() -> None:
    """Query a Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Query a vector store using responses API.")
    print("")

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

    query = "Create a complete report on the impact of AI adoption on the labor market?"

    response = client.responses.create(
        model=MODEL_ID,
        input=[
            {
                "role": "system",
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
