"""Regression tests for file listing and deletion utility scripts."""

# pylint: disable=import-error

from __future__ import annotations

from types import SimpleNamespace

from tests.fakes import FakePagedDeleteApi


def test_list_all_files_paginates_and_prints_total(monkeypatch, reload_module, capsys):
    """List script should walk all pages and report final total."""
    module = reload_module("examples.list_all_files")

    page1 = SimpleNamespace(
        data=[
            SimpleNamespace(
                id="f1", filename="a.pdf", purpose="user_data", status="ok"
            ),
            SimpleNamespace(
                id="f2", filename="b.pdf", purpose="user_data", status="ok"
            ),
        ],
        has_more=True,
    )
    page2 = SimpleNamespace(
        data=[
            SimpleNamespace(id="f3", filename="c.pdf", purpose="user_data", status="ok")
        ],
        has_more=False,
    )
    fake_files = FakePagedDeleteApi([page1, page2], delete_arg_name="file_id")
    fake_client = SimpleNamespace(files=fake_files)

    monkeypatch.setattr(module, "get_inference_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "=== Page 1" in out
    assert "=== Page 2" in out
    assert "Done. Total files listed: 3" in out


def test_delete_all_files_continues_on_single_error(monkeypatch, reload_module, capsys):
    """Delete script should continue deleting even if one file delete fails."""
    module = reload_module("examples.delete_all_files")

    page1 = SimpleNamespace(
        data=[
            SimpleNamespace(
                id="f1", filename="a.pdf", purpose="user_data", status="ok"
            ),
            SimpleNamespace(
                id="f2", filename="b.pdf", purpose="user_data", status="ok"
            ),
        ],
        has_more=False,
    )
    fake_files = FakePagedDeleteApi([page1], delete_arg_name="file_id", fail_ids={"f2"})
    fake_client = SimpleNamespace(files=fake_files)

    monkeypatch.setattr(module, "get_inference_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "ERROR deleting: f2" in out
    assert "Done. Deleted=1, Failed=1, Total=2" in out
    assert fake_files.deleted_ids == ["f1"]
