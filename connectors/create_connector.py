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

from datetime import datetime, timedelta, timezone

from oci.generative_ai.models import (
    CreateVectorStoreConnectorDetails,
    ObjectStorageConfig,
    OciObjectStorageConfiguration,
    ScheduleIntervalConfig,
)
from common.clients import build_oci_genai_client
from config_private import COMPARTMENT_ID

VECTOR_STORE_ID = "vs_fra_qa4kr3kodsiobau3521kqqxky6l2dunnlxju6dpplppmyw9i"

# OCI Object Storage source for the connector
OS_NAMESPACE = "frpj5kvxryk1"
OS_BUCKET = "agent_hub_files"
# entire bucket
OS_PREFIX = ""


def main() -> None:
    """Build connector details for an Object Storage to Vector Store connector."""
    client = build_oci_genai_client()

    # list existing connectors
    response = client.list_vector_store_connectors(COMPARTMENT_ID)

    items = response.data.items

    print("")
    print(f"Total connectors in compartment: {len(items)}")
    print("")
    for item in items:
        print(f" - {item.id} [{item.lifecycle_state}] {item.display_name}")

    # create the new connector
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
            frequency="HOURLY",
            interval=1,
            state="ENABLED",
            # schedule the first run 10 minutes from now
            time_start=datetime.now(timezone.utc) + timedelta(minutes=10),
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
