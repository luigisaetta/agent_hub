"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    Utility script for Demo 4 that lists files in the configured vector store
    and prints their ingest status.
"""

from __future__ import annotations

from openai import NotFoundError

from common import get_inference_client, print_example_summary, print_runtime_config
from config_private import PROJECT_ID, VECTOR_STORE_ID


def _best_effort_filename_from_item(item) -> str | None:
    """Try to read a filename directly from vector-store file payload."""
    for attr in ("filename", "file_name", "name", "display_name"):
        value = getattr(item, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _resolve_filename(client, item) -> str:
    """Resolve filename; handle connector-only files without noisy traceback text."""
    file_id = getattr(item, "id", None)
    if not file_id:
        return "N/A"

    try:
        file_info = client.files.retrieve(
            file_id=file_id,
            extra_headers={"OpenAI-Project": PROJECT_ID},
        )
        return getattr(file_info, "filename", "N/A") or "N/A"
    except NotFoundError as exc:
        # Connector-ingested files are present in vector store but not in files API.
        if "File is a connector file" in str(exc):
            return _best_effort_filename_from_item(item) or "<connector file>"
        return "N/A"
    except Exception:  # pylint: disable=broad-exception-caught
        return "N/A"


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
        filename = _resolve_filename(client, item)

        print(f"File ID:    {file_id}")
        print(f"Filename:   {filename}")
        print(f"Status:     {getattr(item, 'status', None)}")
        print(f"Created at: {getattr(item, 'created_at', None)}")
        print(f"Usage:      {getattr(item, 'usage_bytes', None)} bytes")
        print("")



if __name__ == "__main__":
    main()
