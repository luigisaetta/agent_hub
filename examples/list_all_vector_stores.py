"""
Author: L. Saetta
Last modified: 2026-03-17
License: MIT

Description:
    List all vector stores in the configured project/compartment.
"""

from datetime import datetime, timezone

from common import get_client, print_header, print_runtime_config
from config import IS_PREPROD

PAGE_SIZE = 100


def format_expiration(expires_at: int | None) -> str:
    """Format expiration epoch seconds into a readable UTC datetime string."""
    if not expires_at:
        return "N/A"

    dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def main() -> None:
    """List all vector stores using explicit page-by-page pagination."""
    print_runtime_config()
    print("")

    client = get_client(is_preproduction=IS_PREPROD, is_control_plane=True)

    if IS_PREPROD:
        where = "compartment"
    else:
        where = "project"
    print_header("vector stores", where)

    after = None
    page_num = 1
    total = 0

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

        print(f"\n=== Page {page_num} ({len(page.data)} vector stores) ===")
        for i, vector_store in enumerate(page.data, start=1):
            total += 1
            expires_at = format_expiration(getattr(vector_store, "expires_at", None))
            print(
                f"{i:03d}. id={vector_store.id} "
                f"name={vector_store.name} status={vector_store.status} "
                f"expires_at={expires_at}"
            )

        if not page.has_more:
            break

        after = page.data[-1].id
        page_num += 1

    print(f"\nDone. Total vector stores listed: {total}")
    print("")


if __name__ == "__main__":
    main()
