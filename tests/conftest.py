"""Test fixtures and lightweight dependency stubs."""

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

    oci_openai_mod = types.ModuleType("oci_openai")

    class FakeOciSessionAuth(httpx.Auth):  # pylint: disable=too-few-public-methods
        """Small stub replacing OciSessionAuth in tests."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def auth_flow(self, request):
            yield request

    class FakeOciUserPrincipalAuth:  # pylint: disable=too-few-public-methods
        """Small stub replacing OciUserPrincipalAuth in tests."""

    class FakeOciOpenAI:  # pylint: disable=too-few-public-methods
        """Small stub replacing OciOpenAI in tests."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    oci_openai_mod.OciOpenAI = FakeOciOpenAI
    oci_openai_mod.OciSessionAuth = FakeOciSessionAuth
    oci_openai_mod.OciUserPrincipalAuth = FakeOciUserPrincipalAuth

    monkeypatch.setitem(sys.modules, "openai", openai_mod)
    monkeypatch.setitem(sys.modules, "oci_openai", oci_openai_mod)


@pytest.fixture
def reload_module():
    """Reload a module by name to pick up monkeypatches per test."""

    def _reload(name: str):
        """Reload and return a module by dotted name."""
        if name in sys.modules:
            del sys.modules[name]
        return importlib.import_module(name)

    return _reload
