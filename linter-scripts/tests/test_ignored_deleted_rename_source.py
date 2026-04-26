"""Tests for the rename-source refinement of ``ignored-deleted``.

When a path is captured as a delete (either ``D\\tpath`` from
``git diff --name-status`` or from a ``--changed-files`` payload)
AND the same path also appears as the OLD side of a rename or
copy in the same intake, the audit row's ``reason`` must surface
the more accurate "rename-source" wording naming the NEW path —
not the misleading "file removed" text.

The fix is a pure audit-reason refinement: it does NOT change
which files get linted (the rename's NEW path is still linted as
a normal change, the OLD path is still recorded as
``ignored-deleted``). Only the human-readable ``reason`` cell
changes — and only for the cross-referenced rows.

Three layers of coverage:

1. **Unit-level** — :func:`_resolve_deleted_reason` directly,
   covering the rename-source hit, the legacy fall-through, the
   ``None`` similarities map, and the empty-``old_path`` edge case.
2. **End-to-end via --changed-files** — subprocess invocation
   with a manifest containing both ``D\\told`` and a separate
   ``R\\told\\tnew`` row, asserting the JSON audit reason names
   the new path.
3. **Regression guard** — a manifest with ONLY a delete (no
   matching rename) keeps the legacy reason byte-for-byte.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest_shim import load_placeholder_linter  # noqa: E402

_MOD = load_placeholder_linter()
_RenameSimilarity = _MOD._RenameSimilarity
_resolve = _MOD._resolve_deleted_reason
_DELETED_REASON = _MOD._DELETED_REASON
_DELETED_REASON_FALLBACK = _MOD._DELETED_REASON_FALLBACK

_LINTER = (Path(__file__).resolve().parent.parent
           / "check-placeholder-comments.py")


class TestResolveDeletedReason(unittest.TestCase):
    """Direct unit tests on the resolver helper."""

    def test_rename_source_match_names_new_path(self) -> None:
        sims = {
            "spec/new.md": _RenameSimilarity(
                kind="R", score=92, old_path="spec/old.md"),
        }
        reason = _resolve("spec/old.md", "diff-D", sims)
        # Must surface BOTH the explanation and the new path so the
        # audit reader can follow the trail without cross-referencing.
        self.assertIn("rename/copy", reason)
        self.assertIn("'spec/new.md'", reason)
        self.assertNotIn("file removed", reason)

    def test_rename_source_match_works_for_copy_kind_too(self) -> None:
        # ``C`` rows are renames-with-source-kept conceptually, but
        # if the user authored ``D\told`` alongside a ``C\told\tnew``
        # row the OLD path IS being recorded as deleted in this
        # intake — the rename-source wording still applies.
        sims = {
            "spec/copy.md": _RenameSimilarity(
                kind="C", score=80, old_path="spec/src.md"),
        }
        reason = _resolve("spec/src.md", "changed-files-D", sims)
        self.assertIn("'spec/copy.md'", reason)

    def test_unrelated_delete_falls_through_to_legacy_reason(self) -> None:
        # Path is NOT the OLD side of any rename → legacy per-
        # provenance reason wins. Byte-for-byte preserved.
        sims = {
            "spec/new.md": _RenameSimilarity(
                kind="R", score=92, old_path="spec/old.md"),
        }
        reason = _resolve("spec/genuinely-gone.md", "diff-D", sims)
        self.assertEqual(reason, _DELETED_REASON["diff-D"])

    def test_changed_files_d_falls_through_when_no_rename_match(self) -> None:
        reason = _resolve("spec/x.md", "changed-files-D",
                          {"y.md": _RenameSimilarity(
                              kind="R", score=80, old_path="z.md")})
        self.assertEqual(reason, _DELETED_REASON["changed-files-D"])

    def test_none_similarities_uses_legacy_reason(self) -> None:
        # ``None`` map (audit not requested) must not crash and
        # must reproduce the legacy text exactly.
        self.assertEqual(_resolve("x", "diff-D", None),
                         _DELETED_REASON["diff-D"])
        self.assertEqual(_resolve("x", "changed-files-D", None),
                         _DELETED_REASON["changed-files-D"])

    def test_empty_similarities_map_uses_legacy_reason(self) -> None:
        # Empty map must not match a blank-string old_path either.
        self.assertEqual(_resolve("x", "diff-D", {}),
                         _DELETED_REASON["diff-D"])

    def test_unknown_source_uses_fallback(self) -> None:
        # Future provenance tag → fallback reason, NOT a crash.
        self.assertEqual(
            _resolve("x", "future-source-tag", {}),
            _DELETED_REASON_FALLBACK,
        )

    def test_unknown_source_still_prefers_rename_match(self) -> None:
        # Even when the provenance tag is unrecognised, a
        # rename-source match must win over the fallback reason.
        sims = {
            "new.md": _RenameSimilarity(
                kind="R", score=92, old_path="old.md"),
        }
        reason = _resolve("old.md", "future-source-tag", sims)
        self.assertIn("'new.md'", reason)
        self.assertNotEqual(reason, _DELETED_REASON_FALLBACK)

    def test_empty_old_path_in_similarity_does_not_match_blank(self) -> None:
        # Pathological R/C rows with an empty ``old_path`` (legal
        # in hand-rolled inputs) must not accidentally match a
        # delete row whose path also happens to be the empty
        # string — would surface a confusing reason.
        sims = {
            "new.md": _RenameSimilarity(
                kind="R", score=None, old_path=""),
        }
        # A delete with a non-empty path: no match, legacy reason.
        self.assertEqual(_resolve("real.md", "diff-D", sims),
                         _DELETED_REASON["diff-D"])
        # A delete with an empty path (theoretically impossible but
        # let's pin the contract): also no match — empty old_path
        # is an explicit "we don't know the old side" sentinel.
        self.assertEqual(_resolve("", "diff-D", sims),
                         _DELETED_REASON["diff-D"])

    def test_first_matching_rename_wins_when_multiple_share_old_path(self) -> None:
        # Pathological but legal: two R/C rows claim the same old
        # path (a copy + a rename, say). We pick the first match.
        # The exact "first" is dict-iteration order, which is
        # insertion order in CPython 3.7+. Either name is correct;
        # the contract is just "we name SOME real new path", never
        # crash, never mention the deleted path itself.
        sims = {
            "first.md": _RenameSimilarity(
                kind="R", score=92, old_path="src.md"),
            "second.md": _RenameSimilarity(
                kind="C", score=50, old_path="src.md"),
        }
        reason = _resolve("src.md", "diff-D", sims)
        self.assertTrue(
            "'first.md'" in reason or "'second.md'" in reason,
            msg=f"reason must name one of the rename targets: {reason!r}",
        )
        self.assertNotIn("'src.md'", reason)


def _write_clean_md(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# Title\n\nNo placeholders.\n", encoding="utf-8")


def _run_changed_files(root: Path, manifest_text: str,
                       *extra: str) -> tuple[int, str, str]:
    manifest = root / "changed.txt"
    manifest.write_text(manifest_text, encoding="utf-8")
    cp = subprocess.run(
        [
            sys.executable, str(_LINTER),
            "--root", "spec",
            "--repo-root", str(root),
            "--changed-files", str(manifest),
            "--list-changed-files",
            "--with-similarity",
            "--json",
            *extra,
        ],
        cwd=root, capture_output=True, text=True,
    )
    return cp.returncode, cp.stdout, cp.stderr


class TestEndToEndChangedFiles(unittest.TestCase):
    """Drive the linter via subprocess to confirm the wiring."""

    def test_d_plus_rename_surfaces_rename_source_reason(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_clean_md(root / "spec" / "new.md")
            rc, _out, err = _run_changed_files(
                root,
                "D\tspec/old.md\n"
                "R\tspec/old.md\tspec/new.md\n",
            )
            self.assertEqual(rc, 0, msg=err)
            audit = json.loads(err)
            by_path = {r["path"]: r for r in audit}

            deleted_row = by_path.get("spec/old.md")
            self.assertIsNotNone(deleted_row,
                                 msg=f"expected old.md row in {audit}")
            self.assertEqual(deleted_row["status"], "ignored-deleted")
            self.assertIn("rename/copy", deleted_row["reason"])
            self.assertIn("'spec/new.md'", deleted_row["reason"])
            self.assertNotIn("file removed", deleted_row["reason"])
            # Sanity: the NEW path is still linted as matched.
            new_row = by_path.get("spec/new.md")
            self.assertEqual(new_row["status"], "matched")

    def test_d_plus_arrow_form_rename_also_matches(self) -> None:
        # Arrow form (``OLD => NEW``) records a rename with
        # ``score=None`` but a populated old_path — the resolver
        # must still cross-reference it.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_clean_md(root / "spec" / "new.md")
            rc, _out, err = _run_changed_files(
                root,
                "D\tspec/old.md\n"
                "spec/old.md => spec/new.md\n",
            )
            self.assertEqual(rc, 0, msg=err)
            audit = json.loads(err)
            old_row = next(r for r in audit
                           if r["path"] == "spec/old.md")
            self.assertEqual(old_row["status"], "ignored-deleted")
            self.assertIn("'spec/new.md'", old_row["reason"])

    def test_d_plus_scored_rename_with_score_zero_still_matches(self) -> None:
        # ``R000\told\tnew`` is observed-but-dissimilar — the OLD
        # path is still the rename source, the score is irrelevant
        # to the cross-reference.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_clean_md(root / "spec" / "new.md")
            rc, _out, err = _run_changed_files(
                root,
                "D\tspec/old.md\n"
                "R000\tspec/old.md\tspec/new.md\n",
            )
            self.assertEqual(rc, 0, msg=err)
            audit = json.loads(err)
            old_row = next(r for r in audit
                           if r["path"] == "spec/old.md")
            self.assertIn("'spec/new.md'", old_row["reason"])

    def test_genuine_delete_keeps_legacy_reason(self) -> None:
        # Regression guard: when there's NO rename mentioning the
        # deleted path, the historical ``changed-files-D`` reason
        # text must be preserved byte-for-byte.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rc, _out, err = _run_changed_files(
                root,
                "D\tspec/genuinely-gone.md\n",
            )
            self.assertEqual(rc, 0, msg=err)
            audit = json.loads(err)
            row = next(r for r in audit
                       if r["path"] == "spec/genuinely-gone.md")
            self.assertEqual(row["status"], "ignored-deleted")
            self.assertEqual(row["reason"],
                             _DELETED_REASON["changed-files-D"])
            self.assertNotIn("rename/copy", row["reason"])

    def test_rename_without_separate_d_row_unaffected(self) -> None:
        # Bare rename (no preceding ``D\told`` row) must not
        # synthesise an ``ignored-deleted`` audit entry for the
        # OLD path — the resolver only refines reasons for paths
        # that were ALREADY captured as deletes.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_clean_md(root / "spec" / "new.md")
            rc, _out, err = _run_changed_files(
                root,
                "R\tspec/old.md\tspec/new.md\n",
            )
            self.assertEqual(rc, 0, msg=err)
            audit = json.loads(err)
            paths = {r["path"] for r in audit}
            self.assertIn("spec/new.md", paths)
            self.assertNotIn("spec/old.md", paths,
                             msg=("rename source must NOT be "
                                  "synthesised as an audit row "
                                  "without a preceding delete"))


if __name__ == "__main__":
    unittest.main()