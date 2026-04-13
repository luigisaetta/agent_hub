"""
Author: L. Saetta
Last modified: 2026-04-12
License: MIT

Description:
    Shared OCI Identity Domain JWT token client used by examples and scripts.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request


class OciJwtTokenClient:
    """Request and parse JWT tokens from OCI Identity Domain."""

    def __init__(
        self, *, domain_url: str, client_id: str, client_secret: str, scope: str
    ) -> None:
        self.domain_url = domain_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        print("Scope requested:", scope)

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
        self,
        *,
        explicit_token_url: str | None = None,
        debug_http_request: bool = False,
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
        if debug_http_request:
            self._print_full_http_request(request=request, payload=payload)

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

    @staticmethod
    def _print_full_http_request(
        *, request: urllib.request.Request, payload: bytes
    ) -> None:
        """Print a full HTTP request snapshot to help troubleshoot auth issues."""
        print("")
        print("DEBUG - Full HTTP request to token endpoint:")
        print(f"{request.get_method()} {request.full_url} HTTP/1.1")
        for header_name, header_value in request.header_items():
            print(f"{header_name}: {header_value}")
        print("")
        print(payload.decode("utf-8", errors="replace"))
