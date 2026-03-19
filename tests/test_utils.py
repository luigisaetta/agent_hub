"""Unit tests for utility helpers in common package."""

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


def test_get_client_production_uses_openai_with_expected_kwargs(reload_module):
    """Build production client with API key and project settings."""
    clients = reload_module("common.clients")

    client = clients.get_client(is_preproduction=False)

    assert client.kwargs["base_url"] == clients.BASE_URL
    assert client.kwargs["api_key"] == clients.KEY1
    assert client.kwargs["project"] == clients.PROJECT_ID


def test_get_client_preproduction_uses_oci_client_with_ppe_url(reload_module):
    """Build preproduction client with user principal auth and PPE endpoint."""
    clients = reload_module("common.clients")

    client = clients.get_client(is_preproduction=True)

    assert client.kwargs["base_url"] == clients.BASE_URL
    assert "ppe.inference.generativeai." in client.kwargs["base_url"]
    assert f".{clients.REGION}.oci.oraclecloud.com" in client.kwargs["base_url"]
    assert client.kwargs["compartment_id"] == clients.COMPARTMENT_ID
    assert client.kwargs["auth"].__class__.__name__ == "FakeOciUserPrincipalAuth"


def test_print_header_outputs_consistent_banner(reload_module, capsys):
    """Print header with separators and contextual label."""
    output = reload_module("common.output")

    output.print_header("files", "project")
    captured = capsys.readouterr()

    assert "List of the files in the project" in captured.out
    assert captured.out.count("=") >= 40
