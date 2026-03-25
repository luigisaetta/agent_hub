"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Shared helpers for model-id parsing and provider extraction.
"""

from __future__ import annotations

import re

_PROVIDER_PATTERN = re.compile(r"^[a-z]+$")


def extract_provider_name(model_id: str) -> str:
    """
    Extract provider name from a model id in the form ``provider.model``.
    """
    cleaned_model_id = model_id.strip()
    if not cleaned_model_id:
        msg = "MODEL_ID cannot be empty."
        raise ValueError(msg)

    provider, separator, model_name = cleaned_model_id.partition(".")
    if (
        not separator
        or not provider
        or not model_name
        or not _PROVIDER_PATTERN.fullmatch(provider)
    ):
        msg = (
            "Invalid MODEL_ID format. Expected 'provider.model', " f"got '{model_id}'."
        )
        raise ValueError(msg)

    return provider
