"""
Author: L. Saetta
Last modified: 2026-04-08
License: MIT

Description:
    Regression tests for Demo 5 backend normalization helpers.
"""

# pylint: disable=import-error

from __future__ import annotations

from types import SimpleNamespace


def test_extract_chunk_text_reads_content_blocks(reload_module):
    """Should extract text from content list blocks."""
    module = reload_module("demos.demo5.backend")

    item = SimpleNamespace(
        content=[
            {"type": "text", "text": "first"},
            {"type": "text", "text": "second"},
        ]
    )

    assert module.extract_chunk_text(item) == "first\nsecond"


def test_extract_chunk_text_falls_back_to_text_field(reload_module):
    """Should fallback to item.text when content blocks are missing."""
    module = reload_module("demos.demo5.backend")

    item = SimpleNamespace(content=None, text="standalone chunk")

    assert module.extract_chunk_text(item) == "standalone chunk"


def test_normalize_search_item_collects_metadata(reload_module):
    """Should normalize score, ids, pages and metadata from one item."""
    module = reload_module("demos.demo5.backend")

    item = SimpleNamespace(
        score=0.91,
        filename="doc1.pdf",
        file_id="file_123",
        content=[{"type": "text", "text": "chunk body"}],
        additional_properties={
            "chunk_id": "ch_001",
            "page_numbers": [4, 5],
            "section": "intro",
        },
    )

    normalized = module.normalize_search_item(item, rank=1)

    assert normalized["rank"] == 1
    assert normalized["score"] == 0.91
    assert normalized["filename"] == "doc1.pdf"
    assert normalized["file_id"] == "file_123"
    assert normalized["chunk_id"] == "ch_001"
    assert normalized["pages"] == [4, 5]
    assert normalized["text"] == "chunk body"
    assert normalized["metadata"]["section"] == "intro"


def test_search_vector_store_sorts_results_by_score(reload_module):
    """Search helper should call API and return score-descending ranking."""
    module = reload_module("demos.demo5.backend")

    captured = {"vector_store_id": None, "query": None, "max_num_results": None}

    def fake_search(*, vector_store_id, query, max_num_results, extra_headers):
        captured["vector_store_id"] = vector_store_id
        captured["query"] = query
        captured["max_num_results"] = max_num_results
        assert extra_headers == {"OpenAI-Project": module.PROJECT_ID}

        return SimpleNamespace(
            data=[
                SimpleNamespace(score=0.12, filename="b.pdf", content=[]),
                SimpleNamespace(score=0.88, filename="a.pdf", content=[]),
            ]
        )

    fake_client = SimpleNamespace(vector_stores=SimpleNamespace(search=fake_search))

    results = module.search_vector_store(
        fake_client,
        query="oracle ai",
        max_num_results=7,
    )

    assert captured["vector_store_id"] == module.VECTOR_STORE_ID
    assert captured["query"] == "oracle ai"
    assert captured["max_num_results"] == 7
    assert [item["filename"] for item in results] == ["a.pdf", "b.pdf"]
    assert [item["rank"] for item in results] == [1, 2]
