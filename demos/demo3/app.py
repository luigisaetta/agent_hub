"""
Author: L. Saetta
Last modified: 2026-03-24
License: MIT

Description:
    Demo 3 - Streamlit UI for single PDF upload, preview, and extraction.
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import base64
import json
import logging
import sys
from time import perf_counter
from pathlib import Path

import streamlit as st

# Ensure repository root is importable when Streamlit runs this file directly.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demos.demo3.backend import (
    PDF_TEXT_MODEL_ID,
    STRUCTURED_MODEL_ID,
    extract_structured_data_from_text,
    extract_text_from_pdf_bytes,
)

LOGGER = logging.getLogger("demo3.pdf_preview")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


def _validate_pdf_bytes(pdf_bytes: bytes) -> None:
    """Validate input bytes before rendering preview."""
    if not pdf_bytes:
        raise ValueError("Uploaded file is empty.")
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError(
            "Uploaded file does not look like a valid PDF (missing %PDF- header)."
        )


def _render_pdf_preview_html(pdf_bytes: bytes, *, height: int = 520) -> None:
    """Render PDF preview in pure HTML without external Python libraries."""
    _validate_pdf_bytes(pdf_bytes)
    base64_pdf = base64.b64encode(pdf_bytes).decode("ascii")
    html = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="500"
        height="{height}"
        type="application/pdf"
    ></iframe>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)


def main() -> None:
    """Render demo3 UI."""
    st.set_page_config(
        page_title="Demo3 - PDF Preview and Processing", page_icon="file"
    )
    st.title("Structured extraction from legal documents")

    with st.sidebar:
        st.subheader("PDF Input")
        uploaded_pdf = st.file_uploader("Upload a single PDF", type=["pdf"])

        if uploaded_pdf is not None:
            pdf_bytes = uploaded_pdf.getvalue()
            st.caption(f"File: `{uploaded_pdf.name}` ({len(pdf_bytes):,} bytes)")

            st.markdown("**Preview**")
            try:
                _render_pdf_preview_html(pdf_bytes)
            except Exception as error:  # pylint: disable=broad-exception-caught
                st.error(f"Preview failed: {error}")
                LOGGER.exception(
                    "PDF preview rendering failed for file=%s", uploaded_pdf.name
                )

            process_clicked = st.button("Process PDF", type="primary")
        else:
            pdf_bytes = b""
            process_clicked = False

    if not uploaded_pdf:
        st.info("Please upload a PDF from the sidebar to start.")
        return

    if not process_clicked:
        st.warning("Preview ready. Click **Process PDF** in the sidebar to continue.")
        return

    with st.spinner(f"Extracting full text from PDF with {PDF_TEXT_MODEL_ID}..."):
        text_start = perf_counter()
        try:
            LOGGER.info(
                "[STEP 1] UI started text extraction | file=%s", uploaded_pdf.name
            )
            extracted_text, text_usage = extract_text_from_pdf_bytes(
                pdf_bytes,
                file_name=uploaded_pdf.name,
            )
        except Exception as error:  # pylint: disable=broad-exception-caught
            LOGGER.exception("PDF processing failed for file=%s", uploaded_pdf.name)
            st.error(f"Processing failed: {error}")
            return
        text_elapsed = perf_counter() - text_start
        LOGGER.info(
            "[STEP 1] UI completed text extraction | elapsed=%.2fs", text_elapsed
        )

    with st.spinner(
        f"Parsing extracted text into structured JSON with {STRUCTURED_MODEL_ID}..."
    ):
        struct_start = perf_counter()
        try:
            LOGGER.info("[STEP 2] UI started structured extraction")
            structured_data, struct_usage = extract_structured_data_from_text(
                extracted_text
            )
        except Exception as error:  # pylint: disable=broad-exception-caught
            LOGGER.exception("Structured parsing failed for file=%s", uploaded_pdf.name)
            st.error(f"Structured parsing failed: {error}")
            return
        struct_elapsed = perf_counter() - struct_start
        LOGGER.info(
            "[STEP 2] UI completed structured extraction | elapsed=%.2fs",
            struct_elapsed,
        )

    total_elapsed = text_elapsed + struct_elapsed
    total_input_tokens = text_usage["input_tokens"] + struct_usage["input_tokens"]
    total_output_tokens = text_usage["output_tokens"] + struct_usage["output_tokens"]
    total_tokens = text_usage["total_tokens"] + struct_usage["total_tokens"]

    st.success("PDF processed, text extracted, and structured data generated.")

    st.subheader("Structured JSON")
    st.json(structured_data)

    st.download_button(
        label="Download JSON",
        data=json.dumps(structured_data, indent=2, ensure_ascii=True),
        file_name="demo3_extraction_result.json",
        mime="application/json",
    )

    st.markdown("### Processing Metrics")
    st.write(f"- Total processing time: {total_elapsed:.2f} s")
    st.write(f"- Time for PDF text extraction: {text_elapsed:.2f} s")
    st.write(f"- Time for structured extraction: {struct_elapsed:.2f} s")
    st.write(
        "- Total tokens (input/output/total): "
        f"{total_input_tokens} / {total_output_tokens} / {total_tokens}"
    )


if __name__ == "__main__":
    main()
