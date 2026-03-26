"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    Utility script for Demo 4 that lists files in the configured vector store
    and prints their ingest status.
"""

from __future__ import annotations

from common import get_inference_client, print_example_summary, print_runtime_config
from config_private import PROJECT_ID, VECTOR_STORE_ID


def main() -> None:
    """List files in vector store and print status details."""
    print_runtime_config()
    print("")
    print_example_summary("List files in vector store and inspect their status.")
    print("")

    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    client = get_inference_client()

    page = client.vector_stores.files.list(
        vector_store_id=VECTOR_STORE_ID,
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )

    files = getattr(page, "data", []) or []
    if not files:
        print("No files found in vector store.")
        return

    print("Files in vector store:\n")
    for item in files:
        file_id = getattr(item, "id", None)
        filename = "N/A"

        if file_id:
            try:
                file_info = client.files.retrieve(
                    file_id=file_id,
                    extra_headers={"OpenAI-Project": PROJECT_ID},
                )
                filename = getattr(file_info, "filename", "N/A") or "N/A"
            except Exception as exc:  # pylint: disable=broad-exception-caught
                filename = f"N/A (retrieve error: {exc})"

        print(f"File ID:    {file_id}")
        print(f"Filename:   {filename}")
        print(f"Status:     {getattr(item, 'status', None)}")
        print(f"Created at: {getattr(item, 'created_at', None)}")
        print(f"Usage:      {getattr(item, 'usage_bytes', None)} bytes")
        print("")


if __name__ == "__main__":
    main()
