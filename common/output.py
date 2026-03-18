"""
Shared output helpers.
"""

from __future__ import annotations

from config import BASE_URL, IS_PREPROD, REGION


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


COLS = 60


def print_header(header_type: str, where: str) -> None:
    """Print a standard section header."""
    print("=" * COLS)
    print(f"List of the {header_type} in the {where}")
    print("=" * COLS)
    print("")


def print_runtime_config() -> None:
    """Print the runtime configuration currently in use."""
    print("=" * COLS)
    print("Runtime Configuration")
    print("=" * COLS)
    print(f"IS_PREPROD: {IS_PREPROD}")
    print(f"REGION:     {REGION}")
    print(f"BASE_URL:   {BASE_URL}")


def print_example_summary(summary: str) -> None:
    """Print a short summary of what the current example does."""
    print("=" * COLS)
    print(f"Example: {summary}")
    print("=" * COLS)
