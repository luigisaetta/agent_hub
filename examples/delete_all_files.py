"""
Author: L. Saetta
Last modified: 2026-03-17
License: MIT

Description:
    Delete all files in the configured project/compartment.
"""

from utils import get_client

REGION = "eu-frankfurt-1"
IS_PREPROD = False
PAGE_SIZE = 100


def main() -> None:
    """Delete all files using explicit page-by-page pagination."""
    client = get_client(region=REGION, is_preproduction=IS_PREPROD)
    print("\nDeleting all files in the project")
    print("=" * 34)

    # 1) Collect all file IDs page by page.
    file_ids: list[str] = []
    after = None
    page_num = 1

    while True:
        if after is None:
            page = client.files.list(limit=PAGE_SIZE, order="desc")
        else:
            page = client.files.list(
                limit=PAGE_SIZE,
                order="desc",
                after=after,
            )

        if not page.data:
            break

        print(f"Scanning page {page_num}: found {len(page.data)} files")
        file_ids.extend(item.id for item in page.data)

        if not page.has_more:
            break

        after = page.data[-1].id
        page_num += 1

    if not file_ids:
        print("No files found.")
        return

    # 2) Delete collected IDs.
    print(f"\nDeleting {len(file_ids)} files...")
    deleted = 0
    failed = 0
    for i, file_id in enumerate(file_ids, start=1):
        try:
            delete_result = client.files.delete(file_id=file_id)
            deleted += 1
            print(f"[{i}/{len(file_ids)}] Deleted: {file_id}")
            print(delete_result)
            print("")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            failed += 1
            print(f"[{i}/{len(file_ids)}] ERROR deleting: {file_id}")
            print(f"Reason: {exc}")
            print("")

    print(f"Done. Deleted={deleted}, Failed={failed}, Total={len(file_ids)}")


if __name__ == "__main__":
    main()
