"""
Author: L. Saetta
Last modified: 2026-04-10
License: MIT

Description:
    Minimal CLI client for Hello World agent SSE endpoint.
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
    parser = argparse.ArgumentParser(description="Hello World agent test client.")
    parser.add_argument("name", help="Name to greet.")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8080/chat",
        help="Backend stream endpoint.",
    )
    return parser


def main() -> int:
    """Run CLI client and print final streamed greeting."""
    args = _build_arg_parser().parse_args()

    payload = {"name": args.name}
    request_data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        args.url,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

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

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
