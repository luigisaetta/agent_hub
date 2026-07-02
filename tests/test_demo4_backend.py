"""
Author: L. Saetta
Last modified: 2026-06-03
License: MIT

Description:
    Tests for Demo 4 file_search backend request construction.
"""

from __future__ import annotations

from types import SimpleNamespace


def _make_client(captured):
    """Create a fake client that captures Responses API kwargs."""

    def create(**kwargs):
        captured.update(kwargs)
        return iter(())

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def test_stream_rag_omits_temperature_for_unsupported_models(reload_module):
    """Demo4 should avoid temperature for models that reject the parameter."""
    backend = reload_module("demos.demo4.backend")

    for model_id in ("openai.gpt-5.5", "openai.gpt-5.6", "openai.gpt-5.6-mini"):
        captured = {}
        client = _make_client(captured)

        backend.stream_rag(
            client,
            model_id=model_id,
            user_prompt="Question?",
            conversation_id="conv-1",
        )

        assert "temperature" not in captured
        assert captured["max_output_tokens"] == backend.DEFAULT_MAX_OUTPUT_TOKENS
        assert captured["stream"] is True


def test_stream_rag_keeps_temperature_for_supported_models(reload_module):
    """Demo4 should keep temperature for models that support it."""
    backend = reload_module("demos.demo4.backend")
    captured = {}
    client = _make_client(captured)

    backend.stream_rag(
        client,
        model_id="openai.gpt-5.4",
        user_prompt="Question?",
        conversation_id="conv-1",
    )

    assert captured["temperature"] == backend.DEFAULT_TEMPERATURE
    assert captured["max_output_tokens"] == backend.DEFAULT_MAX_OUTPUT_TOKENS
