"""
Author: L. Saetta
Last modified: 2026-04-13
License: MIT

Description:
    Tests for Deep Agents local client helpers.
"""

# pylint: disable=import-error,protected-access

from __future__ import annotations

import io
import json

from agents.deep_agents01 import client


def test_iter_sse_events_parses_event_and_data_lines():
    """SSE parser should produce (event_type, data_text) tuples."""
    stream = io.BytesIO(
        (
            "event: response.output_text.delta\n"
            'data: {"type":"response.output_text.delta"}\n'
            "\n"
        ).encode("utf-8")
    )
    events = list(client._iter_sse_events(stream))

    assert len(events) == 1
    assert events[0][0] == "response.output_text.delta"
    assert "response.output_text.delta" in events[0][1]


def test_main_returns_one_and_prints_error_on_response_error(monkeypatch, capsys):
    """Client should surface backend error events and exit with code 1."""
    events = (
        "event: response.error\n"
        f"data: {json.dumps({'type': 'response.error', 'data': {'message': 'Not Found'}})}\n"
        "\n"
        "event: response.completed\n"
        f"data: {json.dumps({'type': 'response.completed', 'data': {'error': 'Not Found'}})}\n"
        "\n"
    ).encode("utf-8")

    class _FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

    def _fake_urlopen(request):  # pylint: disable=unused-argument
        return _FakeResponse(events)

    monkeypatch.setattr(client.urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.setattr(client.sys, "argv", ["client.py", "test"])

    exit_code = client.main()
    stderr = capsys.readouterr().err

    assert exit_code == 1
    assert "Backend error: Not Found" in stderr
