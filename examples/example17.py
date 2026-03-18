"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to retrieve the status of a file ingested into a Vector Store.

    LA (17/03/2026): for now it is working only in preprod env.
"""
from common import get_client, print_example_summary, print_runtime_config
from config import IS_PREPROD
from config_private import PROJECT_ID

# here we have a problem
# files are working in production but vector stores are working only in ppe for now

# preprod
VECTOR_STORE_ID = "vs_fra_k2kuewsdtfc7sohca4dc97gh5qp6a7wukhpb427vt7vd70il"
FILE_ID = "file-fra-1596879d-f1ca-4831-9502-bd44770a4664"

def main() -> None:
    """Retrieve the status of a file ingested into a Vector Store."""
    print_runtime_config()
    print("")
    print_example_summary("Retrieve the status of a file ingested into a Vector Store.")
    print("")

    # this function is used to wrap switch from LA to GA
    client = get_client(is_preproduction=IS_PREPROD)

    file_status = client.vector_stores.files.retrieve(
        vector_store_id=VECTOR_STORE_ID,
        file_id=FILE_ID,
         extra_headers={"OpenAI-Project": PROJECT_ID},
    )

    print(f"File ID: {file_status.id}")
    print(f"Status: {file_status.status}")
    print(f"Created at: {file_status.created_at}")
    print(f"Usage bytes: {file_status.usage_bytes}")
    
    


if __name__ == "__main__":
    main()
