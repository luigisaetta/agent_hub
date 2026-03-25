"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Delete all vector stores in the configured project/compartment.
"""

from common import get_control_plane_client

PAGE_SIZE = 100


def main() -> None:
    """Delete all vector stores using explicit page-by-page pagination."""
    client = get_control_plane_client()
    print("\nDeleting all vector stores in the compartment")
    print("=" * 46)

    # 1) Collect all vector store IDs page by page.
    vector_store_ids: list[str] = []
    after = None
    page_num = 1

    while True:
        if after is None:
            page = client.vector_stores.list(limit=PAGE_SIZE, order="desc")
        else:
            page = client.vector_stores.list(
                limit=PAGE_SIZE,
                order="desc",
                after=after,
            )

        if not page.data:
            break

        print(f"Scanning page {page_num}: found {len(page.data)} vector stores")
        vector_store_ids.extend(vs.id for vs in page.data)

        if not page.has_more:
            break

        after = page.data[-1].id
        page_num += 1

    if not vector_store_ids:
        print("No vector stores found.")
        return

    # 2) Delete collected IDs.
    print(f"\nDeleting {len(vector_store_ids)} vector stores...")
    deleted = 0
    failed = 0
    for i, vector_store_id in enumerate(vector_store_ids, start=1):
        try:
            delete_result = client.vector_stores.delete(vector_store_id=vector_store_id)
            deleted += 1
            print(f"[{i}/{len(vector_store_ids)}] Deleted: {vector_store_id}")
            print(delete_result)
            print("")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            failed += 1
            print(f"[{i}/{len(vector_store_ids)}] ERROR deleting: {vector_store_id}")
            print(f"Reason: {exc}")
            print("")

    print(f"Done. Deleted={deleted}, Failed={failed}, Total={len(vector_store_ids)}")


if __name__ == "__main__":
    main()
