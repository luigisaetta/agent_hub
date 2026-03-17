"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Cteate a connector between an OCI Object Storage bucket and a Vector Store.
    This example is currently working only in preproduction environment,
    as the connector API is not yet available in production.

    LA (17/03/2026): to run this code we need an update to OCI Python SDK.
"""

import oci

# ── Config
PROFILE = "DEFAULT"
REGION = "eu-frankfurt-1"

# for now we should work in ppe
SERVICE_ENDPOINT = f"https://ppe.generativeai.{REGION}.oci.oraclecloud.com"
CONNECTOR_ID = "put your ocid"


def build_client():
    """
    Build an OCI Generative AI client using standard API-key profile auth.
    """
    config = oci.config.from_file(profile_name=PROFILE)

    # build the client
    return oci.generative_ai.GenerativeAiClient(
        config=config,
        service_endpoint=SERVICE_ENDPOINT,
    )


def main() -> None:
    """Delete a connector by OCID and confirm the result."""
    genai_client = build_client()
    genai_client.delete_vector_store_connector(CONNECTOR_ID)
    print(f"Delete request accepted for: {CONNECTOR_ID}")

    # Confirm deletion via get (expect 404 / DELETED state)
    try:
        get_response = genai_client.get_vector_store_connector(CONNECTOR_ID)
        print(f"Post-delete lifecycle: {get_response.data.lifecycle_state}")
    except oci.exceptions.ServiceError as exc:
        if exc.status == 404:
            print("Confirmed: connector no longer found (404)")
        else:
            raise


if __name__ == "__main__":
    main()
