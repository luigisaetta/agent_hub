"""
Author: L. Saetta
Last modified: 2026-03-17
License: MIT

Description:
    List all files in the configured project/compartment.
"""

from utils import get_client, print_header

REGION = "eu-frankfurt-1"
IS_PREPROD = False
PAGE_SIZE = 100


def main() -> None:
    """List all files using explicit page-by-page pagination."""
    client = get_client(region=REGION, is_preproduction=IS_PREPROD)

    if IS_PREPROD:
        where = "compartment"
    else:
        where = "project"
    print_header("files", where)

    after = None
    page_num = 1
    total = 0

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

        print(f"\n=== Page {page_num} ({len(page.data)} files) ===")
        for i, item in enumerate(page.data, start=1):
            total += 1
            print(
                f"{i:03d}. id={item.id} filename={item.filename} purpose={item.purpose} status={item.status}"
            )

        if not page.has_more:
            break

        after = page.data[-1].id
        page_num += 1

    print(f"\nDone. Total files listed: {total}")


if __name__ == "__main__":
    main()
