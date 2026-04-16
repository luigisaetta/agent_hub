"""
Author: L. Saetta
Last modified: 2026-03-21
License: MIT

Description:
    Shared endpoint configuration values used by example scripts.
"""

import os

# Defaults can be overridden by AGENT_HUB_REGION.
DEFAULT_REGION = "us-chicago-1"
REGION = os.getenv("AGENT_HUB_REGION", DEFAULT_REGION)

# Shared default model used by examples.
# MODEL_ID = "openai.gpt-5.2"
MODEL_ID = "openai.gpt-5.4"
# MODEL_ID = "google.gemini-2.5-pro"
# MODEL_ID = "openai.gpt-oss-120b"

# Production endpoints (OpenAI-compatible API).
BASE_URL = (
    f"https://inference.generativeai.{REGION}.oci.oraclecloud.com/openai/v1"
)
CP_BASE_URL = f"https://generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"

# to test integration with langfuse
# LANGFUSE_BASE_URL = "https://cloud.langfuse.com"
# this is langfuse hosted on OCI
LANGFUSE_BASE_URL = "http://130.61.176.103:3000"
