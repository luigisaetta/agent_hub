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
CONNECTOR_ID = "ocid1.generativeaivectorconnectorppe.oc1.eu-frankfurt-1.amaaaaaa2xxap7yalmrxkktiz7niij4in5qgdysozfhqc4d3ec2f2ualaokq"

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
    """List connectors in compartment."""
    client = build_client()

    response = client.get_vector_store_connector_stats(CONNECTOR_ID)
    stats = response.data
    print(f"Sync Statistics as of: {stats.time_generated}")
    print(f"Created: {stats.created.total_files_synced if stats.created else 0}")
    print(f"Updated: {stats.updated.total_files_synced if stats.updated else 0}")
    print(f"Deleted: {stats.deleted.total_files_synced if stats.deleted else 0}")
    print(f"Failed: {stats.failed.total_files_synced if stats.failed else 0}")
    print(
        f"In Progress: {stats.in_progress.total_files_synced if stats.in_progress else 0}"
    )
    print(f"Ignored: {stats.ignored.total_files_synced if stats.ignored else 0}")
    print(
        f"Unsupported: {stats.unsupported.total_files_synced if stats.unsupported else 0}"
    )
    print(
        f"Metadata Updated: {stats.metadata_updated.total_files_synced if stats.metadata_updated else 0}"
    )


if __name__ == "__main__":
    main()
