"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Delete a connector between OCI Object Storage and a Vector Store.
"""

from oci.exceptions import ServiceError

from common import build_oci_genai_client, print_runtime_config

CONNECTOR_ID = (
    "ocid1.generativeaivectorconnector.oc1.eu-frankfurt-1."
    "amaaaaaa2xxap7yalmrxkktiz7niij4in5qgdysozfhqc4d3ec2f2ualaokq"
)


def main() -> None:
    """Delete a connector by OCID and confirm the result."""
    print_runtime_config()
    print("")

    genai_client = build_oci_genai_client()
    genai_client.delete_vector_store_connector(CONNECTOR_ID)
    print(f"Delete request accepted for: {CONNECTOR_ID}")

    # Confirm deletion via get (expect 404 / DELETED state)
    try:
        get_response = genai_client.get_vector_store_connector(CONNECTOR_ID)
        print(f"Post-delete lifecycle: {get_response.data.lifecycle_state}")
    except ServiceError as exc:
        if exc.status == 404:
            print("Confirmed: connector no longer found (404)")
        else:
            raise


if __name__ == "__main__":
    main()
