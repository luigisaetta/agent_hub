"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Shared output and formatting helpers for examples.
"""

from __future__ import annotations

import os

from config import BASE_URL, CP_BASE_URL, MODEL_ID, REGION


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


def print_runtime_config() -> None:
    """Print the runtime configuration currently in use."""
    inference_auth_mode = os.getenv("INFERENCE_AUTH_MODE", "api_key").strip().lower()
    if not inference_auth_mode:
        inference_auth_mode = "api_key"

    print("=" * COLS)
    print("Runtime Configuration")
    print("=" * COLS)
    print(f"REGION:     {REGION}")
    print(f"MODEL_ID:   {MODEL_ID}")
    print(f"INFERENCE_AUTH_MODE: {inference_auth_mode}")
    print(f"BASE_URL:   {BASE_URL}")
    print(f"CP_BASE_URL: {CP_BASE_URL}")


def print_example_summary(summary: str) -> None:
    """Print a short summary of what the current example does."""
    print("=" * COLS)
    print(f"Example: {summary}")
    print("=" * COLS)
