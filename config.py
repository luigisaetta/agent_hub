"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Shared endpoint configuration values used by example scripts.
"""

# REGION = "eu-frankfurt-1"
REGION = "us-chicago-1"

# Shared default model used by examples.
MODEL_ID = "openai.gpt-5.2"
# MODEL_ID = "openai.gpt-5.4"
# MODEL_ID = "google.gemini-2.5-pro"
# MODEL_ID = "openai.gpt-oss-120b"

# this switch is here to decide if you want to try in preprod
# or in production environment.
# (17/03/2026)Note that some features are only available in preprod for now,
# so you might want to switch to preprod to try them out.
IS_PREPROD = True

if IS_PREPROD:
    # this is the URL for inference (data plane)
    BASE_URL = f"https://ppe.inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
    # this is the URL for control plane (CP) operations (e.g. vector store management)
    CP_BASE_URL = (
        f"https://ppe.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
    )
else:
    BASE_URL = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
    CP_BASE_URL = (
        f"https://generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
    )

# to test integration with langfuse
# LANGFUSE_BASE_URL = "https://cloud.langfuse.com"
# this is langfuse hosted on OCI
LANGFUSE_BASE_URL = "http://130.61.176.103:3000"
