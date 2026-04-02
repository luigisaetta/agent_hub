"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Unit tests for shared connector and OCI client utilities.
"""

from __future__ import annotations

import sys
import types
from typing import Any


def test_get_oci_genai_service_endpoint_returns_prod_url(reload_module, monkeypatch):
    """Service endpoint helper should return the production endpoint."""

    def from_file(*, profile_name):
        """Return minimal config payload for a given profile."""
        return {"profile": profile_name}

    def genai_client(**kwargs):
        """Return a fake OCI client object storing constructor kwargs."""
        return types.SimpleNamespace(kwargs=kwargs)

    class FakeSecurityTokenSigner:  # pylint: disable=too-few-public-methods
        """Minimal signer stub used by module import wiring."""

    oci_stub = types.ModuleType("oci")
    oci_config_stub = types.ModuleType("oci.config")
    oci_config_stub.from_file = from_file
    oci_generative_ai_stub = types.ModuleType("oci.generative_ai")
    oci_generative_ai_stub.GenerativeAiClient = genai_client
    oci_auth_stub = types.ModuleType("oci.auth")
    oci_auth_signers_stub = types.ModuleType("oci.auth.signers")
    oci_auth_signers_stub.SecurityTokenSigner = FakeSecurityTokenSigner
    oci_signer_stub = types.ModuleType("oci.signer")
    oci_signer_stub.load_private_key_from_file = lambda _path: None

    oci_stub.config = oci_config_stub
    oci_stub.generative_ai = oci_generative_ai_stub
    oci_stub.auth = oci_auth_stub
    oci_stub.signer = oci_signer_stub
    oci_auth_stub.signers = oci_auth_signers_stub

    monkeypatch.setitem(sys.modules, "oci", oci_stub)
    monkeypatch.setitem(sys.modules, "oci.config", oci_config_stub)
    monkeypatch.setitem(sys.modules, "oci.generative_ai", oci_generative_ai_stub)
    monkeypatch.setitem(sys.modules, "oci.auth", oci_auth_stub)
    monkeypatch.setitem(sys.modules, "oci.auth.signers", oci_auth_signers_stub)
    monkeypatch.setitem(sys.modules, "oci.signer", oci_signer_stub)

    module = reload_module("common.clients")

    assert module.get_oci_genai_service_endpoint("eu-frankfurt-1").startswith(
        "https://generativeai."
    )


def test_build_oci_genai_client_uses_profile_and_computed_endpoint(
    reload_module, monkeypatch
):
    """build_oci_genai_client should feed config and endpoint into OCI client."""
    captured_profile: dict[str, str | None] = {"value": None}
    captured_kwargs: dict[str, Any] = {}

    def from_file(*, profile_name):
        """Capture profile name and return fake config dict."""
        captured_profile["value"] = profile_name
        return {
            "profile": profile_name,
            "user": "ocid1.user.oc1..example",
            "tenancy": "ocid1.tenancy.oc1..example",
            "fingerprint": "aa:bb:cc:dd",
            "key_file": "~/.oci/oci_api_key.pem",
        }

    def genai_client(**kwargs):
        """Capture constructor kwargs and return fake client object."""
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return types.SimpleNamespace(**kwargs)

    class FakeSecurityTokenSigner:  # pylint: disable=too-few-public-methods
        """Minimal signer stub used by module import wiring."""

    oci_stub = types.ModuleType("oci")
    oci_config_stub = types.ModuleType("oci.config")
    oci_config_stub.from_file = from_file
    oci_generative_ai_stub = types.ModuleType("oci.generative_ai")
    oci_generative_ai_stub.GenerativeAiClient = genai_client
    oci_auth_stub = types.ModuleType("oci.auth")
    oci_auth_signers_stub = types.ModuleType("oci.auth.signers")
    oci_auth_signers_stub.SecurityTokenSigner = FakeSecurityTokenSigner
    oci_signer_stub = types.ModuleType("oci.signer")
    oci_signer_stub.load_private_key_from_file = lambda _path: None

    oci_stub.config = oci_config_stub
    oci_stub.generative_ai = oci_generative_ai_stub
    oci_stub.auth = oci_auth_stub
    oci_stub.signer = oci_signer_stub
    oci_auth_stub.signers = oci_auth_signers_stub

    monkeypatch.setitem(sys.modules, "oci", oci_stub)
    monkeypatch.setitem(sys.modules, "oci.config", oci_config_stub)
    monkeypatch.setitem(sys.modules, "oci.generative_ai", oci_generative_ai_stub)
    monkeypatch.setitem(sys.modules, "oci.auth", oci_auth_stub)
    monkeypatch.setitem(sys.modules, "oci.auth.signers", oci_auth_signers_stub)
    monkeypatch.setitem(sys.modules, "oci.signer", oci_signer_stub)
    module = reload_module("common.clients")

    client = module.build_oci_genai_client(profile="CUSTOM", region="eu-frankfurt-1")

    assert captured_profile["value"] == "CUSTOM"
    assert captured_kwargs["config"]["profile"] == "CUSTOM"
    assert (
        "generativeai.eu-frankfurt-1.oci.oraclecloud.com"
        in captured_kwargs["service_endpoint"]
    )
    assert client.service_endpoint == captured_kwargs["service_endpoint"]


def test_build_oci_genai_client_uses_user_principal_signer(reload_module, monkeypatch):
    """build_oci_genai_client should use OciUserPrincipalAuth signer when requested."""
    captured_kwargs: dict[str, Any] = {}

    def from_file(*, profile_name):
        """Return fake config payload for a given profile."""
        return {
            "profile": profile_name,
            "user": "ocid1.user.oc1..example",
            "tenancy": "ocid1.tenancy.oc1..example",
            "fingerprint": "aa:bb:cc:dd",
            "key_file": "~/.oci/oci_api_key.pem",
        }

    def genai_client(**kwargs):
        """Capture constructor kwargs and return fake client object."""
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return types.SimpleNamespace(**kwargs)

    class FakeSecurityTokenSigner:  # pylint: disable=too-few-public-methods
        """Minimal signer stub used by module import wiring."""

    oci_stub = types.ModuleType("oci")
    oci_config_stub = types.ModuleType("oci.config")
    oci_config_stub.from_file = from_file
    oci_generative_ai_stub = types.ModuleType("oci.generative_ai")
    oci_generative_ai_stub.GenerativeAiClient = genai_client
    oci_auth_stub = types.ModuleType("oci.auth")
    oci_auth_signers_stub = types.ModuleType("oci.auth.signers")
    oci_auth_signers_stub.SecurityTokenSigner = FakeSecurityTokenSigner
    oci_signer_stub = types.ModuleType("oci.signer")
    oci_signer_stub.load_private_key_from_file = lambda _path: None

    oci_stub.config = oci_config_stub
    oci_stub.generative_ai = oci_generative_ai_stub
    oci_stub.auth = oci_auth_stub
    oci_stub.signer = oci_signer_stub
    oci_auth_stub.signers = oci_auth_signers_stub

    monkeypatch.setitem(sys.modules, "oci", oci_stub)
    monkeypatch.setitem(sys.modules, "oci.config", oci_config_stub)
    monkeypatch.setitem(sys.modules, "oci.generative_ai", oci_generative_ai_stub)
    monkeypatch.setitem(sys.modules, "oci.auth", oci_auth_stub)
    monkeypatch.setitem(sys.modules, "oci.auth.signers", oci_auth_signers_stub)
    monkeypatch.setitem(sys.modules, "oci.signer", oci_signer_stub)

    module = reload_module("common.clients")
    module.build_oci_genai_client(auth_mode="user_principal")

    assert captured_kwargs["signer"].__class__.__name__ == "FakeUserPrincipalSigner"


def test_build_oci_genai_client_rejects_invalid_auth_mode(reload_module, monkeypatch):
    """build_oci_genai_client should raise ValueError for unknown auth mode."""

    def from_file(*, profile_name):
        """Return fake config payload for a given profile."""
        return {
            "profile": profile_name,
            "user": "ocid1.user.oc1..example",
            "tenancy": "ocid1.tenancy.oc1..example",
            "fingerprint": "aa:bb:cc:dd",
            "key_file": "~/.oci/oci_api_key.pem",
        }

    def genai_client(**kwargs):
        """Return fake client object."""
        return types.SimpleNamespace(**kwargs)

    class FakeSecurityTokenSigner:  # pylint: disable=too-few-public-methods
        """Minimal signer stub used by module import wiring."""

    oci_stub = types.ModuleType("oci")
    oci_config_stub = types.ModuleType("oci.config")
    oci_config_stub.from_file = from_file
    oci_generative_ai_stub = types.ModuleType("oci.generative_ai")
    oci_generative_ai_stub.GenerativeAiClient = genai_client
    oci_auth_stub = types.ModuleType("oci.auth")
    oci_auth_signers_stub = types.ModuleType("oci.auth.signers")
    oci_auth_signers_stub.SecurityTokenSigner = FakeSecurityTokenSigner
    oci_signer_stub = types.ModuleType("oci.signer")
    oci_signer_stub.load_private_key_from_file = lambda _path: None

    oci_stub.config = oci_config_stub
    oci_stub.generative_ai = oci_generative_ai_stub
    oci_stub.auth = oci_auth_stub
    oci_stub.signer = oci_signer_stub
    oci_auth_stub.signers = oci_auth_signers_stub

    monkeypatch.setitem(sys.modules, "oci", oci_stub)
    monkeypatch.setitem(sys.modules, "oci.config", oci_config_stub)
    monkeypatch.setitem(sys.modules, "oci.generative_ai", oci_generative_ai_stub)
    monkeypatch.setitem(sys.modules, "oci.auth", oci_auth_stub)
    monkeypatch.setitem(sys.modules, "oci.auth.signers", oci_auth_signers_stub)
    monkeypatch.setitem(sys.modules, "oci.signer", oci_signer_stub)

    module = reload_module("common.clients")
    try:
        module.build_oci_genai_client(auth_mode="invalid")
    except ValueError as exc:
        assert "Invalid auth mode" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for invalid auth_mode")


def test_build_oci_genai_client_reads_auth_mode_from_env(reload_module, monkeypatch):
    """Use session auth when OCI_AUTH_MODE=session."""
    captured_kwargs: dict[str, Any] = {}

    def from_file(*, profile_name):
        """Return fake config payload containing session auth fields."""
        return {
            "profile": profile_name,
            "security_token_file": "~/fake-token",
            "key_file": "~/fake-key",
        }

    def genai_client(**kwargs):
        """Capture constructor kwargs and return fake client object."""
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return types.SimpleNamespace(**kwargs)

    class FakeSecurityTokenSigner:  # pylint: disable=too-few-public-methods
        """Minimal signer stub used by module import wiring."""

        def __init__(self, token, private_key):
            self.token = token
            self.private_key = private_key

    oci_stub = types.ModuleType("oci")
    oci_config_stub = types.ModuleType("oci.config")
    oci_config_stub.from_file = from_file
    oci_generative_ai_stub = types.ModuleType("oci.generative_ai")
    oci_generative_ai_stub.GenerativeAiClient = genai_client
    oci_auth_stub = types.ModuleType("oci.auth")
    oci_auth_signers_stub = types.ModuleType("oci.auth.signers")
    oci_auth_signers_stub.SecurityTokenSigner = FakeSecurityTokenSigner
    oci_signer_stub = types.ModuleType("oci.signer")
    oci_signer_stub.load_private_key_from_file = lambda _path: "fake-key"

    oci_stub.config = oci_config_stub
    oci_stub.generative_ai = oci_generative_ai_stub
    oci_stub.auth = oci_auth_stub
    oci_stub.signer = oci_signer_stub
    oci_auth_stub.signers = oci_auth_signers_stub

    monkeypatch.setitem(sys.modules, "oci", oci_stub)
    monkeypatch.setitem(sys.modules, "oci.config", oci_config_stub)
    monkeypatch.setitem(sys.modules, "oci.generative_ai", oci_generative_ai_stub)
    monkeypatch.setitem(sys.modules, "oci.auth", oci_auth_stub)
    monkeypatch.setitem(sys.modules, "oci.auth.signers", oci_auth_signers_stub)
    monkeypatch.setitem(sys.modules, "oci.signer", oci_signer_stub)
    monkeypatch.setenv("OCI_AUTH_MODE", "session")

    module = reload_module("common.clients")

    def fake_open(_path, encoding=None):  # noqa: ANN001
        """Return a fake token stream."""
        _ = encoding

        class _FakeHandle:  # pylint: disable=too-few-public-methods
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):  # noqa: ANN001,ANN201
                return False

            def read(self):
                """Return fake token content."""
                return "fake-token"

        return _FakeHandle()

    monkeypatch.setattr("builtins.open", fake_open)
    module.build_oci_genai_client()

    assert captured_kwargs["signer"].__class__.__name__ == "FakeSecurityTokenSigner"


def test_build_oci_genai_client_rejects_session_profile_for_user_principal(
    reload_module, monkeypatch
):
    """Reject session-style profile when user_principal auth is selected."""

    def from_file(*, profile_name):
        """Return fake session-style config payload."""
        return {
            "profile": profile_name,
            "user": "ocid1.user.oc1..example",
            "tenancy": "ocid1.tenancy.oc1..example",
            "fingerprint": "aa:bb:cc:dd",
            "key_file": "~/.oci/sessions/DEFAULT/oci_api_key.pem",
            "security_token_file": "~/.oci/sessions/DEFAULT/token",
        }

    def genai_client(**kwargs):
        """Return fake client object."""
        return types.SimpleNamespace(**kwargs)

    class FakeSecurityTokenSigner:  # pylint: disable=too-few-public-methods
        """Minimal signer stub used by module import wiring."""

    oci_stub = types.ModuleType("oci")
    oci_config_stub = types.ModuleType("oci.config")
    oci_config_stub.from_file = from_file
    oci_generative_ai_stub = types.ModuleType("oci.generative_ai")
    oci_generative_ai_stub.GenerativeAiClient = genai_client
    oci_auth_stub = types.ModuleType("oci.auth")
    oci_auth_signers_stub = types.ModuleType("oci.auth.signers")
    oci_auth_signers_stub.SecurityTokenSigner = FakeSecurityTokenSigner
    oci_signer_stub = types.ModuleType("oci.signer")
    oci_signer_stub.load_private_key_from_file = lambda _path: None

    oci_stub.config = oci_config_stub
    oci_stub.generative_ai = oci_generative_ai_stub
    oci_stub.auth = oci_auth_stub
    oci_stub.signer = oci_signer_stub
    oci_auth_stub.signers = oci_auth_signers_stub

    monkeypatch.setitem(sys.modules, "oci", oci_stub)
    monkeypatch.setitem(sys.modules, "oci.config", oci_config_stub)
    monkeypatch.setitem(sys.modules, "oci.generative_ai", oci_generative_ai_stub)
    monkeypatch.setitem(sys.modules, "oci.auth", oci_auth_stub)
    monkeypatch.setitem(sys.modules, "oci.auth.signers", oci_auth_signers_stub)
    monkeypatch.setitem(sys.modules, "oci.signer", oci_signer_stub)

    module = reload_module("common.clients")
    try:
        module.build_oci_genai_client(auth_mode="user_principal")
    except ValueError as exc:
        assert "looks like a session-auth profile" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for incompatible profile/auth mode")
