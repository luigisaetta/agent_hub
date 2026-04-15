"""
Author: L. Saetta
Last modified: 2026-04-15
License: MIT

Description:
    Utility script that checks which models are reachable/working with the
    current OCI OpenAI-compatible runtime configuration.
"""

from __future__ import annotations

from openai import OpenAIError

from common import get_inference_client, print_example_summary, print_runtime_config
from config import REGION

TEMPERATURE = 0.0
TEST_REQUEST = "Reply with only: ok"
REQUEST_TIMEOUT_SECONDS = 20
GREEN_CHECK = "\033[92m✓\033[0m"
RED_X = "\033[91m✗\033[0m"

# Keep this list simple and local to the script so it is easy to reuse/update.
MODEL_CANDIDATES = (
    "openai.gpt-5.2",
    "openai.gpt-5.4",
    "openai.gpt-oss-120b",
     "openai.gpt-oss-20b",
    "xai.grok-4-fast-non-reasoning",
    "xai.grok-4-fast-reasoning",
    "xai.grok-4-1-fast-non-reasoning",
    "xai.grok-4.20-0309-non-reasoning",
    "google.gemini-2.5-pro",
    "google.gemini-2.5-flash",
    "cohere.command-a-03-2025",
    "meta.llama-4-maverick-17b-128e-instruct-fp8",
    "meta.llama-4-scout-17b-16e-instruct",
    "ocid1.generativeaiendpoint.oc1.us-chicago-1.amaaaaaa2xxap7ya4bvxqruf3d6f7g543zlfsogmk2axjeeva27otzilnnla"
)


def _check_model(*, client, model_id: str) -> tuple[bool, str]:
    """Return (is_ok, detail) after a minimal request with one model."""
    try:
        response = client.responses.create(
            model=model_id,
            temperature=TEMPERATURE,
            input=TEST_REQUEST,
            max_output_tokens=32,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        output_text = (response.output_text or "").strip()
        if output_text:
            return True, output_text
        return True, "<empty output>"
    except OpenAIError as exc:
        return False, str(exc)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return False, str(exc)


def _print_markdown_report(results: list[tuple[str, str, bool]]) -> None:
    """Print final markdown summary table."""
    print("")
    print("## Final Report")
    print("")
    print("| Model | Region | Status |")
    print("|---|---|---|")
    for model_id, region, is_ok in results:
        status = "✅" if is_ok else "❌"
        print(f"| `{model_id}` | `{region}` | {status} |")


def main() -> None:
    """Check all configured model candidates and print a compact report."""
    print_runtime_config()
    print("")
    print_example_summary("Model availability check utility.")
    print("")
    print(f"Test request: {TEST_REQUEST}")
    print("")

    client = get_inference_client()
    results: list[tuple[str, str, bool]] = []

    for model_id in MODEL_CANDIDATES:
        is_ok, detail = _check_model(client=client, model_id=model_id)
        results.append((model_id, REGION, is_ok))
        status = GREEN_CHECK if is_ok else RED_X
        detail_label = "response" if is_ok else "error"
        print(f"{status} {model_id}")
        print(f"   {detail_label}: {detail}")

    _print_markdown_report(results)


if __name__ == "__main__":
    main()
