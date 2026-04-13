"""
Author: L. Saetta
Last modified: 2026-04-12
License: MIT

Description:
    Tests for Hello World JWT client helpers.
"""

# pylint: disable=import-error,protected-access

from __future__ import annotations

import io
from pathlib import Path

from agents.hello_world import client_jwt


def test_iter_sse_events_parses_event_and_data_lines():
    """SSE parser should produce (event_type, data_text) tuples."""
    stream = io.BytesIO(
        (
            "event: response.output_text.delta\n"
            'data: {"type":"response.output_text.delta"}\n'
            "\n"
        ).encode("utf-8")
    )
    events = list(client_jwt._iter_sse_events(stream))

    assert len(events) == 1
    assert events[0][0] == "response.output_text.delta"
    assert "response.output_text.delta" in events[0][1]


def test_print_configuration_masks_secret_values(capsys):
    """Configuration output should mask secret fields."""
    config = {
        "env_file": "agents/hello_world/.env.client_jwt.local",
        "agent_url": "http://127.0.0.1:8080/chat",
        "oci_domain_url": "https://idcs.example.com:443",
        "oci_scope": "invoke",
        "oci_token_url": "",
        "oci_client_id": "my-client-id",
        "oci_client_secret": "super-secret-value",
        "request_timeout_seconds": 60,
        "debug_token_http_request": True,
    }

    client_jwt._print_configuration("Luca", config=config)
    out = capsys.readouterr().out

    assert "super-secret-value" not in out
    assert "my-client-id" not in out
    assert '"oci_client_secret": "<set>"' in out
    assert '"oci_client_id": "<set>"' in out


def test_load_runtime_config_reads_values_from_env_file(tmp_path: Path):
    """Runtime config should be loaded from dedicated env file."""
    env_file = tmp_path / ".env.client_jwt.local"
    env_file.write_text(
        "\n".join(
            [
                "AGENT_URL=http://127.0.0.1:8080/chat",
                "OCI_DOMAIN_URL=https://idcs.example.com:443",
                "OCI_CLIENT_ID=test-client-id",
                "OCI_CLIENT_SECRET=test-client-secret",
                "OCI_SCOPE=invoke",
                "REQUEST_TIMEOUT_SECONDS=45",
                "DEBUG_TOKEN_HTTP_REQUEST=false",
            ]
        ),
        encoding="utf-8",
    )

    config = client_jwt._load_runtime_config(  # pylint: disable=protected-access
        env_file=str(env_file)
    )

    assert config["agent_url"] == "http://127.0.0.1:8080/chat"
    assert config["oci_scope"] == "invoke"
    assert config["request_timeout_seconds"] == 45
    assert config["debug_token_http_request"] is False
