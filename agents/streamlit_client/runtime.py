"""
Author: L. Saetta
Last modified: 2026-04-14
License: MIT

Description:
    Shared runtime helpers for Streamlit client that invokes OCI Enterprise AI
    agent endpoints, optionally with JWT client-credentials authentication.
"""

# pylint: disable=import-error

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Iterator

from common.oci_jwt_token_client import OciJwtTokenClient

DEFAULT_AGENT_API_VERSION = "20251112"


def derive_agent_url(
    *,
    region: str,
    genai_application_id: str,
    endpoint_path: str = "/actions/invoke/chat",
) -> str:
    """Return runtime chat URL derived from region and application id.

    If the provided value is already an HTTP(S) URL, it is returned as-is.
    """
    normalized = genai_application_id.strip()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized

    app_id = normalized.split("/")[-1]
    cleaned_endpoint_path = endpoint_path.strip() or "/actions/invoke/chat"
    if not cleaned_endpoint_path.startswith("/"):
        cleaned_endpoint_path = "/" + cleaned_endpoint_path
    return (
        "https://"
        f"inference.generativeai.{region.strip()}.oci.oraclecloud.com/"
        f"{DEFAULT_AGENT_API_VERSION}/hostedApplications/{app_id}{cleaned_endpoint_path}"
    )


def parse_payload_text(payload_text: str) -> dict[str, Any] | list[Any]:
    """Parse payload from textarea content.

    Accepts JSON payload; if not valid JSON, wraps text into the default schema.
    """
    cleaned = payload_text.strip()
    if not cleaned:
        raise ValueError("Payload is empty.")

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, (dict, list)):
            return parsed
        raise ValueError("Payload JSON must be an object or array.")
    except json.JSONDecodeError:
        return {"user_request": cleaned}


def iter_sse_events(stream) -> Iterator[tuple[str, str]]:
    """Yield SSE events as (event_type, data_text)."""
    current_event = "message"
    data_lines: list[str] = []

    while True:
        raw_line = stream.readline()
        if not raw_line:
            if data_lines:
                yield current_event, "\n".join(data_lines)
            return

        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data_lines:
                yield current_event, "\n".join(data_lines)
            current_event = "message"
            data_lines = []
            continue

        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            current_event = line[6:].strip() or "message"
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())


def request_access_token(
    *,
    token_config: dict[str, str],
) -> tuple[str, str, dict[str, Any]]:
    """Request and parse access token from OCI Identity Domain."""
    oci_domain_url = str(token_config.get("oci_domain_url", "")).strip()
    oci_client_id = str(token_config.get("oci_client_id", "")).strip()
    oci_client_secret = str(token_config.get("oci_client_secret", "")).strip()
    oci_scope = str(token_config.get("oci_scope", "")).strip()
    oci_token_url = str(token_config.get("oci_token_url", "")).strip()

    token_client = OciJwtTokenClient(
        domain_url=oci_domain_url,
        client_id=oci_client_id,
        client_secret=oci_client_secret,
        scope=oci_scope,
    )
    token_url, token_response = token_client.request_jwt_token(
        explicit_token_url=oci_token_url or None,
    )
    access_token, _, jwt_payload, _ = token_client.parse_access_token(token_response)
    return token_url, access_token, jwt_payload


def select_important_jwt_claims(jwt_payload: dict[str, Any]) -> dict[str, Any]:
    """Return only relevant JWT claims for UI/debug visibility."""
    important_keys = (
        "aud",
        "scope",
        "exp",
        "iat",
        "iss",
        "sub",
        "client_id",
        "jti",
    )
    return {
        key: jwt_payload[key]
        for key in important_keys
        if key in jwt_payload and jwt_payload[key] not in ("", None)
    }


def invoke_agent(
    *,
    agent_url: str,
    payload: dict[str, Any] | list[Any],
    request_timeout_seconds: int,
    access_token: str = "",
    on_delta: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Invoke agent SSE endpoint and return final output plus parsed events."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    if access_token.strip():
        headers["Authorization"] = f"Bearer {access_token.strip()}"

    request = urllib.request.Request(
        agent_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    deltas: list[str] = []
    final_output_text = ""
    events: list[dict[str, Any]] = []

    try:
        with urllib.request.urlopen(
            request, timeout=request_timeout_seconds
        ) as response:
            for event_type, data_text in iter_sse_events(response):
                try:
                    event = json.loads(data_text)
                except json.JSONDecodeError:
                    continue

                payload_type = str(event.get("type", event_type))
                event_data = event.get("data", {})
                if not isinstance(event_data, dict):
                    event_data = {}

                events.append(
                    {
                        "event_type": event_type,
                        "payload_type": payload_type,
                        "data": event_data,
                    }
                )

                if payload_type == "response.output_text.delta":
                    delta = str(event_data.get("delta", ""))
                    if delta:
                        deltas.append(delta)
                        if on_delta is not None:
                            on_delta("".join(deltas))

                if payload_type == "response.completed":
                    final_output_text = str(event_data.get("output_text", "")).strip()

                if payload_type == "response.error":
                    raise RuntimeError(
                        str(event_data.get("message", "Unknown response.error"))
                    )

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error: {exc}") from exc

    if not final_output_text:
        final_output_text = "".join(deltas).strip()

    return {
        "final_output_text": final_output_text,
        "events": events,
    }
