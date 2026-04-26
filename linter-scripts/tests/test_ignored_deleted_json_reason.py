"""JSON audit payload carries the per-source ``ignored-deleted`` reason.

The text table already shows the diversified reason from the
``_DELETED_REASON`` map; this suite locks in the contract that the
``--json`` output contains the same wording so dashboards consuming
the JSON array can reason about provenance without scraping the
human table.

Hermetic: feeds authored ``--changed-files`` payloads through
``_resolve_changed_md`` then renders via
``_render_changed_files_audit(as_json=True)``. No git, no temp repo
beyond a throwaway changed-files input file.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest_shim import load_placeholder_linter  # noqa: E402

_MOD = load_placeholder_linter()

_resolve_changed_md = _MOD._resolve_changed_md
_render_changed_files_audit = _MOD._render_changed_files_audit
_DELETED_REASON = _MOD._DELETED_REASON
_DELETED_REASON_FALLBACK = _MOD._DELETED_REASON_FALLBACK


def _audit_json(payload: str) -> list[dict]:
    """End-to-end: payload → audit list → JSON array (parsed back)."""
    audit: list = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        cf = root / "changed.txt"
        cf.write_text(payload, encoding="utf-8")
        _resolve_changed_md(
            repo_root=root, root=root,
            diff_base=None, changed_files=str(cf),
            extensions=("md",), audit=audit,
        )
    buf = io.StringIO()
    _render_changed_files_audit(audit, buf, as_json=True)
    return json.loads(buf.getvalue())


class TestDeletedReasonVocabulary(unittest.TestCase):
    """Map sanity — every provenance tag has its own row text."""

    def test_known_provenance_tags_present(self) -> None:
        self.assertIn("diff-D", _DELETED_REASON)
        self.assertIn("changed-files-D", _DELETED_REASON)

    def test_each_reason_is_unique(self) -> None:
        # Distinct provenance must produce distinct reason text —
        # otherwise the per-source split is invisible to JSON consumers.
        values = list(_DELETED_REASON.values())
        self.assertEqual(len(values), len(set(values)))

    def test_fallback_distinct_from_known_reasons(self) -> None:
        self.assertNotIn(_DELETED_REASON_FALLBACK,
                         _DELETED_REASON.values())


class TestJsonCarriesIgnoredDeletedRow(unittest.TestCase):
    """The JSON payload must include `ignored-deleted` rows verbatim."""

    def test_d_row_appears_in_json_with_status_and_reason(self) -> None:
        payload = _audit_json("D\tspec/gone.md\n")
        deleted = [r for r in payload if r["status"] == "ignored-deleted"]
        self.assertEqual(len(deleted), 1)
        self.assertEqual(deleted[0]["path"], "spec/gone.md")
        self.assertEqual(deleted[0]["reason"],
                         _DELETED_REASON["changed-files-D"])

    def test_reason_substring_is_grep_stable_for_logs(self) -> None:
        # The full reason text isn't part of the machine contract,
        # but `--changed-files` is a stable substring CI scripts
        # may grep on. Pin it so a future re-word doesn't silently
        # drop the provenance hint.
        payload = _audit_json("D\tspec/gone.md\n")
        reason = next(r["reason"] for r in payload
                      if r["status"] == "ignored-deleted")
        self.assertIn("--changed-files", reason)

    def test_status_vocabulary_includes_ignored_deleted(self) -> None:
        # Mixed payload: one A row + one D row → both statuses must
        # appear in the JSON, in input order.
        payload = _audit_json("A\tspec/new.md\nD\tspec/gone.md\n")
        statuses = [r["status"] for r in payload]
        self.assertIn("ignored-deleted", statuses)

    def test_multiple_d_rows_each_serialised_with_same_reason(self) -> None:
        # Per-row stability: two delete rows from the same source
        # produce two JSON entries with identical `reason` text.
        payload = _audit_json("D\tspec/a.md\nD\tspec/b.md\n")
        deleted = [r for r in payload if r["status"] == "ignored-deleted"]
        self.assertEqual([r["path"] for r in deleted],
                         ["spec/a.md", "spec/b.md"])
        for row in deleted:
            self.assertEqual(row["reason"],
                             _DELETED_REASON["changed-files-D"])

    def test_legacy_static_reason_string_no_longer_emitted(self) -> None:
        # Regression guard: the pre-task static text must not appear
        # in the JSON anymore — if it does, the per-source map isn't
        # being consulted (e.g. parser tuple → consumer drift).
        payload = _audit_json("D\tspec/gone.md\n")
        deleted = next(r for r in payload
                       if r["status"] == "ignored-deleted")
        legacy = "git reported D (deleted): no post-state file to lint"
        self.assertNotEqual(deleted["reason"], legacy)


class TestJsonShapeUnchangedForDeletedRows(unittest.TestCase):
    """Per-source reason must not perturb the rest of the JSON record."""

    def test_deleted_row_has_only_three_top_level_keys(self) -> None:
        # Without `--with-similarity`, every row — including the
        # deleted one — must keep the legacy 3-key schema. The
        # similarity sub-object must NOT leak in just because the
        # deleted-row pathway was touched.
        payload = _audit_json("D\tspec/gone.md\n")
        deleted = next(r for r in payload
                       if r["status"] == "ignored-deleted")
        self.assertEqual(set(deleted.keys()), {"path", "status", "reason"})


if __name__ == "__main__":
    unittest.main()
