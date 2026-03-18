"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Shared endpoint configuration values used by example scripts.
"""

REGION = "eu-frankfurt-1"

# this switch is here to decide if you want to try in preprod
# or in production environment.
# (17/03/2026)Note that some features are only available in preprod for now, 
# so you might want to switch to preprod to try them out.
IS_PREPROD = False

if IS_PREPROD:
    BASE_URL = f"https://ppe.inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
else:
    BASE_URL = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1"
