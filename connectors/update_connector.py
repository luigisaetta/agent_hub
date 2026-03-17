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

from oci.generative_ai.models import (
    UpdateVectorStoreConnectorDetails,
    ScheduleIntervalConfig,
)
from connectors.common import build_client

CONNECTOR_ID = "put your ocid"


def main() -> None:
    """Update schedule settings for a connector by OCID."""
    genai_client = build_client()

    details = UpdateVectorStoreConnectorDetails(
        schedule_config=ScheduleIntervalConfig(
            config_type="INTERVAL",
            frequency="HOURLY",
            interval=1,
            state="ENABLED",
        ),
    )

    update_response = genai_client.update_vector_store_connector(CONNECTOR_ID, details)

    connector = update_response.data
    print(f"Updated connector : {connector.display_name}")
    print(f" description : {connector.description}")
    print(f" lifecycle : {connector.lifecycle_state}")


if __name__ == "__main__":
    main()
