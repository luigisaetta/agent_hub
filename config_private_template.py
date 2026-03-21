"""
Author: L. Saetta
Last modified: 2026-03-21
License: MIT

Description:
    Legacy template kept for backward compatibility.
    Secrets are now loaded from .env profile files (see .env.preprod-chicago, etc.).
    This file can still be used as a reference for required keys.
"""

# Required keys in each .env profile:
# PROJECT_ID=ocid1.generativeaiproject.oc1.<region>.<unique_id>
# KEY1=sk-<your-primary-api-key>
# KEY2=sk-<your-secondary-api-key>
# COMPARTMENT_ID=ocid1.compartment.oc1..<unique_id>
# LANGFUSE_SECRET_KEY=sk-lf-<your-secret-key>
# LANGFUSE_PUBLIC_KEY=pk-lf-<your-public-key>
# LF_PWD=<your-langfuse-password>
# VECTOR_STORE_ID=vs_<your-vector-store-id>
