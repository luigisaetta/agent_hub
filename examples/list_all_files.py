"""
Author: L. Saetta
Last modified: 2026-03-17
License: MIT

Description:
    List all files in the configured project/compartment.
"""

from common import get_inference_client, print_header, print_runtime_config
from config_private import PROJECT_ID

PAGE_SIZE = 100


def main() -> None:
    """List all files using explicit page-by-page pagination."""
    print_runtime_config()
    print("")

    client = get_inference_client()
    print_header("files", "project")

    after = None
    page_num = 1
    total = 0

    while True:
        if after is None:
            page = client.files.list(
                limit=PAGE_SIZE,
                order="desc",
                extra_headers={"OpenAI-Project": PROJECT_ID},
            )
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
                f"{i:03d}. id={item.id} filename={item.filename} "
                f"purpose={item.purpose} status={item.status}"
            )

        if not page.has_more:
            break

        after = page.data[-1].id
        page_num += 1

    print(f"\nDone. Total files listed: {total}")
    print("")


if __name__ == "__main__":
    main()
