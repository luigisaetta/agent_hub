"""
Shared output helpers.
"""

from __future__ import annotations


def print_streamed_output(stream) -> str:
    """
    Print streaming text deltas from a Responses API stream and return full text.
    """
    chunks = []
    for event in stream:
        if event.type == "response.output_text.delta":
            chunks.append(event.delta)
            print(event.delta, end="", flush=True)
    return "".join(chunks)


def print_header(header_type: str, where: str) -> None:
    """Print a standard section header."""
    print("=" * 44)
    print(f"List of the {header_type} in the {where}")
    print("=" * 44)
    print("")
