"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Tests for retrieval helpers in the common package.
"""

from __future__ import annotations

from types import SimpleNamespace


def _make_annotation(index, file_id, filename, pages):
    """Create a lightweight annotation object for tests."""
    return SimpleNamespace(
        index=index,
        file_id=file_id,
        filename=filename,
        additional_properties={"page_numbers": pages},
    )


def _make_response(text, annotations):
    """Create a minimal response object compatible with extract_text_and_refs."""
    text_obj = SimpleNamespace(type="output_text", text=text, annotations=annotations)
    output_item = SimpleNamespace(type="message", content=[text_obj])
    return SimpleNamespace(output=[SimpleNamespace(type="reasoning"), output_item])


def test_extract_text_and_refs_handles_empty_annotations(reload_module):
    """No annotations should preserve text and return no references."""
    retrieval = reload_module("common.retrieval")
    response = _make_response("Hello world", [])

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "Hello world"
    assert refs == []


def test_extract_text_and_refs_falls_back_to_file_search_results(reload_module):
    """File-search results should provide references when text has no annotations."""
    retrieval = reload_module("common.retrieval")
    text_obj = SimpleNamespace(type="output_text", text="answer", annotations=[])
    response = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="file_search_call",
                results=[
                    SimpleNamespace(
                        file_id="file-1",
                        filename="doc.pdf",
                        attributes={"page_numbers": [2, 1]},
                    ),
                    SimpleNamespace(
                        file_id="file-1",
                        filename="doc.pdf",
                        attributes={"page_numbers": [1, 2]},
                    ),
                    SimpleNamespace(
                        file_id="file-2",
                        filename="other.pdf",
                        attributes={},
                    ),
                ],
            ),
            SimpleNamespace(type="message", content=[text_obj]),
        ]
    )

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "answer"
    assert refs == [
        {"n": 1, "filename": "doc.pdf", "pages": [1, 2]},
        {"n": 2, "filename": "other.pdf", "pages": []},
    ]


def test_extract_text_and_refs_prefers_annotations_over_file_search_results(
    reload_module,
):
    """Inline citations should remain the source of refs when present."""
    retrieval = reload_module("common.retrieval")
    text_obj = SimpleNamespace(
        type="output_text",
        text="answer",
        annotations=[
            _make_annotation(
                index=0, file_id="file-1", filename="annotated.pdf", pages=[3]
            )
        ],
    )
    response = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="file_search_call",
                results=[
                    SimpleNamespace(
                        file_id="file-2",
                        filename="tool-result.pdf",
                        attributes={"page_numbers": [9]},
                    )
                ],
            ),
            SimpleNamespace(type="message", content=[text_obj]),
        ]
    )

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] answer"
    assert refs == [{"n": 1, "filename": "annotated.pdf", "pages": [3]}]


def test_extract_text_and_refs_reuses_ref_number_for_same_file(reload_module):
    """Multiple annotations from the same file should map to a single reference."""
    retrieval = reload_module("common.retrieval")
    annotations = [
        _make_annotation(index=0, file_id="file-1", filename="a.pdf", pages=[1]),
        _make_annotation(index=5, file_id="file-1", filename="a.pdf", pages=[1]),
    ]
    response = _make_response("abcdefghij", annotations)

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] abcde[1] fghij"
    assert refs == [{"n": 1, "filename": "a.pdf", "pages": [1]}]


def test_extract_text_and_refs_sorts_by_index_before_inserting_markers(reload_module):
    """Markers should be inserted based on sorted annotation index, not input order."""
    retrieval = reload_module("common.retrieval")
    annotations = [
        _make_annotation(index=6, file_id="file-b", filename="b.pdf", pages=[3]),
        _make_annotation(index=0, file_id="file-a", filename="a.pdf", pages=[1, 2]),
    ]
    response = _make_response("0123456789", annotations)

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] 012345[2] 6789"
    assert refs == [
        {"n": 1, "filename": "a.pdf", "pages": [1, 2]},
        {"n": 2, "filename": "b.pdf", "pages": [3]},
    ]


def test_extract_text_and_refs_finds_message_and_output_text_by_type(reload_module):
    """Should locate output_text in message item without relying on fixed indices."""
    retrieval = reload_module("common.retrieval")
    text_obj = SimpleNamespace(
        type="output_text",
        text="hello",
        annotations=[
            _make_annotation(index=0, file_id="f1", filename="doc.pdf", pages=[2])
        ],
    )
    response = SimpleNamespace(
        output=[
            SimpleNamespace(type="file_search_call", content=[]),
            SimpleNamespace(
                type="message",
                content=[SimpleNamespace(type="output_image"), text_obj],
            ),
        ]
    )

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] hello"
    assert refs == [{"n": 1, "filename": "doc.pdf", "pages": [2]}]


def test_extract_text_and_refs_handles_missing_optional_fields(reload_module):
    """Should tolerate missing annotations and additional_properties fields."""
    retrieval = reload_module("common.retrieval")
    response = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="message",
                content=[SimpleNamespace(type="output_text", text="No refs")],
            )
        ]
    )

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "No refs"
    assert refs == []


def test_extract_text_and_refs_handles_missing_additional_properties(reload_module):
    """Missing additional_properties should not break reference extraction."""
    retrieval = reload_module("common.retrieval")
    annotation = SimpleNamespace(index=0, file_id="f1", filename="doc.pdf")
    response = _make_response("hello", [annotation])

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] hello"
    assert refs == [{"n": 1, "filename": "doc.pdf", "pages": []}]


def test_extract_text_and_refs_uses_last_output_text(reload_module):
    """If multiple output_text blocks exist, the last one should be selected."""
    retrieval = reload_module("common.retrieval")
    response = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="message",
                content=[
                    SimpleNamespace(type="output_text", text="old", annotations=[])
                ],
            ),
            SimpleNamespace(
                type="message",
                content=[
                    SimpleNamespace(type="output_text", text="new", annotations=[])
                ],
            ),
        ]
    )

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "new"
    assert refs == []


def test_extract_text_and_refs_filters_non_file_citation_types(reload_module):
    """Only file_citation annotations should be considered when type is provided."""
    retrieval = reload_module("common.retrieval")
    annotations = [
        SimpleNamespace(
            type="url_citation",
            index=0,
            file_id="file-1",
            filename="a.pdf",
            additional_properties={"page_numbers": [1]},
        ),
        SimpleNamespace(
            type="file_citation",
            index=1,
            file_id="file-1",
            filename="a.pdf",
            additional_properties={"page_numbers": [1]},
        ),
    ]
    response = _make_response("abcd", annotations)

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "a[1] bcd"
    assert refs == [{"n": 1, "filename": "a.pdf", "pages": [1]}]


def test_extract_text_and_refs_separates_same_filename_by_file_id(reload_module):
    """Different file_id values should not collapse into the same reference."""
    retrieval = reload_module("common.retrieval")
    annotations = [
        _make_annotation(index=0, file_id="file-1", filename="shared.pdf", pages=[2]),
        _make_annotation(index=2, file_id="file-2", filename="shared.pdf", pages=[2]),
    ]
    response = _make_response("abcd", annotations)

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] ab[2] cd"
    assert refs == [
        {"n": 1, "filename": "shared.pdf", "pages": [2]},
        {"n": 2, "filename": "shared.pdf", "pages": [2]},
    ]


def test_extract_text_and_refs_ignores_invalid_indexes(reload_module):
    """Annotations with invalid indexes should be skipped."""
    retrieval = reload_module("common.retrieval")
    annotations = [
        _make_annotation(index=0, file_id="file-1", filename="a.pdf", pages=[1]),
        _make_annotation(index=999, file_id="file-2", filename="b.pdf", pages=[2]),
        SimpleNamespace(
            index="x",
            file_id="file-3",
            filename="c.pdf",
            additional_properties={"page_numbers": [3]},
        ),
    ]
    response = _make_response("abcd", annotations)

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] abcd"
    assert refs == [{"n": 1, "filename": "a.pdf", "pages": [1]}]


def test_extract_text_and_refs_does_not_merge_unknown_file_annotations(reload_module):
    """Unknown source annotations should not be merged under a single reference."""
    retrieval = reload_module("common.retrieval")
    annotations = [
        SimpleNamespace(index=0, additional_properties={"page_numbers": [1]}),
        SimpleNamespace(index=2, additional_properties={"page_numbers": [1]}),
    ]
    response = _make_response("abcd", annotations)

    text, refs = retrieval.extract_text_and_refs(response)

    assert text == "[1] ab[2] cd"
    assert refs == [
        {"n": 1, "filename": "unknown_file", "pages": [1]},
        {"n": 2, "filename": "unknown_file", "pages": [1]},
    ]
