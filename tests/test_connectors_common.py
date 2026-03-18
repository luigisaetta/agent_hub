"""Unit tests for shared connector utilities."""

from __future__ import annotations

import sys
import types
from typing import Any


def test_get_oci_genai_service_endpoint_preprod_and_prod(reload_module, monkeypatch):
    """Service endpoint helper should switch correctly by environment."""

    def from_file(*, profile_name):
        """Return minimal config payload for a given profile."""
        return {"profile": profile_name}

    def genai_client(**kwargs):
        """Return a fake OCI client object storing constructor kwargs."""
        return types.SimpleNamespace(kwargs=kwargs)

    oci_stub = types.ModuleType("oci")
    oci_stub.config = types.SimpleNamespace(from_file=from_file)
    oci_stub.generative_ai = types.SimpleNamespace(GenerativeAiClient=genai_client)
    monkeypatch.setitem(sys.modules, "oci", oci_stub)

    module = reload_module("common.clients")

    assert module.get_oci_genai_service_endpoint("eu-frankfurt-1", True).startswith(
        "https://ppe."
    )
    assert module.get_oci_genai_service_endpoint("eu-frankfurt-1", False).startswith(
        "https://generativeai."
    )


def test_build_oci_genai_client_uses_profile_and_computed_endpoint(
    reload_module, monkeypatch
):
    """build_oci_genai_client should feed config and selected endpoint into OCI client."""
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

    oci_stub = types.ModuleType("oci")
    oci_stub.config = types.SimpleNamespace(from_file=from_file)
    oci_stub.generative_ai = types.SimpleNamespace(GenerativeAiClient=genai_client)

    monkeypatch.setitem(sys.modules, "oci", oci_stub)
    module = reload_module("common.clients")

    client = module.build_oci_genai_client(
        profile="CUSTOM", region="eu-frankfurt-1", use_preprod=True
    )

    assert captured_profile["value"] == "CUSTOM"
    assert captured_kwargs["config"] == {"profile": "CUSTOM"}
    assert (
        "ppe.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
        in captured_kwargs["service_endpoint"]
    )
    assert client.service_endpoint == captured_kwargs["service_endpoint"]
