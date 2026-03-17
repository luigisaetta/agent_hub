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

from pathlib import Path
import sys

import oci

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from oci.generative_ai.models import (
    CreateVectorStoreConnectorDetails,
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

# OCI Object Storage source for the connector
OS_NAMESPACE = "frpj5kvxryk1"
OS_BUCKET = "agent_hub_files"
# entire bucket
OS_PREFIX = ""


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

    create_connector_details = CreateVectorStoreConnectorDetails(
        compartment_id=COMPARTMENT_ID,
        vector_store_id=VECTOR_STORE_ID,
        display_name="Product Docs Connector",
        description="Syncs documentation from Object Storage",
        configuration=OciObjectStorageConfiguration(
            storage_config_list=[
                ObjectStorageConfig(
                    namespace=OS_NAMESPACE,
                    bucket_name=OS_BUCKET,
                    prefix_list=[OS_PREFIX] if OS_PREFIX else [],
                )
            ]
        ),
        schedule_config=ScheduleIntervalConfig(
            config_type="INTERVAL",
            frequency="DAILY",
            interval=1,
            state="ENABLED",
        ),
    )

    print("")
    print("Creating connector...")
    response = client.create_vector_store_connector(create_connector_details)
    connector = response.data
    connector_id = connector.id
    print(f"Connector Created: {connector_id} | State:{connector.lifecycle_state}")
    print("")


if __name__ == "__main__":
    main()
