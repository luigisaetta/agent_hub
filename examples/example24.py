"""
Author: L. Saetta
Last modified: 2026-04-11
License: MIT

Description:
    Example script that obtains an OCI Identity Domain JWT token via
    OAuth2 Client Credentials and prints full JWT content.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from common.oci_jwt_token_client import OciJwtTokenClient

DEFAULT_ENV_FILE = "examples/.env.example24.local"


def _load_required_env(var_name: str) -> str:
    """Read one required environment variable or fail with a clear message."""
    value = (os.getenv(var_name) or "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value


def main() -> int:
    """Load config, call OCI domain, then print decoded JWT details."""
    parser = argparse.ArgumentParser(
        description="Get JWT token from OCI Identity Domain and decode it."
    )
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help="Path to local env file for this example.",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file)

    try:
        domain_url = _load_required_env("OCI_DOMAIN_URL")
        client_id = _load_required_env("OCI_CLIENT_ID")
        client_secret = _load_required_env("OCI_CLIENT_SECRET")
        scope = _load_required_env("OCI_SCOPE")

        token_client = OciJwtTokenClient(
            domain_url=domain_url,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
        )
        token_url, token_response = token_client.request_jwt_token(
            explicit_token_url=os.getenv("OCI_TOKEN_URL")
        )
        access_token, jwt_header, jwt_payload, signature = (
            token_client.parse_access_token(token_response)
        )

    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Token endpoint:", token_url)
    print("")
    print("Raw token response:")
    print(json.dumps(token_response, indent=2, ensure_ascii=False))
    print("")
    print("JWT access_token (raw):")
    print(access_token)
    print("")
    print("JWT header:")
    print(json.dumps(jwt_header, indent=2, ensure_ascii=False))
    print("")
    print("JWT payload:")
    print(json.dumps(jwt_payload, indent=2, ensure_ascii=False))
    print("")
    print("JWT signature (base64url):")
    print(signature)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
