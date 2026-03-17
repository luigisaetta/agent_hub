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

from http import client
from pathlib import Path
import sys
from urllib import response

import oci

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from oci.generative_ai.models import (
    CreateVectorStoreConnectorDetails,
    UpdateVectorStoreConnectorDetails,
    ObjectStorageConfig,
    OciObjectStorageConfiguration,
    ScheduleIntervalConfig,
)
from config_private import COMPARTMENT_ID

# ── Config
PROFILE = "DEFAULT"
REGION = "eu-frankfurt-1"

# for now we should work in ppe
SERVICE_ENDPOINT = f"https://ppe.generativeai.{REGION}.oci.oraclecloud.com"
VECTOR_STORE_ID = "vs_fra_qa4kr3kodsiobau3521kqqxky6l2dunnlxju6dpplppmyw9i"
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
    """Build connector details for an Object Storage to Vector Store connector."""
    client = build_client()

    response = client.list_vector_store_connectors(COMPARTMENT_ID)

    items = response.data.items

    print("")
    print(f"Total connectors in compartment: {len(items)}")
    print("")
    for item in items:
        print(f" - {item.id} [{item.lifecycle_state}] {item.display_name}")

    client.delete_vector_store_connector(CONNECTOR_ID)
    print(f"Delete request accepted for: {CONNECTOR_ID}")
    
    # Confirm deletion via get (expect 404 / DELETED state)
    try:
        response = client.get_vector_store_connector(CONNECTOR_ID)
        print(f"Post-delete lifecycle: {response.data.lifecycle_state}")
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            print("Confirmed: connector no longer found (404)")
        else:
            raise

if __name__ == "__main__":
    main()
