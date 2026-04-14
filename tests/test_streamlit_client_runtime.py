"""
Author: L. Saetta
Last modified: 2026-04-14
License: MIT

Description:
    Unit tests for Streamlit generalized client runtime helpers.
"""

# pylint: disable=import-error

from __future__ import annotations

import io

import pytest

from agents.streamlit_client import runtime


def test_derive_agent_url_from_application_id() -> None:
    """URL should be derived from region + app id using runtime template."""
    url = runtime.derive_agent_url(
        region="us-chicago-1",
        genai_application_id="ocid1.generativeaihostedapplication.oc1..aaaa",
    )

    assert "inference.generativeai.us-chicago-1.oci.oraclecloud.com" in url
    assert (
        "/hostedApplications/ocid1.generativeaihostedapplication.oc1..aaaa/actions/invoke/chat"
        in url
    )


def test_derive_agent_url_with_custom_endpoint_path() -> None:
    """Derived URL should use custom endpoint path when provided."""
    url = runtime.derive_agent_url(
        region="us-chicago-1",
        genai_application_id="ocid1.generativeaihostedapplication.oc1..aaaa",
        endpoint_path="/chat",
    )
    assert url.endswith(
        "/hostedApplications/ocid1.generativeaihostedapplication.oc1..aaaa/chat"
    )


def test_derive_agent_url_passthrough_when_full_url_is_provided() -> None:
    """If user inputs an URL directly, it should be returned unchanged."""
    original = "https://custom.endpoint.example.com/chat"
    assert (
        runtime.derive_agent_url(
            region="us-chicago-1",
            genai_application_id=original,
        )
        == original
    )


def test_parse_payload_text_parses_json_object() -> None:
    """JSON object in textarea should be parsed as dict."""
    payload = runtime.parse_payload_text('{"user_request": "ciao"}')
    assert payload == {"user_request": "ciao"}


def test_parse_payload_text_wraps_plain_text() -> None:
    """Plain text payload should fallback to default request schema."""
    payload = runtime.parse_payload_text("hello world")
    assert payload == {"user_request": "hello world"}


def test_parse_payload_text_rejects_empty_input() -> None:
    """Empty payload must fail with a clear validation error."""
    with pytest.raises(ValueError, match="Payload is empty"):
        runtime.parse_payload_text("   ")


def test_iter_sse_events_parses_single_message() -> None:
    """SSE stream with one event should return expected tuple."""
    stream = io.BytesIO(
        (
            "event: response.output_text.delta\n"
            'data: {"type":"response.output_text.delta","data":{"delta":"Hi"}}\n'
            "\n"
        ).encode("utf-8")
    )
    events = list(runtime.iter_sse_events(stream))

    assert len(events) == 1
    assert events[0][0] == "response.output_text.delta"
    assert "response.output_text.delta" in events[0][1]


def test_select_important_jwt_claims_filters_payload() -> None:
    """Only expected important claims should be returned."""
    payload = {
        "aud": "my-audience",
        "scope": "urn:test:scope",
        "exp": 123456,
        "iat": 123000,
        "iss": "issuer",
        "sub": "subject",
        "client_id": "abc",
        "jti": "token-id",
        "extra": "ignore-me",
    }
    selected = runtime.select_important_jwt_claims(payload)

    assert selected["aud"] == "my-audience"
    assert selected["scope"] == "urn:test:scope"
    assert "extra" not in selected
