from __future__ import annotations

from types import SimpleNamespace


class _VectorStoreItem:
    def __init__(self, vs_id: str, name: str, status: str = "completed", expires_at: int | None = None):
        self.id = vs_id
        self.name = name
        self.status = status
        self.expires_at = expires_at


class _FakeVectorStoresApi:
    def __init__(self, pages: list[SimpleNamespace], fail_ids: set[str] | None = None):
        self._pages = pages
        self._idx = 0
        self.fail_ids = fail_ids or set()
        self.deleted_ids: list[str] = []

    def list(self, **kwargs):
        page = self._pages[self._idx]
        self._idx += 1
        return page

    def delete(self, vector_store_id: str):
        if vector_store_id in self.fail_ids:
            raise RuntimeError("simulated delete error")
        self.deleted_ids.append(vector_store_id)
        return {"id": vector_store_id, "deleted": True}


def test_format_expiration_handles_none_and_epoch(reload_module):
    module = reload_module("examples.list_all_vector_stores")

    assert module.format_expiration(None) == "N/A"
    assert module.format_expiration(0) == "N/A"
    assert module.format_expiration(1).startswith("1970-01-01")


def test_list_all_vector_stores_paginates_and_prints(monkeypatch, reload_module, capsys):
    module = reload_module("examples.list_all_vector_stores")

    page1 = SimpleNamespace(
        data=[
            _VectorStoreItem("vs1", "docs", expires_at=1),
            _VectorStoreItem("vs2", "notes", expires_at=None),
        ],
        has_more=True,
    )
    page2 = SimpleNamespace(data=[_VectorStoreItem("vs3", "reports", expires_at=2)], has_more=False)
    fake_vs = _FakeVectorStoresApi([page1, page2])
    fake_client = SimpleNamespace(vector_stores=fake_vs)

    monkeypatch.setattr(module, "get_client", lambda **_: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "=== Page 1" in out
    assert "=== Page 2" in out
    assert "Done. Total vector stores listed: 3" in out
    assert "expires_at=" in out


def test_delete_all_vs_continues_on_single_error(monkeypatch, reload_module, capsys):
    module = reload_module("examples.delete_all_vs")

    page1 = SimpleNamespace(
        data=[
            _VectorStoreItem("vs1", "docs"),
            _VectorStoreItem("vs2", "notes"),
        ],
        has_more=False,
    )
    fake_vs = _FakeVectorStoresApi([page1], fail_ids={"vs2"})
    fake_client = SimpleNamespace(vector_stores=fake_vs)

    monkeypatch.setattr(module, "get_client", lambda **_: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "ERROR deleting: vs2" in out
    assert "Done. Deleted=1, Failed=1, Total=2" in out
    assert fake_vs.deleted_ids == ["vs1"]
