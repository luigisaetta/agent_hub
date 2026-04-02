"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Test fixtures and lightweight dependency stubs shared across test modules.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import httpx
import pytest


@pytest.fixture(autouse=True)
def project_on_sys_path() -> None:
    """Ensure repo root is importable during tests."""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


@pytest.fixture(autouse=True)
def stub_external_sdk_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide simple stubs for SDK modules used by local helpers."""

    openai_mod = types.ModuleType("openai")

    class FakeOpenAI:  # pylint: disable=too-few-public-methods
        """Small stub replacing openai.OpenAI in tests."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    openai_mod.OpenAI = FakeOpenAI

    oci_genai_auth_mod = types.ModuleType("oci_genai_auth")

    class FakeOciSessionAuth(httpx.Auth):  # pylint: disable=too-few-public-methods
        """Small stub replacing OciSessionAuth in tests."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def auth_flow(self, request):
            yield request

    class FakeUserPrincipalSigner:  # pylint: disable=too-few-public-methods
        """Minimal signer stub exposed by FakeOciUserPrincipalAuth."""

    class FakeOciUserPrincipalAuth(
        httpx.Auth
    ):  # pylint: disable=too-few-public-methods
        """Small stub replacing OciUserPrincipalAuth in tests."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.signer = FakeUserPrincipalSigner()
            self.config = {
                "user": "ocid1.user.oc1..example",
                "tenancy": "ocid1.tenancy.oc1..example",
                "fingerprint": "aa:bb:cc:dd",
                "key_file": "~/.oci/oci_api_key.pem",
            }

        def auth_flow(self, request):
            yield request

    oci_genai_auth_mod.OciSessionAuth = FakeOciSessionAuth
    oci_genai_auth_mod.OciUserPrincipalAuth = FakeOciUserPrincipalAuth

    monkeypatch.setitem(sys.modules, "openai", openai_mod)
    monkeypatch.setitem(sys.modules, "oci_genai_auth", oci_genai_auth_mod)


@pytest.fixture
def reload_module():
    """Reload a module by name to pick up monkeypatches per test."""

    def _reload(name: str):
        """Reload and return a module by dotted name."""
        if name in sys.modules:
            del sys.modules[name]
        return importlib.import_module(name)

    return _reload
