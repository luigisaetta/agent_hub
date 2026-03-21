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
# (17/03/2026) Note that some features are only available in preprod for now,
# so you might want to switch to preprod to try them out.
IS_PREPROD = True

# Production endpoints are the source of truth.
PROD_BASE_URL = (
    f"https://inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
)
PROD_CP_BASE_URL = (
    f"https://generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
)

if IS_PREPROD:
    # Preprod endpoints are derived from prod by prefixing the hostname with "ppe.".
    BASE_URL = PROD_BASE_URL.replace("https://", "https://ppe.", 1)
    CP_BASE_URL = PROD_CP_BASE_URL.replace("https://", "https://ppe.", 1)
else:
    BASE_URL = PROD_BASE_URL
    CP_BASE_URL = PROD_CP_BASE_URL

# to test integration with langfuse
# LANGFUSE_BASE_URL = "https://cloud.langfuse.com"
# this is langfuse hosted on OCI
LANGFUSE_BASE_URL = "http://130.61.176.103:3000"
