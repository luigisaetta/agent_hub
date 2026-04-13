"""
Author: L. Saetta
Last modified: 2026-04-12
License: MIT

Description:
    JWT-enabled CLI client for Hello World agent SSE endpoint.
    It retrieves a JWT access token from OCI IAM/Identity Domain
    and uses it as Bearer token when invoking the agent endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Iterator

from dotenv import load_dotenv

from common.oci_jwt_token_client import OciJwtTokenClient

DEFAULT_ENV_FILE = "agents/hello_world/.env.client_jwt.local"


def _iter_sse_events(stream) -> Iterator[tuple[str, str]]:
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


def _build_arg_parser() -> argparse.ArgumentParser:
    """Return command-line parser."""
    parser = argparse.ArgumentParser(description="Hello World JWT test client.")
    parser.add_argument("name", help="Name to greet.")
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help="Path to env file for JWT client configuration.",
    )
    return parser


def _load_required_env(var_name: str) -> str:
    """Read one required environment variable or fail with a clear message."""
    value = (os.getenv(var_name) or "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value


def _load_runtime_config(*, env_file: str) -> dict:
    """Load runtime configuration from dedicated env file and environment."""
    load_dotenv(env_file)

    timeout_label = (os.getenv("REQUEST_TIMEOUT_SECONDS") or "60").strip()
    try:
        request_timeout_seconds = int(timeout_label)
    except ValueError as exc:
        raise ValueError(
            "Invalid REQUEST_TIMEOUT_SECONDS value: expected integer."
        ) from exc

    debug_http_request = (
        os.getenv("DEBUG_TOKEN_HTTP_REQUEST") or "true"
    ).strip().lower() in {"1", "true", "yes", "on"}

    return {
        "agent_url": _load_required_env("AGENT_URL"),
        "oci_domain_url": _load_required_env("OCI_DOMAIN_URL"),
        "oci_client_id": _load_required_env("OCI_CLIENT_ID"),
        "oci_client_secret": _load_required_env("OCI_CLIENT_SECRET"),
        "oci_scope": _load_required_env("OCI_SCOPE"),
        "oci_token_url": (os.getenv("OCI_TOKEN_URL") or "").strip(),
        "request_timeout_seconds": request_timeout_seconds,
        "debug_token_http_request": debug_http_request,
        "env_file": env_file,
    }


def _masked(value: str) -> str:
    """Mask secrets in logs while still showing if they are configured."""
    normalized = value.strip()
    return "<set>" if normalized else "<missing>"


def _print_configuration(name: str, *, config: dict) -> None:
    """Print non-sensitive configuration used by this client."""
    config_snapshot = {
        "name": name,
        "env_file": config["env_file"],
        "agent_url": config["agent_url"],
        "oci_domain_url": config["oci_domain_url"],
        "oci_scope": config["oci_scope"],
        "oci_token_url": config["oci_token_url"] or "<auto>",
        "oci_client_id": _masked(str(config["oci_client_id"])),
        "oci_client_secret": _masked(str(config["oci_client_secret"])),
        "request_timeout_seconds": config["request_timeout_seconds"],
        "debug_token_http_request": config["debug_token_http_request"],
    }
    print("Configuration (secrets masked):")
    print(json.dumps(config_snapshot, indent=2, ensure_ascii=False))


def _get_access_token(*, config: dict) -> tuple[str, str, dict]:
    """Request OCI JWT token and return endpoint, token, and decoded payload."""
    token_client = OciJwtTokenClient(
        domain_url=str(config["oci_domain_url"]),
        client_id=str(config["oci_client_id"]),
        client_secret=str(config["oci_client_secret"]),
        scope=str(config["oci_scope"]),
    )
    token_url, token_response = token_client.request_jwt_token(
        explicit_token_url=str(config["oci_token_url"]) or None,
        debug_http_request=bool(config["debug_token_http_request"]),
    )
    access_token, _, jwt_payload, _ = token_client.parse_access_token(token_response)
    return token_url, access_token, jwt_payload


def _invoke_agent(*, config: dict, name: str, access_token: str) -> str:
    """Call agent endpoint using Bearer JWT and return final output text."""
    payload = {"name": name}
    request_data = json.dumps(payload).encode("utf-8")
    
    # here we do the call to the agent endpoint, 
    # passing the JWT access token in the Authorization header
    # 1 Create the reques
    request = urllib.request.Request(
        str(config["agent_url"]),
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )

    final_output_text = ""
    # 2 Do the call and extract output from response
    with urllib.request.urlopen(
        request, timeout=int(config["request_timeout_seconds"])
    ) as response:
        for event_type, data_text in _iter_sse_events(response):
            try:
                event = json.loads(data_text)
            except json.JSONDecodeError:
                continue

            payload_type = str(event.get("type", event_type))
            data = event.get("data", {}) if isinstance(event.get("data"), dict) else {}

            if payload_type == "response.output_text.delta":
                delta = str(data.get("delta", ""))
                if delta:
                    print(delta)

            if payload_type == "response.completed":
                final_output_text = str(data.get("output_text", "")).strip()
                break

    return final_output_text


def main() -> int:
    """Run JWT-enabled client and print streamed greeting."""
    args = _build_arg_parser().parse_args()

    try:
        config = _load_runtime_config(env_file=args.env_file)
        _print_configuration(args.name, config=config)
        print("")
        print("Step 1/4: Requesting JWT token from OCI IAM...")
        token_url, access_token, jwt_payload = _get_access_token(config=config)
        print("")
        print(
            "Step 2/4: JWT token obtained successfully "
            f"(token endpoint: {token_url}, token length: {len(access_token)})."
        )
        print("JWT payload:")
        print(json.dumps(jwt_payload, indent=2, ensure_ascii=False))

        print("")
        print("Step 3/4: Invoking agent endpoint with Authorization Bearer token...")
        final_output_text = _invoke_agent(
            config=config,
            name=args.name,
            access_token=access_token,
        )
        print("")
        print("Step 4/4: Agent response received.")
        print(f"Agent response: {final_output_text or '<empty>'}")

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
