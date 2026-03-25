"""
Shared retrieval-related helpers.
"""

from __future__ import annotations


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

    refs_by_key = {}
    ref_list = []
    counter = 1
    offset = 0  # Tracks text growth after inserting markers.

    for ann_pos, ann in enumerate(annotations):
        filename = getattr(ann, "filename", None) or "unknown_file"
        file_id = getattr(ann, "file_id", None)
        additional_properties = getattr(ann, "additional_properties", {}) or {}
        if not isinstance(additional_properties, dict):
            additional_properties = {}

        page_numbers = additional_properties.get("page_numbers") or []
        if not isinstance(page_numbers, list):
            page_numbers = [page_numbers]

        normalized_pages = tuple(sorted({p for p in page_numbers if p is not None}))

        # Reuse the same reference number for the same source + page set.
        source_key = file_id or filename
        if source_key == "unknown_file":
            # Avoid merging unrelated citations when both file_id and filename are missing.
            source_key = ("unknown_file", ann_pos, ann.index)
        ref_key = (source_key, normalized_pages)

        if ref_key not in refs_by_key:
            refs_by_key[ref_key] = counter
            ref_list.append(
                {
                    "n": counter,
                    "filename": filename,
                    "pages": list(normalized_pages),
                }
            )
            counter += 1

        ref_number = refs_by_key[ref_key]

        # Insert the inline marker at the annotation position.
        marker = f"[{ref_number}] "
        pos = ann.index + offset
        text = text[:pos] + marker + text[pos:]
        offset += len(marker)

    return text, ref_list
