"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how to upload a file to a vector store
    and wait for file-batch processing.
"""

from pathlib import Path

from common import get_control_plane_client, print_example_summary, print_runtime_config
from config_private import VECTOR_STORE_ID


def main() -> None:
    """Upload a file and store it in the vector store."""
    print_runtime_config()
    print("")
    print_example_summary("Upload to vector store and poll batch processing.")
    print("")

    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = get_control_plane_client()

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
