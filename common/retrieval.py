"""
Shared retrieval-related helpers.
"""

from __future__ import annotations


def extract_text_and_refs(response):
    """
    Extract response text and inline file references from file-search annotations.
    """
    text_obj = None

    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "message":
            continue

        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", None) == "output_text":
                text_obj = content
                break

        if text_obj is not None:
            break

    if text_obj is None:
        return "", []

    text = getattr(text_obj, "text", "") or ""
    raw_annotations = getattr(text_obj, "annotations", []) or []
    annotations = sorted(
        [ann for ann in raw_annotations if hasattr(ann, "index")],
        key=lambda ann: ann.index,
    )

    refs_by_file_id = {}
    ref_list = []
    counter = 1
    offset = 0

    for ann in annotations:
        file_id = getattr(ann, "file_id", None)
        if not file_id:
            continue

        if file_id not in refs_by_file_id:
            refs_by_file_id[file_id] = counter
            additional_properties = getattr(ann, "additional_properties", {}) or {}
            if not isinstance(additional_properties, dict):
                additional_properties = {}

            ref_list.append(
                {
                    "n": counter,
                    "filename": getattr(ann, "filename", None),
                    "pages": additional_properties.get("page_numbers"),
                }
            )
            counter += 1

        marker = f"[{refs_by_file_id[file_id]}] "
        pos = ann.index + offset
        text = text[:pos] + marker + text[pos:]
        offset += len(marker)

    return text, ref_list
