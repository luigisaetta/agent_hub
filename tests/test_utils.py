"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Unit tests for utility helpers in the common package.
"""

from __future__ import annotations

from types import SimpleNamespace


def test_print_streamed_output_collects_only_text_deltas(reload_module, capsys):
    """Collect only output_text delta events and print concatenated text."""
    output = reload_module("common.output")

    stream = [
        SimpleNamespace(type="response.output_text.delta", delta="Hel"),
        SimpleNamespace(type="response.reasoning.delta", delta="ignored"),
        SimpleNamespace(type="response.output_text.delta", delta="lo"),
    ]

    result = output.print_streamed_output(stream)
    captured = capsys.readouterr()

    assert result == "Hello"
    assert captured.out == "Hello"


def test_get_inference_client_uses_openai_with_expected_kwargs(reload_module):
    """Build inference client with API key and project settings."""
    clients = reload_module("common.clients")

    client = clients.get_inference_client()

    assert client.kwargs["base_url"] == clients.BASE_URL
    assert client.kwargs["api_key"] == clients.KEY1
    assert client.kwargs["project"] == clients.PROJECT_ID


def test_get_control_plane_client_uses_signed_http_client(reload_module):
    """Build control-plane client with session-auth and compartment headers."""
    clients = reload_module("common.clients")

    client = clients.get_control_plane_client()

    assert client.kwargs["base_url"] == clients.CP_BASE_URL
    assert client.kwargs["api_key"] == "unused"
    assert "default_headers" not in client.kwargs
    assert (
        client.kwargs["http_client"].headers["opc-compartment-id"]
        == clients.COMPARTMENT_ID
    )
    assert client.kwargs["http_client"].auth.__class__.__name__ == "FakeOciSessionAuth"


def test_print_header_outputs_consistent_banner(reload_module, capsys):
    """Print header with separators and contextual label."""
    output = reload_module("common.output")

    output.print_header("files", "project")
    captured = capsys.readouterr()

    assert "List of the files in the project" in captured.out
    assert captured.out.count("=") >= 40


def test_extract_provider_name_returns_prefix_before_first_dot(reload_module):
    """Extract provider from model id using dotted provider.model convention."""
    models = reload_module("common.models")

    provider = models.extract_provider_name("google.gemini-2.5-pro")

    assert provider == "google"


def test_extract_provider_name_rejects_invalid_or_empty_model_id(reload_module):
    """Invalid model identifiers should raise a ValueError."""
    models = reload_module("common.models")

    for invalid_model_id in ("", "   ", "gpt-5.2", ".gpt-5.2"):
        try:
            models.extract_provider_name(invalid_model_id)
            raised = False
        except ValueError:
            raised = True

        assert raised is True
