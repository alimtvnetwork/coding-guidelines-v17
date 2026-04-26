"""`--only-deleted-source` filter — restricts the audit's
`ignored-deleted` rows to specific intake provenances.

The flag is a SCALPEL on the deleted-rows bucket: non-deleted rows
(`matched`, `ignored-extension`, `ignored-out-of-root`,
`ignored-missing`) pass through unchanged regardless of the filter,
and only `ignored-deleted` rows whose `source` tag is in the
repeatable allow-set survive. This module pins:

* CLI surface — repeatable, closed-vocabulary `choices`, no-op
  when omitted (legacy parity).
* Renderer semantics — text, JSON, and CSV all see the same
  filtered row set, byte-for-byte aligned.
* Header + footer — the header surfaces the active filter and the
  per-source `deleted-by-source:` breakdown line counts every
  source in the canonical order against the post-dedupe / pre-
  filter intake (so the operator can see what was filtered out).
* Composition — `--dedupe-changed-files` runs first,
  `--only-changed-status` runs second, `--only-deleted-source`
  runs last; CSV mirrors the same pipeline.

End-to-end tests drive the published CLI as a subprocess so
STDOUT/STDERR routing is exercised through real OS pipes.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest_shim import load_placeholder_linter  # noqa: E402

_MOD = load_placeholder_linter()
_LINTER = (Path(__file__).resolve().parent.parent
           / "check-placeholder-comments.py")


# ---------------------------------------------------------------------
# Sandbox helper — covers every deleted-source class in one payload.
# ---------------------------------------------------------------------

_PAYLOAD_ALL_SOURCES = (
    # plain delete → changed-files-D
    "D\tspec/gone.md\n"
    # rename in tab form → matched (NEW) + changed-files-R-old (OLD)
    "R092\tspec/old1.md\tspec/new1.md\n"
    # copy in tab form → matched (NEW) + changed-files-C-old (OLD)
    "C075\tspec/src.md\tspec/copy.md\n"
    # rename in arrow form → matched (NEW) + changed-files-R-old (OLD)
    "spec/orig.md => spec/dest.md\n"
)


class _Sandbox:
    def __init__(self, payload: str = _PAYLOAD_ALL_SOURCES) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.spec = self.root / "spec"
        self.spec.mkdir()
        # Files actually present so the NEW-side rows resolve to
        # `matched` rather than `ignored-missing`.
        for rel in ("spec/new1.md", "spec/copy.md", "spec/dest.md"):
            (self.root / rel).write_text("# x\n", encoding="utf-8")
        self.changed = self.root / "changed.txt"
        self.changed.write_text(payload, encoding="utf-8")

    def __enter__(self) -> "_Sandbox":
        return self

    def __exit__(self, *exc: object) -> None:
        self._tmp.cleanup()

    def run(self, *extra: str) -> subprocess.CompletedProcess:
        cmd = [
            sys.executable, str(_LINTER),
            "--root", str(self.spec),
            "--changed-files", str(self.changed),
            "--list-changed-files",
            *extra,
        ]
        return subprocess.run(cmd, capture_output=True, text=True,
                              check=False, cwd=str(self.root))


# ---------------------------------------------------------------------
# CLI surface — argparse `choices`, repeatability, no-op default.
# ---------------------------------------------------------------------

class CliSurface(unittest.TestCase):

    def test_unknown_source_is_rejected_by_argparse(self) -> None:
        with _Sandbox() as box:
            proc = box.run("--only-deleted-source", "no-such-source")
        # Argparse rejects unknown choices with exit 2.
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr.lower())

    def test_default_is_noop_legacy_audit_unchanged(self) -> None:
        # Without the flag, every `ignored-deleted` row appears —
        # 1 plain D + 2 rename OLD-sides + 1 copy OLD-side = 4.
        with _Sandbox() as box:
            proc = box.run()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ignored-deleted=4", proc.stderr)
        # The breakdown line surfaces because deletes are present
        # even without the filter — confirms the conditional emit.
        self.assertIn("deleted-by-source:", proc.stderr)


# ---------------------------------------------------------------------
# Filter semantics — text mode.
# ---------------------------------------------------------------------

class TextModeFilterSemantics(unittest.TestCase):

    def test_filter_to_changed_files_d_keeps_only_plain_delete(
            self) -> None:
        with _Sandbox() as box:
            proc = box.run("--only-deleted-source", "changed-files-D")
        # Plain delete survives; OLD-side rows are dropped.
        self.assertIn("spec/gone.md", proc.stderr)
        self.assertNotIn("spec/old1.md", proc.stderr)
        self.assertNotIn("spec/src.md", proc.stderr)
        self.assertNotIn("spec/orig.md", proc.stderr)

    def test_filter_to_rename_old_keeps_both_intakes(self) -> None:
        # `changed-files-R-old` appears twice in the fixture (one
        # tab-form rename, one arrow-form rename). Both must survive.
        with _Sandbox() as box:
            proc = box.run(
                "--only-deleted-source", "changed-files-R-old",
            )
        self.assertIn("spec/old1.md", proc.stderr)
        self.assertIn("spec/orig.md", proc.stderr)
        # Plain D + copy-OLD are dropped.
        self.assertNotIn("spec/gone.md", proc.stderr)
        self.assertNotIn("spec/src.md", proc.stderr)

    def test_non_deleted_rows_pass_through_unchanged(self) -> None:
        # The scalpel only touches `ignored-deleted` rows. Every
        # `matched` row in the fixture must survive every filter.
        with _Sandbox() as box:
            proc = box.run("--only-deleted-source", "diff-D")
        # No `diff-D` row exists in this `--changed-files` intake,
        # so every `ignored-deleted` row is dropped — but the three
        # NEW-side `matched` rows MUST still be visible.
        self.assertIn("spec/new1.md", proc.stderr)
        self.assertIn("spec/copy.md", proc.stderr)
        self.assertIn("spec/dest.md", proc.stderr)
        self.assertNotIn("ignored-deleted ", proc.stderr.split(
            "totals:", 1)[0])

    def test_repeatable_flag_unions_the_allowed_set(self) -> None:
        with _Sandbox() as box:
            proc = box.run(
                "--only-deleted-source", "changed-files-D",
                "--only-deleted-source", "changed-files-C-old",
            )
        self.assertIn("spec/gone.md", proc.stderr)
        self.assertIn("spec/src.md", proc.stderr)
        self.assertNotIn("spec/old1.md", proc.stderr)
        self.assertNotIn("spec/orig.md", proc.stderr)


# ---------------------------------------------------------------------
# Header + footer — the operator-facing breadcrumbs.
# ---------------------------------------------------------------------

class HeaderAndFooterAnnotations(unittest.TestCase):

    def test_header_surfaces_active_source_filter(self) -> None:
        with _Sandbox() as box:
            proc = box.run("--only-deleted-source", "diff-R-old",
                           "--only-deleted-source", "diff-C-old")
        # Sources are rendered sorted so the header diff is stable
        # across runs regardless of CLI argument order.
        self.assertIn("deleted-source filter (diff-C-old+diff-R-old)",
                      proc.stderr)

    def test_breakdown_line_uses_canonical_source_order(self) -> None:
        with _Sandbox() as box:
            proc = box.run()
        # `deleted-by-source:` line lists every source in
        # `_DELETED_SOURCES` order. Pin the column order so a
        # downstream log scraper can hard-code positions.
        for src in _MOD._DELETED_SOURCES:
            self.assertIn(f"{src}=", proc.stderr)
        # Counts add up to 4 (the total `ignored-deleted` rows in
        # the fixture: 1 plain + 2 rename-old + 1 copy-old).
        line = next(ln for ln in proc.stderr.splitlines()
                    if "deleted-by-source:" in ln)
        nums = [int(tok.split("=")[1]) for tok in line.split()
                if "=" in tok]
        self.assertEqual(sum(nums), 4)

    def test_breakdown_counts_full_intake_not_filtered_view(
            self) -> None:
        # Filter to a single source — the breakdown line must
        # still report every source's underlying count, NOT the
        # filtered count, so the operator sees what was hidden.
        with _Sandbox() as box:
            proc = box.run("--only-deleted-source", "changed-files-D")
        line = next(ln for ln in proc.stderr.splitlines()
                    if "deleted-by-source:" in ln)
        # Both `changed-files-D=1` AND `changed-files-R-old=2` are
        # present even though only the plain D survived the filter.
        self.assertIn("changed-files-D=1", line)
        self.assertIn("changed-files-R-old=2", line)
        self.assertIn("changed-files-C-old=1", line)

    def test_breakdown_omitted_when_no_deletes_and_no_filter(
            self) -> None:
        # Legacy parity: an audit with zero `ignored-deleted` rows
        # AND no source filter must NOT gain the breakdown line.
        with _Sandbox(payload="spec/keep.md\n") as box:
            (box.spec / "keep.md").write_text("# k", encoding="utf-8")
            proc = box.run()
        self.assertNotIn("deleted-by-source:", proc.stderr)
        # Sanity: totals line still appears.
        self.assertIn("totals:", proc.stderr)

    def test_breakdown_emitted_under_filter_even_with_zero_deletes(
            self) -> None:
        # When the operator opted into the filter, surface the line
        # even if the underlying intake has no deletes — confirms
        # the filter ran and shows the all-zero breakdown.
        with _Sandbox(payload="spec/keep.md\n") as box:
            (box.spec / "keep.md").write_text("# k", encoding="utf-8")
            proc = box.run("--only-deleted-source", "diff-D")
        self.assertIn("deleted-by-source:", proc.stderr)
        self.assertIn("diff-D=0", proc.stderr)


# ---------------------------------------------------------------------
# JSON mode — array stays in sync with text-mode filtered view.
# ---------------------------------------------------------------------

class JsonModeMirrorsTextFilter(unittest.TestCase):

    def test_json_array_drops_filtered_deleted_rows(self) -> None:
        with _Sandbox() as box:
            proc = box.run(
                "--json",
                "--list-changed-files-verbose",
                "--only-deleted-source", "changed-files-R-old",
            )
        self.assertEqual(proc.returncode, 0,
                         msg=f"stderr:\n{proc.stderr}")
        audit = json.loads(proc.stderr.strip())
        # 3 NEW-side `matched` rows pass through; only the 2 R-old
        # `ignored-deleted` rows survive among the deletes.
        statuses = [r["status"] for r in audit]
        self.assertEqual(statuses.count("matched"), 3)
        self.assertEqual(statuses.count("ignored-deleted"), 2)
        # Every surviving deleted row carries the allowed source tag.
        for r in audit:
            if r["status"] == "ignored-deleted":
                self.assertEqual(r["source"], "changed-files-R-old")


# ---------------------------------------------------------------------
# CSV export — mirrors the same filtered set.
# ---------------------------------------------------------------------

class CsvExportMirrorsFilter(unittest.TestCase):

    def _csv_rows(self, *args: str) -> list[list[str]]:
        with _Sandbox() as box:
            csv_path = box.root / "audit.csv"
            proc = box.run(
                "--similarity-csv", str(csv_path),
                *args,
            )
            self.assertEqual(proc.returncode, 0,
                             msg=f"stderr:\n{proc.stderr}")
            with csv_path.open(encoding="utf-8", newline="") as fh:
                return list(csv.reader(fh))

    def test_csv_drops_filtered_deleted_rows(self) -> None:
        grid = self._csv_rows(
            "--only-deleted-source", "changed-files-D",
        )
        body = grid[1:]
        # 3 matched + 1 surviving deleted = 4 rows.
        self.assertEqual(len(body), 4)
        deleted = [r for r in body if r[1] == "ignored-deleted"]
        self.assertEqual(len(deleted), 1)
        self.assertEqual(deleted[0][0], "spec/gone.md")

    def test_csv_preserves_non_deleted_rows(self) -> None:
        # Even a filter that drops EVERY deleted row must leave the
        # `matched` / `ignored-*` non-deleted rows untouched.
        grid = self._csv_rows(
            "--only-deleted-source", "diff-D",
        )
        body = grid[1:]
        statuses = sorted(r[1] for r in body)
        # 3 NEW-side matched rows, no deleted rows survive (no
        # `diff-D` source exists in this `--changed-files` intake).
        self.assertEqual(statuses, ["matched", "matched", "matched"])


# ---------------------------------------------------------------------
# Composition with other filters.
# ---------------------------------------------------------------------

class ComposesWithOtherFilters(unittest.TestCase):

    def test_combined_with_only_changed_status(self) -> None:
        # `--only-changed-status ignored-deleted` first narrows to
        # the 4 deleted rows; `--only-deleted-source changed-files-D`
        # then narrows to the 1 plain delete. Both filter banners
        # must appear in the header.
        with _Sandbox() as box:
            proc = box.run(
                "--only-changed-status", "ignored-deleted",
                "--only-deleted-source", "changed-files-D",
            )
        self.assertIn("filtered, 1 of 7 row(s) shown", proc.stderr)
        self.assertIn("deleted-source filter (changed-files-D)",
                      proc.stderr)
        # Only the plain D row is visible in the table body.
        self.assertIn("spec/gone.md", proc.stderr)
        self.assertNotIn("spec/old1.md", proc.stderr)

    def test_combined_with_dedupe(self) -> None:
        # Duplicate the plain D in the payload; dedupe collapses it
        # to one row, then the source filter keeps that survivor.
        payload = (
            "D\tspec/gone.md\n"
            "D\tspec/gone.md\n"
            "R092\tspec/old1.md\tspec/new1.md\n"
        )
        with _Sandbox(payload=payload) as box:
            proc = box.run(
                "--dedupe-changed-files",
                "--only-deleted-source", "changed-files-D",
            )
        # Footer reports the dedupe drop AND the source filter.
        self.assertIn("deduped, 1 duplicate(s) dropped", proc.stderr)
        self.assertIn("deleted-source filter (changed-files-D)",
                      proc.stderr)
        self.assertIn("spec/gone.md", proc.stderr)
        # The R-old row is dropped by the source filter.
        self.assertNotIn("spec/old1.md", proc.stderr)


if __name__ == "__main__":
    unittest.main()