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
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

DEFAULT_ENV_FILE = "examples/.env.example24.local"


class OciJwtTokenClient:
    """Request and parse JWT tokens from OCI Identity Domain."""

    def __init__(
        self, *, domain_url: str, client_id: str, client_secret: str, scope: str
    ) -> None:
        self.domain_url = domain_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope

    @staticmethod
    def _decode_b64url_json(data: str) -> dict:
        """Decode one base64url JSON JWT segment into a dictionary."""
        padded = data + "=" * ((4 - len(data) % 4) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return json.loads(decoded_bytes.decode("utf-8"))

    def _resolve_token_url(self, explicit_token_url: str | None) -> str:
        """Resolve token endpoint from explicit value or OCI domain base URL."""
        if explicit_token_url:
            return explicit_token_url.strip()
        return f"{self.domain_url.rstrip('/')}/oauth2/v1/token"

    def request_jwt_token(
        self, *, explicit_token_url: str | None = None
    ) -> tuple[str, dict]:
        """Request JWT token and return the resolved token URL plus response payload."""
        token_url = self._resolve_token_url(explicit_token_url)
        payload = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "scope": self.scope,
            }
        ).encode("utf-8")

        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        basic_auth = base64.b64encode(credentials).decode("utf-8")

        request = urllib.request.Request(
            token_url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {basic_auth}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode("utf-8", errors="replace")
                return token_url, json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP error {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Connection error: {exc}") from exc

    def parse_access_token(self, token_response: dict) -> tuple[str, dict, dict, str]:
        """Extract and decode access token into raw token, header, payload, signature."""
        access_token = str(token_response.get("access_token", "")).strip()
        if not access_token:
            raise RuntimeError(
                "Token response does not include access_token. "
                f"Response: {json.dumps(token_response, ensure_ascii=False)}"
            )

        parts = access_token.split(".")
        if len(parts) != 3:
            raise RuntimeError(
                "Returned access_token is not a JWT (expected 3 segments)."
            )

        jwt_header = self._decode_b64url_json(parts[0])
        jwt_payload = self._decode_b64url_json(parts[1])
        signature = parts[2]
        return access_token, jwt_header, jwt_payload, signature


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
