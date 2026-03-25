"""Regression tests for vector store listing and deletion utility scripts."""

# pylint: disable=import-error

from __future__ import annotations

from types import SimpleNamespace

from tests.fakes import FakePagedDeleteApi


def test_format_expiration_handles_none_and_epoch(reload_module):
    """Expiration formatter should handle empty and epoch values."""
    module = reload_module("examples.list_all_vector_stores")

    assert module.format_expiration(None) == "N/A"
    assert module.format_expiration(0) == "N/A"
    assert module.format_expiration(1).startswith("1970-01-01")


def test_list_all_vector_stores_paginates_and_prints(
    monkeypatch, reload_module, capsys
):
    """List script should walk all vector store pages and print totals."""
    module = reload_module("examples.list_all_vector_stores")

    page1 = SimpleNamespace(
        data=[
            SimpleNamespace(id="vs1", name="docs", status="completed", expires_at=1),
            SimpleNamespace(
                id="vs2", name="notes", status="completed", expires_at=None
            ),
        ],
        has_more=True,
    )
    page2 = SimpleNamespace(
        data=[
            SimpleNamespace(id="vs3", name="reports", status="completed", expires_at=2)
        ],
        has_more=False,
    )
    fake_vs = FakePagedDeleteApi([page1, page2], delete_arg_name="vector_store_id")
    fake_client = SimpleNamespace(vector_stores=fake_vs)

    monkeypatch.setattr(module, "get_control_plane_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "=== Page 1" in out
    assert "=== Page 2" in out
    assert "Done. Total vector stores listed: 3" in out
    assert "expires_at=" in out


def test_delete_all_vs_continues_on_single_error(monkeypatch, reload_module, capsys):
    """Delete script should continue deleting even if one vector store fails."""
    module = reload_module("examples.delete_all_vs")

    page1 = SimpleNamespace(
        data=[
            SimpleNamespace(id="vs1", name="docs", status="completed", expires_at=None),
            SimpleNamespace(
                id="vs2", name="notes", status="completed", expires_at=None
            ),
        ],
        has_more=False,
    )
    fake_vs = FakePagedDeleteApi(
        [page1],
        delete_arg_name="vector_store_id",
        fail_ids={"vs2"},
    )
    fake_client = SimpleNamespace(vector_stores=fake_vs)

    monkeypatch.setattr(module, "get_control_plane_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "ERROR deleting: vs2" in out
    assert "Done. Deleted=1, Failed=1, Total=2" in out
    assert fake_vs.deleted_ids == ["vs1"]
