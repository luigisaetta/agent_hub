"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how to upload a file to a vector store
    and wait for file-batch processing.
"""

from pathlib import Path

from common import get_client

REGION = "us-chicago-1"
IS_PREPROD = True
VECTOR_STORE_ID = "vs_ord_8rbth2q8lgxawdn7za4exue8l0qcdbwohkgscy7lkkl9wqeg"


# this function is used to wrap switch from LA to GA
# default: production environment, but you can switch to preproduction
# by setting is_preproduction to True.
def main() -> None:
    """Upload a file and store it in the vector store."""
    client = get_client(region=REGION, is_preproduction=IS_PREPROD)

    root_dir = Path(__file__).resolve().parents[1]
    file_path = root_dir / "pdf" / "labor_market_impacts_ai.pdf"

    print("Uploading file...")

    # --------------------------------------------------
    # Upload files and wait for processing (chunk + embed)
    # --------------------------------------------------
    with open(file_path, "rb") as file_stream:
        file_batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=VECTOR_STORE_ID,
            files=[file_stream],
        )

        print(f"Upload status: {file_batch.status}")
        print(f"Files processed: {file_batch.file_counts}")


if __name__ == "__main__":
    main()
