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
