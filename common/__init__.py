"""Shared helpers package."""

from common.clients import (
    PROFILE,
    REGION,
    IS_PREPROD,
    build_oci_genai_client,
    get_client,
    get_oci_genai_service_endpoint,
)
from common.output import (
    print_example_summary,
    print_header,
    print_runtime_config,
    print_streamed_output,
)
from common.models import extract_provider_name
from common.retrieval import extract_text_and_refs

__all__ = [
    "PROFILE",
    "REGION",
    "IS_PREPROD",
    "build_oci_genai_client",
    "get_client",
    "get_oci_genai_service_endpoint",
    "print_example_summary",
    "print_header",
    "print_runtime_config",
    "print_streamed_output",
    "extract_provider_name",
    "extract_text_and_refs",
]
