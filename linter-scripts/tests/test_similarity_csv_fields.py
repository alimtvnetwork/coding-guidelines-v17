"""Unit + CLI tests for ``--similarity-csv-fields``.

Covers the spec parser (:func:`_parse_similarity_csv_fields`), the
writer's projection behaviour (:func:`_write_similarity_csv` with a
``fields=`` argument), and the end-to-end CLI gate (typos must fail
with exit code 2 BEFORE the linter starts scanning).

The canonical column vocabulary is asserted byte-for-byte so a
future re-ordering of the contract trips immediately.
"""
from __future__ import annotations

import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest_shim import load_placeholder_linter  # noqa: E402

_MOD = load_placeholder_linter()

_ChangedFileAudit = _MOD._ChangedFileAudit
_RenameSimilarity = _MOD._RenameSimilarity
_write_similarity_csv = _MOD._write_similarity_csv
_parse = _MOD._parse_similarity_csv_fields
_FIELDS_ALL = _MOD._SIMILARITY_CSV_FIELDS_ALL

_LINTER = (Path(__file__).resolve().parent.parent
           / "check-placeholder-comments.py")


def _read_csv(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))


def _write_to_tmp(rows, **kwargs) -> list[list[str]]:
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "audit.csv"
        _write_similarity_csv(rows, str(out), **kwargs)
        return _read_csv(out.read_text(encoding="utf-8"))


class TestParseSpec(unittest.TestCase):

    def test_canonical_vocabulary_is_frozen(self) -> None:
        # Pin the contract: the seven recognised names + their order.
        # Re-ordering or extending this tuple is a breaking change
        # for any user CI script that hard-codes a field list.
        self.assertEqual(_FIELDS_ALL, (
            "path", "status", "reason",
            "kind", "score", "old_path", "score_kind",
        ))

    def test_simple_subset_preserves_order(self) -> None:
        self.assertEqual(_parse("path,status,score"),
                         ("path", "status", "score"))

    def test_user_supplied_order_wins_over_canonical_order(self) -> None:
        # The whole point of the flag is *projection* — if the user
        # asks for score-first, they get score-first regardless of
        # the canonical default order.
        self.assertEqual(_parse("score,kind,path,status"),
                         ("score", "kind", "path", "status"))

    def test_whitespace_around_tokens_is_stripped(self) -> None:
        self.assertEqual(_parse(" path , status,  score "),
                         ("path", "status", "score"))

    def test_trailing_and_leading_commas_are_tolerated(self) -> None:
        # Empty tokens drop silently — a trailing comma is a common
        # shell-history artefact and shouldn't be a failure.
        self.assertEqual(_parse(",path,status,"),
                         ("path", "status"))

    def test_score_kind_is_a_first_class_column(self) -> None:
        # Users can opt INTO score_kind from the CSV alone, without
        # also enabling --similarity-labels (which would touch the
        # text-table and JSON surfaces too).
        self.assertEqual(_parse("path,score_kind"),
                         ("path", "score_kind"))

    def test_empty_spec_raises(self) -> None:
        for spec in ("", " ", ",", " , , "):
            with self.subTest(spec=spec):
                with self.assertRaises(ValueError) as cm:
                    _parse(spec)
                self.assertIn("at least one column", str(cm.exception))

    def test_unknown_column_name_raises_with_allowed_list(self) -> None:
        with self.assertRaises(ValueError) as cm:
            _parse("path,old-path,status")  # hyphen instead of underscore
        msg = str(cm.exception)
        self.assertIn("old-path", msg)
        # The error must include the canonical vocabulary so the
        # operator can copy-paste the right name.
        self.assertIn("old_path", msg)
        self.assertIn("score_kind", msg)

    def test_duplicate_column_name_raises(self) -> None:
        with self.assertRaises(ValueError) as cm:
            _parse("path,status,path")
        self.assertIn("duplicate", str(cm.exception))
        self.assertIn("path", str(cm.exception))


class TestWriterProjection(unittest.TestCase):

    def _sample_rows(self) -> list:
        return [
            _ChangedFileAudit(
                path="readme.md", status="matched", reason="ok",
            ),
            _ChangedFileAudit(
                path="docs/new.md", status="matched", reason="ok",
                similarity=_RenameSimilarity(
                    kind="R", score=92, old_path="docs/old.md",
                ),
            ),
            _ChangedFileAudit(
                path="copy.md", status="matched", reason="ok",
                similarity=_RenameSimilarity(
                    kind="C", score=None, old_path="src.md",
                ),
            ),
        ]

    def test_default_call_unchanged_when_fields_is_none(self) -> None:
        # Regression guard: passing fields=None must produce the
        # exact 6-column header the legacy contract promises.
        grid = _write_to_tmp(self._sample_rows())
        self.assertEqual(grid[0], list(_MOD._SIMILARITY_CSV_HEADER))

    def test_fields_overrides_default_header(self) -> None:
        grid = _write_to_tmp(
            self._sample_rows(),
            fields=("path", "status", "score"),
        )
        self.assertEqual(grid[0], ["path", "status", "score"])
        # Body cells follow the requested column order.
        self.assertEqual(grid[1], ["readme.md", "matched", ""])
        self.assertEqual(grid[2], ["docs/new.md", "matched", "92"])
        # Unscored R/C row keeps its empty score cell — the
        # projection must not fabricate a value.
        self.assertEqual(grid[3], ["copy.md", "matched", ""])

    def test_fields_can_drop_old_path(self) -> None:
        # The poster-child use case from the README: share an audit
        # externally without leaking the OLD-side path layout.
        grid = _write_to_tmp(
            self._sample_rows(),
            fields=("path", "status", "reason", "kind", "score"),
        )
        self.assertEqual(grid[0],
                         ["path", "status", "reason", "kind", "score"])
        for row in grid[1:]:
            self.assertNotIn("docs/old.md", row)
            self.assertNotIn("src.md", row)

    def test_fields_can_request_score_kind_without_with_labels(self) -> None:
        # score_kind must populate from the row's similarity object
        # regardless of with_labels — the field-spec is the gate.
        grid = _write_to_tmp(
            self._sample_rows(),
            with_labels=False,
            fields=("path", "score_kind"),
        )
        self.assertEqual(grid[0], ["path", "score_kind"])
        self.assertEqual(grid[1], ["readme.md", ""])  # plain row
        self.assertEqual(grid[2], ["docs/new.md", "rename-similarity"])
        self.assertEqual(grid[3], ["copy.md", "unscored"])

    def test_fields_overrides_with_labels_append(self) -> None:
        # When fields is supplied, the with_labels-driven append is
        # NOT layered on top — the user gets exactly the columns
        # they asked for. This lets --similarity-labels stay on for
        # the text/JSON surfaces while the CSV view is trimmed.
        grid = _write_to_tmp(
            self._sample_rows(),
            with_labels=True,
            fields=("path", "score"),
        )
        self.assertEqual(grid[0], ["path", "score"])
        self.assertEqual(len(grid[1]), 2)

    def test_fields_can_re_order_columns(self) -> None:
        grid = _write_to_tmp(
            self._sample_rows(),
            fields=("score", "path"),
        )
        self.assertEqual(grid[0], ["score", "path"])
        self.assertEqual(grid[2], ["92", "docs/new.md"])


class TestCliGate(unittest.TestCase):
    """End-to-end: a bad spec must fail BEFORE the linter scans."""

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as d:
            return subprocess.run(
                [sys.executable, str(_LINTER), "--root", d, *args],
                capture_output=True, text=True,
            )

    def test_unknown_column_exits_2(self) -> None:
        cp = self._run("--similarity-csv-fields", "path,old-path")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("--similarity-csv-fields", cp.stderr)
        self.assertIn("old-path", cp.stderr)
        # STDOUT must stay empty per the failure-stream contract
        # documented in README-rename-intake.md.
        self.assertEqual(cp.stdout, "")

    def test_empty_spec_exits_2(self) -> None:
        cp = self._run("--similarity-csv-fields", "")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("at least one column", cp.stderr)
        self.assertEqual(cp.stdout, "")

    def test_duplicate_column_exits_2(self) -> None:
        cp = self._run("--similarity-csv-fields", "path,path")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("duplicate", cp.stderr)
        self.assertEqual(cp.stdout, "")

    def test_valid_spec_without_csv_flag_is_accepted(self) -> None:
        # The validator runs even when --similarity-csv itself isn't
        # set, but a *valid* spec must not block the run — it's a
        # no-op until the export flag is added.
        cp = self._run("--similarity-csv-fields", "path,status")
        # Exit 0 (clean run on an empty dir) — no spec error.
        self.assertEqual(cp.returncode, 0, msg=cp.stderr)


if __name__ == "__main__":
    unittest.main()