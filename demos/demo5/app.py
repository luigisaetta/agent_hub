"""
Author: L. Saetta
Last modified: 2026-04-08
License: MIT

Description:
    Demo 5 Streamlit UI to explore vector-store search chunks and metadata.
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure repository root is importable when Streamlit runs this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.demo5.backend import (  # noqa: E402
    DEFAULT_MAX_RESULTS,
    create_client,
    get_runtime_config,
    search_vector_store,
)

RESULTS_KEY = "demo5_results"
QUERY_KEY = "demo5_query"
MAX_RESULTS_KEY = "demo5_max_results"


def _init_session_state() -> None:
    """Initialize state keys used by the page."""
    if RESULTS_KEY not in st.session_state:
        st.session_state[RESULTS_KEY] = []
    if QUERY_KEY not in st.session_state:
        st.session_state[QUERY_KEY] = ""
    if MAX_RESULTS_KEY not in st.session_state:
        st.session_state[MAX_RESULTS_KEY] = DEFAULT_MAX_RESULTS


def _render_sidebar(config: dict[str, str]) -> int:
    """Render sidebar configuration and controls."""
    with st.sidebar:
        st.subheader("Runtime Configuration")
        st.caption(f"REGION: `{config['region']}`")
        st.caption(f"MODEL_ID: `{config['model_id']}`")
        st.caption(f"VECTOR_STORE_ID: `{config['vector_store_id'] or 'MISSING'}`")

        st.divider()
        st.subheader("Search Options")
        max_results = st.slider(
            "Max results",
            min_value=1,
            max_value=20,
            step=1,
            key=MAX_RESULTS_KEY,
        )

    return max_results


def _render_results(results: list[dict]) -> None:
    """Render retrieved chunks and related metadata in central view."""
    if not results:
        st.info("No chunks retrieved for this query.")
        return

    st.success(f"Retrieved chunks: {len(results)}")
    for item in results:
        title = f"#{item['rank']} | score={item['score']:.4f} | {item['filename']}"
        with st.expander(title, expanded=item["rank"] == 1):
            st.markdown("**Chunk text**")
            st.write(item["text"] or "<empty>")

            st.markdown("**Metadata**")
            st.json(
                {
                    "file_id": item["file_id"],
                    "filename": item["filename"],
                    "chunk_id": item["chunk_id"],
                    "pages": item["pages"],
                    "score": item["score"],
                    "additional_properties": item["metadata"],
                }
            )


def main() -> None:
    """Render Demo 5 and execute vector-store search requests."""
    st.set_page_config(page_title="Demo5 - Vector Store Explorer")
    st.title("Demo5: Vector Store Chunk Explorer")
    st.write(
        "Run semantic search on the configured vector store and inspect retrieved "
        "chunk texts with metadata."
    )

    _init_session_state()
    runtime_config = get_runtime_config()
    max_results = _render_sidebar(runtime_config)

    if not runtime_config["vector_store_id"]:
        st.error("VECTOR_STORE_ID is empty for the active profile.")
        st.info("Set VECTOR_STORE_ID in the selected .env profile and retry.")
        return

    with st.form("search_form"):
        query = st.text_area(
            "Query",
            value=st.session_state[QUERY_KEY],
            placeholder="Example: What are the main impacts of AI on labor market?",
            height=100,
        )
        submitted = st.form_submit_button("Search")

    if submitted:
        cleaned_query = query.strip()
        st.session_state[QUERY_KEY] = cleaned_query
        if not cleaned_query:
            st.warning("Insert a non-empty query.")
            return

        client = create_client()
        with st.spinner("Searching vector store..."):
            try:
                st.session_state[RESULTS_KEY] = search_vector_store(
                    client,
                    query=cleaned_query,
                    max_num_results=max_results,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                st.session_state[RESULTS_KEY] = []
                st.error(f"Search failed: {exc}")
                return

    _render_results(st.session_state[RESULTS_KEY])


if __name__ == "__main__":
    main()
