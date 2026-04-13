"""
Author: L. Saetta
Last modified: 2026-04-13
License: MIT

Description:
    Minimal CLI client for Deep Agents local SSE endpoint.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Iterator


def _iter_sse_events(stream) -> Iterator[tuple[str, str]]:
    """Yield SSE events as (event_type, data_text)."""
    current_event = "message"
    data_lines: list[str] = []

    while True:
        raw_line = stream.readline()
        if not raw_line:
            if data_lines:
                yield current_event, "\n".join(data_lines)
            return

        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data_lines:
                yield current_event, "\n".join(data_lines)
            current_event = "message"
            data_lines = []
            continue

        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            current_event = line[6:].strip() or "message"
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())


def _build_arg_parser() -> argparse.ArgumentParser:
    """Return command-line parser."""
    parser = argparse.ArgumentParser(description="Deep Agents local test client.")
    parser.add_argument("prompt", help="User prompt.")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8090/chat",
        help="Backend stream endpoint.",
    )
    return parser


def main() -> int:
    """Run CLI client and print final streamed response."""
    args = _build_arg_parser().parse_args()

    request_data = json.dumps({"prompt": args.prompt}).encode("utf-8")
    request = urllib.request.Request(
        args.url,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    had_output = False
    error_message = ""

    try:
        with urllib.request.urlopen(request) as response:
            for event_type, data_text in _iter_sse_events(response):
                try:
                    event = json.loads(data_text)
                except json.JSONDecodeError:
                    continue

                payload_type = str(event.get("type", event_type))
                data = (
                    event.get("data", {}) if isinstance(event.get("data"), dict) else {}
                )

                if payload_type == "response.output_text.delta":
                    delta = str(data.get("delta", ""))
                    if delta:
                        print(delta)
                        had_output = True
                    continue

                if payload_type == "response.error":
                    message = str(data.get("message", "Unknown backend error")).strip()
                    error_message = message or "Unknown backend error"
                    print(f"Backend error: {error_message}", file=sys.stderr)
                    continue

                if payload_type == "response.completed":
                    completed_error = str(data.get("error", "")).strip()
                    if completed_error:
                        error_message = completed_error

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    if error_message:
        return 1
    if not had_output:
        print("No output received from server.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
