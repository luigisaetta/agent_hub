"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    This example shows how-to upload a file
    and how-to get the list of all the files in the project.
"""

from pathlib import Path

from common import get_client, print_example_summary, print_runtime_config
from config import IS_PREPROD
from config_private import PROJECT_ID


# this function is used to wrap switch from LA to GA
# default: production environment, but you can switch to preproduction
# by setting is_preproduction to True.
def main() -> None:
    """Upload a file and print the list of project files."""
    print_runtime_config()
    print("")
    print_example_summary("Upload a PDF file and list project files.")
    print("")

    client = get_client(is_preproduction=IS_PREPROD)

    root_dir = Path(__file__).resolve().parents[1]
    file_path = root_dir / "pdf" / "labor_market_impacts_ai.pdf"

    print("Uploading file...")
    with open(file_path, "rb") as f:
        # warning: repeating means you're uploading a new version of the same file
        # and it will create a new file each time. In production,
        # you should store the file ID and reuse it.
        file = client.files.create(
            file=f,
            purpose="user_data",
            extra_headers={"OpenAI-Project": PROJECT_ID},
        )
        print(file)

    # list files
    print("Listing files in the project/compartment...")
    files_list = client.files.list(
        order="asc",
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )
    print("")

    for _file in files_list:
        print(_file)


if __name__ == "__main__":
    main()
