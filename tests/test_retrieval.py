"""Tests for retrieval helpers in common package."""

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
    assert refs == [{"n": 1, "filename": "doc.pdf", "pages": None}]
