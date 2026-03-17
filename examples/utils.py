"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Utility helpers shared by example scripts.
"""

from openai import OpenAI

# these are needed in ppe
from oci_openai import OciOpenAI, OciUserPrincipalAuth

from config import BASE_URL
from config_private import KEY1, PROJECT_ID, COMPARTMENT_ID


def print_streamed_output(stream) -> str:
    """
    Print streaming text deltas from a Responses API stream and return full text.
    """
    chunks = []
    for event in stream:
        if event.type == "response.output_text.delta":
            chunks.append(event.delta)
            print(event.delta, end="", flush=True)
    return "".join(chunks)


def get_client(region: str = "eu-frankfurt-1", is_preproduction: bool = False):
    """
    Get an OpenAI client instance. If is_preproduction is True,
    it returns a client configured for the preproduction environment;
    otherwise, it returns a client configured for the production environment.

    as default it assumes production environment, but you can switch to preproduction
    by setting is_preproduction to True.
    """
    if is_preproduction:
        base_url = (
            f"https://ppe.generativeai.{region}.oci.oraclecloud.com/20231130/openai/v1"
        )

        _client = OciOpenAI(
            base_url=base_url,
            auth=OciUserPrincipalAuth(),
            compartment_id=COMPARTMENT_ID,
        )
    else:
        # production
        # using key
        _client = OpenAI(
            base_url=BASE_URL,
            api_key=KEY1,
            project=PROJECT_ID,
        )
    return _client


def print_header(type: str, where: str) -> None:
    """
    Print a header for the list of vector stores.
    """
    print("=" * 44)
    print(f"List of the {type} in the {where}")
    print("=" * 44)
    print("")
