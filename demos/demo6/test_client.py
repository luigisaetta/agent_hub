"""
Author: L. Saetta
Last modified: 2026-04-08
License: MIT

Description:
    Minimal CLI client for Demo 6 backend SSE stream.
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
    parser = argparse.ArgumentParser(description="Demo6 SSE test client.")
    parser.add_argument("query", help="User request to send to backend.")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/chat/stream",
        help="Backend stream endpoint.",
    )
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--reranker-model-id", default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--top-n", type=int, default=None)
    parser.add_argument("--vector-store-id", default=None)
    return parser


def main() -> int:
    """Run CLI client and print filtered stream output to stdout."""
    args = _build_arg_parser().parse_args()

    payload: dict[str, object] = {"user_request": args.query, "history": []}
    if args.model_id:
        payload["model_id"] = args.model_id
    if args.reranker_model_id:
        payload["reranker_model_id"] = args.reranker_model_id
    if args.top_k is not None:
        payload["top_k"] = args.top_k
    if args.top_n is not None:
        payload["top_n"] = args.top_n
    if args.vector_store_id:
        payload["vector_store_id"] = args.vector_store_id

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

    answer_streaming = False

    def _pretty_node_event(node_name: object, status: str) -> str:
        label = str(node_name or "UnknownNode")
        return f"[{status.upper():9}] {label}"

    try:
        with urllib.request.urlopen(request) as response:
            for event_type, data_text in _iter_sse_events(response):
                try:
                    event = json.loads(data_text)
                except json.JSONDecodeError:
                    continue

                payload_type = str(event.get("type", event_type))
                node = event.get("node")
                data = (
                    event.get("data", {}) if isinstance(event.get("data"), dict) else {}
                )

                if payload_type == "graph.node.started" and node != "AnswerGenerator":
                    print(_pretty_node_event(node, "started"))
                    continue

                if payload_type == "graph.node.completed" and node != "AnswerGenerator":
                    print(_pretty_node_event(node, "completed"))
                    continue

                if (
                    payload_type == "response.output_text.delta"
                    and node == "AnswerGenerator"
                ):
                    delta = str(data.get("delta", ""))
                    if delta:
                        if not answer_streaming:
                            print()
                        answer_streaming = True
                        print(delta, end="", flush=True)
                    continue

                if (
                    payload_type == "response.output_text.completed"
                    and node == "AnswerGenerator"
                    and answer_streaming
                ):
                    print()

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
