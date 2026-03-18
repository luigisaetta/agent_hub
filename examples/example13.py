"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to get the list of Vector Stores in the project/compartment.
    It shows how-to do pagination correctly

    LA (17/03/2026): for now it is working only in preprod env.
"""

from common import get_client

REGION = "eu-frankfurt-1"
IS_PREPROD = True


def print_header():
    """
    Print a header for the list of vector stores.
    """
    print("=" * 44)
    print("List of the Vector Stores in the compartment")
    print("=" * 44)
    print("")


def main() -> None:
    """List and print vector stores for the configured project/compartment."""
    # this function is used to wrap switch from LA to GA
    client = get_client(region=REGION, is_preproduction=IS_PREPROD)

    print_header()

    page_size = 10
    page_num = 1
    after = None

    while True:
        if after is None:
            page = client.vector_stores.list(limit=page_size, order="desc")
        else:
            page = client.vector_stores.list(
                limit=page_size,
                order="desc",
                after=after,
            )

        if not page.data:
            # exit if no data is returned
            break

        print(f"\n=== Page {page_num} ===")
        for i, _vs in enumerate(page.data, start=1):
            print(f"Vector Store {i}:")
            print(_vs)
            print("")

        if not page.has_more:
            break

        after = page.data[-1].id
        page_num += 1


if __name__ == "__main__":
    main()
