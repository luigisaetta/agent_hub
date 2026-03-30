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
        return {"profile": profile_name}

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
    assert captured_kwargs["config"] == {"profile": "CUSTOM"}
    assert (
        "generativeai.eu-frankfurt-1.oci.oraclecloud.com"
        in captured_kwargs["service_endpoint"]
    )
    assert client.service_endpoint == captured_kwargs["service_endpoint"]
