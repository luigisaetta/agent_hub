from __future__ import annotations

from types import SimpleNamespace


class _FileItem:
    def __init__(self, file_id: str, filename: str, purpose: str = "user_data", status: str = "processed"):
        self.id = file_id
        self.filename = filename
        self.purpose = purpose
        self.status = status


class _FakeFilesApi:
    def __init__(self, pages: list[SimpleNamespace], fail_ids: set[str] | None = None):
        self._pages = pages
        self._idx = 0
        self.fail_ids = fail_ids or set()
        self.deleted_ids: list[str] = []

    def list(self, **kwargs):
        page = self._pages[self._idx]
        self._idx += 1
        return page

    def delete(self, file_id: str):
        if file_id in self.fail_ids:
            raise RuntimeError("simulated delete error")
        self.deleted_ids.append(file_id)
        return {"id": file_id, "deleted": True}


def test_list_all_files_paginates_and_prints_total(monkeypatch, reload_module, capsys):
    module = reload_module("examples.list_all_files")

    page1 = SimpleNamespace(
        data=[_FileItem("f1", "a.pdf"), _FileItem("f2", "b.pdf")],
        has_more=True,
    )
    page2 = SimpleNamespace(data=[_FileItem("f3", "c.pdf")], has_more=False)
    fake_files = _FakeFilesApi([page1, page2])
    fake_client = SimpleNamespace(files=fake_files)

    monkeypatch.setattr(module, "get_client", lambda **_: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "=== Page 1" in out
    assert "=== Page 2" in out
    assert "Done. Total files listed: 3" in out


def test_delete_all_files_continues_on_single_error(monkeypatch, reload_module, capsys):
    module = reload_module("examples.delete_all_files")

    page1 = SimpleNamespace(data=[_FileItem("f1", "a.pdf"), _FileItem("f2", "b.pdf")], has_more=False)
    fake_files = _FakeFilesApi([page1], fail_ids={"f2"})
    fake_client = SimpleNamespace(files=fake_files)

    monkeypatch.setattr(module, "get_client", lambda **_: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "ERROR deleting: f2" in out
    assert "Done. Deleted=1, Failed=1, Total=2" in out
    assert fake_files.deleted_ids == ["f1"]
