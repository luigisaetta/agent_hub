"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Shared retrieval helpers for extracting text and citations from responses.
"""

from __future__ import annotations


def _get_mapping_value(obj, key):
    """Read a value from either a dict-like object or an SDK model."""
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _get_pages(source):
    """Return normalized page numbers from citation/result metadata."""
    metadata = (
        _get_mapping_value(source, "additional_properties")
        or _get_mapping_value(source, "attributes")
        or {}
    )
    if not isinstance(metadata, dict):
        metadata = {}

    page_numbers = metadata.get("page_numbers") or []
    if not isinstance(page_numbers, list):
        page_numbers = [page_numbers]

    return tuple(sorted({page for page in page_numbers if page is not None}))


def _make_ref_key(source, fallback_key):
    """Build a stable key for deduplicating retrieved sources."""
    filename = _get_mapping_value(source, "filename") or "unknown_file"
    file_id = _get_mapping_value(source, "file_id")
    pages = _get_pages(source)

    source_key = file_id or filename
    if source_key == "unknown_file":
        source_key = fallback_key

    return (source_key, pages), filename, pages


def _append_ref(refs_by_key, ref_list, source, fallback_key):
    """Append a source reference if it has not been listed already."""
    ref_key, filename, pages = _make_ref_key(source, fallback_key)
    if ref_key in refs_by_key:
        return refs_by_key[ref_key]

    ref_number = len(ref_list) + 1
    refs_by_key[ref_key] = ref_number
    ref_list.append(
        {
            "n": ref_number,
            "filename": filename,
            "pages": list(pages),
        }
    )
    return ref_number


def _extract_file_search_result_refs(response):
    """Extract deterministic references from file_search_call results."""
    refs_by_key = {}
    ref_list = []

    for item_pos, item in enumerate(getattr(response, "output", []) or []):
        if getattr(item, "type", None) != "file_search_call":
            continue
        for result_pos, result in enumerate(getattr(item, "results", []) or []):
            fallback_key = ("file_search_result", item_pos, result_pos)
            _append_ref(refs_by_key, ref_list, result, fallback_key)

    return ref_list


def _extract_annotation_refs(text, annotations):
    """Insert inline markers and extract references from citation annotations."""
    refs_by_key = {}
    ref_list = []
    offset = 0

    for ann_pos, ann in enumerate(annotations):
        fallback_key = ("unknown_file", ann_pos, ann.index)
        ref_number = _append_ref(refs_by_key, ref_list, ann, fallback_key)

        marker = f"[{ref_number}] "
        pos = ann.index + offset
        text = text[:pos] + marker + text[pos:]
        offset += len(marker)

    return text, ref_list


def extract_text_and_refs(response):
    """
    Extract assistant text and inline references from file-search annotations.

    Reference model:
    - inline citations in the text: [1], [2], ...
    - one reference entry per distinct evidence block
      (approximated as filename + page_numbers)
    """
    # Find the last assistant output_text block without assuming fixed positions.
    text_obj = None
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "message":
            continue
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", None) == "output_text":
                text_obj = content

    if text_obj is None:
        return "", []

    text = getattr(text_obj, "text", "") or ""
    base_text_len = len(text)

    # Keep only file-citation annotations with a valid insertion index.
    raw_annotations = getattr(text_obj, "annotations", []) or []
    filtered_annotations = []
    for ann in raw_annotations:
        ann_type = getattr(ann, "type", None)
        ann_index = getattr(ann, "index", None)

        is_supported_type = ann_type in (None, "file_citation")
        is_valid_index = isinstance(ann_index, int) and 0 <= ann_index <= base_text_len
        if is_supported_type and is_valid_index:
            filtered_annotations.append(ann)

    annotations = sorted(filtered_annotations, key=lambda ann: ann.index)

    text, ref_list = _extract_annotation_refs(text, annotations)

    if not ref_list:
        ref_list = _extract_file_search_result_refs(response)

    return text, ref_list
