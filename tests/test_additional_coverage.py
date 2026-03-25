"""Additional regression tests to improve branch coverage."""

# pylint: disable=import-error

from __future__ import annotations

from types import SimpleNamespace

from tests.fakes import FakePagedDeleteApi


def test_list_all_files_handles_empty_first_page(monkeypatch, reload_module, capsys):
    """List-all-files script should gracefully handle an empty first page."""
    module = reload_module("examples.list_all_files")

    empty_page = SimpleNamespace(data=[], has_more=False)
    fake_files = FakePagedDeleteApi([empty_page], delete_arg_name="file_id")
    fake_client = SimpleNamespace(files=fake_files)
    monkeypatch.setattr(module, "get_inference_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "Done. Total files listed: 0" in out


def test_delete_all_files_handles_empty_project(monkeypatch, reload_module, capsys):
    """Delete-all-files script should stop cleanly when there are no files."""
    module = reload_module("examples.delete_all_files")

    empty_page = SimpleNamespace(data=[], has_more=False)
    fake_files = FakePagedDeleteApi([empty_page], delete_arg_name="file_id")
    fake_client = SimpleNamespace(files=fake_files)
    monkeypatch.setattr(module, "get_inference_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "No files found." in out


def test_list_all_vector_stores_handles_empty_first_page(
    monkeypatch, reload_module, capsys
):
    """List-all-vector-stores script should report zero when no data exists."""
    module = reload_module("examples.list_all_vector_stores")

    empty_page = SimpleNamespace(data=[], has_more=False)
    fake_vs = FakePagedDeleteApi([empty_page], delete_arg_name="vector_store_id")
    fake_client = SimpleNamespace(vector_stores=fake_vs)
    monkeypatch.setattr(module, "get_control_plane_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "Done. Total vector stores listed: 0" in out


def test_delete_all_vs_handles_empty_compartment(monkeypatch, reload_module, capsys):
    """Delete-all-vector-stores script should return when nothing is found."""
    module = reload_module("examples.delete_all_vs")

    empty_page = SimpleNamespace(data=[], has_more=False)
    fake_vs = FakePagedDeleteApi([empty_page], delete_arg_name="vector_store_id")
    fake_client = SimpleNamespace(vector_stores=fake_vs)
    monkeypatch.setattr(module, "get_control_plane_client", lambda: fake_client)

    module.main()
    out = capsys.readouterr().out

    assert "No vector stores found." in out


def test_example15_uploads_with_expected_vector_store_and_closes_file(
    monkeypatch, reload_module
):
    """example15 should call upload_and_poll with correct vector store and close file."""
    module = reload_module("examples.example15")

    captured = {"vector_store_id": None, "file_obj": None}

    def upload_and_poll(*, vector_store_id, files):
        """Capture upload call details and return a fake batch object."""
        captured["vector_store_id"] = vector_store_id
        captured["file_obj"] = files[0]
        return SimpleNamespace(status="completed", file_counts={"completed": 1})

    fake_file_batches = SimpleNamespace(upload_and_poll=upload_and_poll)
    fake_vector_stores = SimpleNamespace(file_batches=fake_file_batches)
    fake_client = SimpleNamespace(vector_stores=fake_vector_stores)

    monkeypatch.setattr(module, "get_control_plane_client", lambda: fake_client)

    module.main()

    assert captured["vector_store_id"] == module.VECTOR_STORE_ID
    assert captured["file_obj"] is not None
    assert captured["file_obj"].closed
