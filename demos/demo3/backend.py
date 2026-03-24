"""
Author: L. Saetta
Last modified: 2026-03-24
License: MIT

Description:
    Backend logic for Demo3 PDF processing via Responses API.
"""

from __future__ import annotations

import logging
import json
from io import BytesIO

from openai import OpenAI

from config import BASE_URL
from config_private import KEY1, PROJECT_ID
from demos.demo3.llm_schema_models import ProceduraVendita

LOGGER = logging.getLogger("demo3.pdf_processing")

# configs
# hybrid setup:
# - Gemini for PDF-to-text extraction
# - GPT-5.2 for structured parsing
PDF_TEXT_MODEL_ID = "google.gemini-2.5-pro"
STRUCTURED_MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 12000

TRANSCRIPTION_PROMPT = (
    "Extract the full text from the attached PDF as faithfully as possible.\n"
    "Rules:\n"
    "- Preserve original order and wording.\n"
    "- Do not summarize, translate, or rewrite.\n"
    "- Keep headings and bullet points when present.\n"
    "- For unreadable parts, use [unclear].\n"
    "Return only the extracted text."
)

STRUCTURED_EXTRACTION_PROMPT = (
    "Extract structured data from the provided text of an Italian judicial sale notice.\n"
    "Rules:\n"
    "- Follow exactly the structure of the provided Pydantic output format.\n"
    "- Use only information present in the text.\n"
    "- Do not invent values.\n"
    "- If a field is missing, use null only when the schema allows it.\n"
    "- Keep canonical field names from the schema.\n"
    "- For amount-like fields that are typed as string, always return strings.\n"
    "- In each lot, extract one separate item for each distinct asset in oggetti_vendita.\n"
    "- Do not collapse multiple assets into one object.\n"
    "- If assets are listed in a single sentence separated by semicolons, split them into separate objects.\n"
    "- Return only structured data matching the schema."
)


def create_client() -> OpenAI:
    """Create OpenAI-compatible client for OCI Generative AI."""
    return OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )


def _extract_output_text(response) -> str:
    """Extract output text from a Responses API object with fallbacks."""
    output_text = (getattr(response, "output_text", "") or "").strip()
    if output_text:
        return output_text

    fragments: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", "") == "output_text":
                text = getattr(content, "text", "")
                if text:
                    fragments.append(text)

    return "\n".join(fragments).strip()


def _extract_usage(response) -> dict:
    """Extract token usage counters from a Responses API object."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _example_value_from_schema(node: dict, definitions: dict) -> object:
    """Build an example value from a JSON-schema node."""
    ref = node.get("$ref")
    if ref:
        def_name = ref.split("/")[-1]
        return _example_value_from_schema(definitions.get(def_name, {}), definitions)

    if "enum" in node and node["enum"]:
        for candidate in node["enum"]:
            if candidate not in (None, ""):
                return candidate
        return node["enum"][0]

    node_type = node.get("type")
    if isinstance(node_type, list):
        non_null = [item for item in node_type if item != "null"]
        node_type = non_null[0] if non_null else "null"

    if node_type == "object":
        props = node.get("properties", {})
        required = node.get("required", [])
        result = {}
        for key, prop_schema in props.items():
            if key in required:
                result[key] = _example_value_from_schema(prop_schema, definitions)
            else:
                result[key] = None
        return result

    if node_type == "array":
        items = node.get("items", {})
        return [_example_value_from_schema(items, definitions)]

    if node_type == "number":
        return 0.0
    if node_type == "integer":
        return 0
    if node_type == "boolean":
        return False
    if node_type == "null":
        return None
    return "example"


def _build_runtime_example_from_model() -> str:
    """Create a runtime JSON example from the Pydantic schema."""
    schema = ProceduraVendita.model_json_schema()
    definitions = schema.get("$defs", {})
    example_obj = _example_value_from_schema(schema, definitions)
    return json.dumps(example_obj, ensure_ascii=True, indent=2)


def extract_text_from_pdf_bytes(
    pdf_bytes: bytes, *, file_name: str
) -> tuple[str, dict]:
    """Upload PDF and extract text using Gemini 2.5 Pro via Responses API."""
    if not pdf_bytes:
        raise ValueError("Uploaded PDF is empty.")

    LOGGER.info("[STEP 1] Text extraction started | file=%s", file_name)
    client = create_client()
    file_stream = BytesIO(pdf_bytes)
    file_stream.name = file_name

    uploaded_file = client.files.create(
        file=file_stream,
        purpose="user_data",
        extra_headers={"OpenAI-Project": PROJECT_ID},
    )

    LOGGER.info(
        "[STEP 1] Uploaded PDF | file_id=%s | file=%s", uploaded_file.id, file_name
    )

    response = client.responses.create(
        model=PDF_TEXT_MODEL_ID,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": TRANSCRIPTION_PROMPT},
                    {"type": "input_file", "file_id": uploaded_file.id},
                ],
            }
        ],
    )

    extracted_text = _extract_output_text(response)
    snippet = extracted_text[:600].replace("\n", " ")
    LOGGER.info(
        "[STEP 1] Extracted text snippet | %s", snippet if snippet else "<empty>"
    )

    usage = _extract_usage(response)
    LOGGER.info(
        "[STEP 1] Text extraction completed | tokens in/out/total=%d/%d/%d",
        usage["input_tokens"],
        usage["output_tokens"],
        usage["total_tokens"],
    )
    return extracted_text, usage


def extract_structured_data_from_text(extracted_text: str) -> tuple[dict, dict]:
    """Parse extracted text into ProceduraVendita using responses.parse."""
    if not extracted_text.strip():
        raise ValueError("Extracted text is empty. Cannot run structured parsing.")

    LOGGER.info("[STEP 2] Structured JSON extraction started")
    client = create_client()
    runtime_example = _build_runtime_example_from_model()
    response = client.responses.parse(
        model=STRUCTURED_MODEL_ID,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        input=[
            {
                "role": "user",
                "content": (
                    f"{STRUCTURED_EXTRACTION_PROMPT}\n\n"
                    "Example JSON shape (generated at runtime from the Pydantic schema):\n"
                    f"{runtime_example}\n\n"
                    "Input text to parse:\n"
                    "----- BEGIN EXTRACTED TEXT -----\n"
                    f"{extracted_text}\n"
                    "----- END EXTRACTED TEXT -----"
                ),
            }
        ],
        store=False,
        text_format=ProceduraVendita,
    )

    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("Structured parsing returned no parsed object.")

    data = parsed.model_dump(mode="json")
    usage = _extract_usage(response)
    LOGGER.info(
        "[STEP 2] Structured JSON extraction completed | keys=%s | tokens in/out/total=%d/%d/%d",
        list(data.keys()),
        usage["input_tokens"],
        usage["output_tokens"],
        usage["total_tokens"],
    )
    return data, usage
