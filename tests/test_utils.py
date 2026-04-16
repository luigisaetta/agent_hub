"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Unit tests for utility helpers in the common package.
"""

from __future__ import annotations

from types import SimpleNamespace
import httpx


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


def test_get_inference_client_uses_openai_with_expected_kwargs(
    reload_module, monkeypatch
):
    """Build inference client with API key and project settings by default."""
    monkeypatch.delenv("INFERENCE_AUTH_MODE", raising=False)
    clients = reload_module("common.clients")

    client = clients.get_inference_client()

    assert clients.BASE_URL.endswith("/openai/v1")
    assert "/20231130/openai/v1" not in clients.BASE_URL
    assert client.kwargs["base_url"] == clients.BASE_URL
    assert client.kwargs["api_key"] == clients.KEY1
    assert client.kwargs["project"] == clients.PROJECT_ID
    assert "http_client" not in client.kwargs


def test_get_inference_client_supports_user_principal_auth(reload_module, monkeypatch):
    """Build inference client with user-principal signer auth."""
    monkeypatch.setenv("INFERENCE_AUTH_MODE", "user_principal")
    clients = reload_module("common.clients")

    client = clients.get_inference_client()

    assert client.kwargs["base_url"] == clients.BASE_URL
    assert client.kwargs["api_key"] == "unused"
    assert client.kwargs["project"] == clients.PROJECT_ID
    assert client.kwargs["http_client"].auth.__class__.__name__ == (
        "FakeOciUserPrincipalAuth"
    )


def test_get_inference_client_supports_session_auth(reload_module, monkeypatch):
    """Build inference client with session signer auth."""
    monkeypatch.setenv("INFERENCE_AUTH_MODE", "session")
    clients = reload_module("common.clients")

    client = clients.get_inference_client()

    assert client.kwargs["base_url"] == clients.BASE_URL
    assert client.kwargs["api_key"] == "unused"
    assert client.kwargs["project"] == clients.PROJECT_ID
    assert client.kwargs["http_client"].auth.__class__.__name__ == "FakeOciSessionAuth"


def test_get_inference_client_rejects_invalid_auth_mode(reload_module, monkeypatch):
    """Reject unknown inference auth mode values."""
    monkeypatch.setenv("INFERENCE_AUTH_MODE", "invalid")
    clients = reload_module("common.clients")

    try:
        clients.get_inference_client()
    except ValueError as exc:
        assert "Invalid inference auth mode" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for invalid INFERENCE_AUTH_MODE")


def test_get_control_plane_client_uses_signed_http_client(reload_module):
    """Build control-plane client with default auth and compartment headers."""
    clients = reload_module("common.clients")

    client = clients.get_control_plane_client()

    assert client.kwargs["base_url"] == clients.CP_BASE_URL
    assert client.kwargs["api_key"] == "unused"
    assert "default_headers" not in client.kwargs
    assert (
        client.kwargs["http_client"].headers["opc-compartment-id"]
        == clients.COMPARTMENT_ID
    )
    assert (
        client.kwargs["http_client"].auth.__class__.__name__
        == "FakeOciUserPrincipalAuth"
    )


def test_get_control_plane_client_supports_user_principal_auth(reload_module):
    """Build control-plane client with user-principal auth when requested."""
    clients = reload_module("common.clients")

    client = clients.get_control_plane_client(auth_mode="user_principal")

    assert client.kwargs["http_client"].auth.__class__.__name__ == (
        "FakeOciUserPrincipalAuth"
    )


def test_get_control_plane_client_rejects_invalid_auth_mode(reload_module):
    """Reject unknown control-plane auth mode values."""
    clients = reload_module("common.clients")

    try:
        clients.get_control_plane_client(auth_mode="invalid")
    except ValueError as exc:
        assert "Invalid auth mode" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for invalid auth_mode")


def test_get_control_plane_client_reads_auth_mode_from_env(reload_module, monkeypatch):
    """Use session auth when OCI_AUTH_MODE=session."""
    monkeypatch.setenv("OCI_AUTH_MODE", "session")
    clients = reload_module("common.clients")

    client = clients.get_control_plane_client()

    assert client.kwargs["http_client"].auth.__class__.__name__ == "FakeOciSessionAuth"


def test_get_control_plane_client_rejects_session_profile_for_user_principal(
    reload_module, monkeypatch
):
    """Reject session-style profile when control-plane uses user_principal."""
    clients = reload_module("common.clients")

    class BadUserPrincipalAuth(httpx.Auth):  # pylint: disable=too-few-public-methods
        """Auth stub exposing a session-style config."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.config = {
                "user": "ocid1.user.oc1..example",
                "tenancy": "ocid1.tenancy.oc1..example",
                "fingerprint": "aa:bb:cc:dd",
                "key_file": "~/.oci/sessions/DEFAULT/oci_api_key.pem",
                "security_token_file": "~/.oci/sessions/DEFAULT/token",
            }

        def auth_flow(self, request):
            yield request

    monkeypatch.setattr(clients, "OciUserPrincipalAuth", BadUserPrincipalAuth)
    try:
        clients.get_control_plane_client(auth_mode="user_principal")
    except ValueError as exc:
        assert "looks like a session-auth profile" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for incompatible profile/auth mode")


def test_print_header_outputs_consistent_banner(reload_module, capsys):
    """Print header with separators and contextual label."""
    output = reload_module("common.output")

    output.print_header("files", "project")
    captured = capsys.readouterr()

    assert "List of the files in the project" in captured.out
    assert captured.out.count("=") >= 40


def test_print_runtime_config_includes_inference_auth_mode(
    reload_module, monkeypatch, capsys
):
    """Print runtime config with explicit inference auth mode."""
    monkeypatch.setenv("INFERENCE_AUTH_MODE", "user_principal")
    output = reload_module("common.output")

    output.print_runtime_config()
    captured = capsys.readouterr()

    assert "Runtime Configuration" in captured.out
    assert "INFERENCE_AUTH_MODE: user_principal" in captured.out


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
