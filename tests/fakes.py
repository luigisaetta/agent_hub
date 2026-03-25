"""
Author: L. Saetta
Last modified: 2026-03-25
License: MIT

Description:
    Shared fake API helpers for pagination and delete flow tests.
"""

from __future__ import annotations

from types import SimpleNamespace


class FakePagedDeleteApi:
    """Fake API exposing list/delete methods with deterministic page sequencing."""

    def __init__(
        self,
        pages: list[SimpleNamespace],
        delete_arg_name: str,
        fail_ids: set[str] | None = None,
    ) -> None:
        """Initialize with pages and optional IDs that should fail on delete."""
        self._pages = pages
        self._idx = 0
        self._delete_arg_name = delete_arg_name
        self.fail_ids = fail_ids or set()
        self.deleted_ids: list[str] = []

    def list(self, **_kwargs):
        """Return next pre-canned page."""
        page = self._pages[self._idx]
        self._idx += 1
        return page

    def delete(self, **kwargs):
        """Delete by configured keyword argument and optionally simulate failures."""
        item_id = kwargs[self._delete_arg_name]
        if item_id in self.fail_ids:
            raise RuntimeError("simulated delete error")

        self.deleted_ids.append(item_id)
        return {"id": item_id, "deleted": True}
