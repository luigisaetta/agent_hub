"""
Shared retrieval-related helpers.
"""

from __future__ import annotations


def extract_text_and_refs(response):
    """
    Extract response text and inline file references from file-search annotations.
    """
    text_obj = response.output[1].content[0]

    text = text_obj.text
    annotations = sorted(text_obj.annotations, key=lambda ann: ann.index)

    refs_by_file_id = {}
    ref_list = []
    counter = 1
    offset = 0

    for ann in annotations:
        file_id = ann.file_id

        if file_id not in refs_by_file_id:
            refs_by_file_id[file_id] = counter
            ref_list.append(
                {
                    "n": counter,
                    "filename": ann.filename,
                    "pages": ann.additional_properties.get("page_numbers"),
                }
            )
            counter += 1

        marker = f"[{refs_by_file_id[file_id]}] "
        pos = ann.index + offset
        text = text[:pos] + marker + text[pos:]
        offset += len(marker)

    return text, ref_list
