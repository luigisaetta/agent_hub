"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    Progressive loader for Demo 4: uploads files from pdf_rag/ into a vector store,
    skipping files already present by filename.
"""

from __future__ import annotations

from pathlib import Path

from common import get_inference_client
from config_private import PROJECT_ID, VECTOR_STORE_ID

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _list_all_vector_store_files(client) -> list:
    """List all file entries currently attached to the vector store."""
    all_items = []
    after = None

    while True:
        params = {"vector_store_id": VECTOR_STORE_ID}
        if after:
            params["after"] = after

        page = client.vector_stores.files.list(
            **params,
            extra_headers={"OpenAI-Project": PROJECT_ID},
        )
        data = getattr(page, "data", []) or []
        all_items.extend(data)

        if not getattr(page, "has_more", False) or not data:
            break

        after = getattr(data[-1], "id", None)
        if not after:
            break

    return all_items


def _existing_filenames_in_vector_store(client) -> set[str]:
    """Resolve existing filenames in vector store (best effort)."""
    existing_names: set[str] = set()

    for item in _list_all_vector_store_files(client):
        file_id = getattr(item, "id", None)
        if not file_id:
            continue

        try:
            file_info = client.files.retrieve(
                file_id=file_id,
                extra_headers={"OpenAI-Project": PROJECT_ID},
            )
            filename = getattr(file_info, "filename", None)
            if filename:
                existing_names.add(filename)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Warning: cannot resolve filename for file_id={file_id}: {exc}")

    return existing_names


def main() -> None:
    """Progressively load local files from pdf_rag/ into the configured vector store."""
    if not VECTOR_STORE_ID:
        print("VECTOR_STORE_ID is empty for the active profile.")
        print("Set VECTOR_STORE_ID in the selected .env profile.")
        return

    root_dir = Path(__file__).resolve().parents[2]
    source_dir = root_dir / "pdf_rag"

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"Directory not found: {source_dir}")
        print("Create pdf_rag/ and add files to ingest.")
        return

    local_files = sorted(
        p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"
    )
    if not local_files:
        print(f"No files found in {source_dir}")
        return

    client = get_inference_client()

    print("Collecting existing filenames in vector store...")
    existing_names = _existing_filenames_in_vector_store(client)
    print(f"Already present in vector store: {len(existing_names)}")

    uploaded = 0
    skipped = 0

    for file_path in local_files:
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            skipped += 1
            print(
                f"SKIP  {file_path.name} (size={file_size} bytes > "
                f"MAX_FILE_SIZE={MAX_FILE_SIZE} bytes)"
            )
            continue

        if file_path.name in existing_names:
            skipped += 1
            print(f"SKIP  {file_path.name} (already present)")
            continue

        print(f"Uploading {file_path.name} ...")
        with open(file_path, "rb") as file_stream:
            uploaded_file = client.files.create(
                file=file_stream,
                purpose="user_data",
                extra_headers={"OpenAI-Project": PROJECT_ID},
            )

        file_id = getattr(uploaded_file, "id", None)
        if not file_id:
            print("  ERROR missing file_id after upload; skipping vector store attach")
            continue

        attach_result = client.vector_stores.files.create(
            vector_store_id=VECTOR_STORE_ID,
            file_id=file_id,
        )
        status = getattr(attach_result, "status", "unknown")
        print(f"  file_id={file_id} attach_status={status}")

        uploaded += 1
        existing_names.add(file_path.name)

    print("")
    print(
        f"Done. Uploaded={uploaded}, Skipped={skipped}, Total local files={len(local_files)}"
    )


if __name__ == "__main__":
    main()
