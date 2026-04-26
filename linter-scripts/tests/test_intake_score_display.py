"""Tests for scored-vs-unscored similarity-score labelling on the
rename/copy intake — both the human text table and the JSON
variant emitted under ``--json``.

Why this file (and not a few more cases tacked onto
``test_diff_rename_log_flag.py``): the score-display contract is a
stand-alone vocabulary (``n/a`` sentinel + ``score_status`` enum)
that needs to stay in sync between two renderers, a dataclass
serialiser, and operator-facing docs. Keeping its tests in one
file makes the contract greppable as a unit when the next person
touches it.

Invariants covered:

* Text renderer prints ``n/a`` (NOT the legacy ``---``) for
  unscored rows so ``score == 0`` and ``score is None`` are
  visually distinguishable. Alignment under the ``score`` header
  is preserved (both ``092`` and ``n/a`` are ≤3 chars and pad to
  the 5-wide column).
* Text renderer emits a vocabulary legend (``score = git
  similarity % (0–100); n/a = unscored input``) iff at least one
  unscored row is present, and unconditionally on a forced-empty
  table — gating on row content keeps the common all-scored case
  noise-free.
* ``_intake_row_to_json`` pairs ``"score": <int|null>`` with
  ``"score_status": "scored"|"unscored"`` so machine consumers can
  match on a labelled enum without convention-based ``null``
  interpretation. ``score`` for an unscored row is ``null``
  (not ``0``, not ``-1``) so it round-trips through
  ``Optional[int]`` typing in downstream code.
* ``_render_rename_intake_json`` writes a single
  ``{"rename_intake": {"row_count": ..., "rows": [...]}}`` JSON
  document to its stream so STDERR output stays line-parseable
  alongside STDOUT verdicts.
* End-to-end: ``--json --diff-rename-log`` emits the JSON intake
  on STDERR while STDOUT remains a single parseable verdict
  document. The text table must NOT appear on STDERR in this
  mode (otherwise both formats would race).
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LINTER = (Path(__file__).resolve().parent.parent
          / "check-placeholder-comments.py")


def _run(*args: str, cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run([sys.executable, str(LINTER), *args],
                       cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class TextRendererScoreLabelling(unittest.TestCase):
    def setUp(self) -> None:
        from conftest_shim import load_placeholder_linter
        self.chk = load_placeholder_linter()

    def test_unscored_row_renders_as_n_a_not_dashes(self) -> None:
        """Regression guard: the legacy ``---`` sentinel was
        ambiguous with "score was 0". The new sentinel is the
        explicit ``n/a`` so the two cases can't be conflated."""
        row = self.chk._DiffIntakeRow("R", None, "spec/a.md", "spec/b.md")
        buf = io.StringIO()
        self.chk._render_rename_intake_table([row], buf)
        out = buf.getvalue()
        self.assertIn("n/a", out)
        # Old sentinel must not reappear via copy-paste regression.
        # (Search the data row only — the surrounding banner has no
        # ``---``, so a substring check on the full output is fine.)
        self.assertNotIn("---", out)

    def test_scored_row_renders_as_zero_padded_percent(self) -> None:
        """Scored rows keep the fixed-width ``NNN`` form so the
        score column doesn't shift between 1-, 2-, and 3-digit
        scores."""
        rows = [
            self.chk._DiffIntakeRow("R", 7, "spec/a.md", "spec/x.md"),
            self.chk._DiffIntakeRow("R", 75, "spec/b.md", "spec/y.md"),
            self.chk._DiffIntakeRow("R", 100, "spec/c.md", "spec/z.md"),
        ]
        buf = io.StringIO()
        self.chk._render_rename_intake_table(rows, buf)
        out = buf.getvalue()
        self.assertIn("007", out)
        self.assertIn("075", out)
        self.assertIn("100", out)

    def test_score_zero_is_distinguishable_from_unscored(self) -> None:
        """The whole point of the labelling improvement: a row
        with ``score == 0`` and a row with ``score is None`` must
        render differently."""
        rows = [
            self.chk._DiffIntakeRow("R", 0, "spec/zero.md", "spec/x.md"),
            self.chk._DiffIntakeRow("R", None, "spec/none.md", "spec/y.md"),
        ]
        buf = io.StringIO()
        self.chk._render_rename_intake_table(rows, buf)
        out = buf.getvalue()
        self.assertIn("000", out)
        self.assertIn("n/a", out)

    def test_legend_appears_when_unscored_rows_present(self) -> None:
        rows = [
            self.chk._DiffIntakeRow("R", 92, "spec/a.md", "spec/x.md"),
            self.chk._DiffIntakeRow("R", None, "spec/b.md", "spec/y.md"),
        ]
        buf = io.StringIO()
        self.chk._render_rename_intake_table(rows, buf)
        out = buf.getvalue()
        self.assertIn("score = git similarity %", out)
        self.assertIn("n/a = unscored input", out)

    def test_legend_suppressed_when_all_rows_scored(self) -> None:
        """Common case: every row carries a score. The legend
        would be redundant noise — only print it when at least
        one row demonstrates the unscored sentinel."""
        rows = [
            self.chk._DiffIntakeRow("R", 92, "spec/a.md", "spec/x.md"),
            self.chk._DiffIntakeRow("C", 50, "spec/b.md", "spec/y.md"),
        ]
        buf = io.StringIO()
        self.chk._render_rename_intake_table(rows, buf)
        out = buf.getvalue()
        self.assertNotIn("git similarity", out)

    def test_legend_unconditional_on_empty_forced_table(self) -> None:
        """Forced-empty table: legend prints anyway so the
        score vocabulary is documented even with zero rows."""
        buf = io.StringIO()
        self.chk._render_rename_intake_table([], buf)
        out = buf.getvalue()
        self.assertIn("score = git similarity %", out)
        self.assertIn("n/a = unscored input", out)

    def test_alignment_preserved_with_n_a_sentinel(self) -> None:
        """Switching from ``---`` to ``n/a`` must not break the
        ``score`` column's alignment with the OLD column."""
        rows = [
            self.chk._DiffIntakeRow("R", 92, "spec/a.md", "spec/x.md"),
            self.chk._DiffIntakeRow("R", None, "spec/b.md", "spec/y.md"),
        ]
        buf = io.StringIO()
        self.chk._render_rename_intake_table(rows, buf)
        lines = buf.getvalue().splitlines()
        # Find data rows (start with two spaces + 'R') and check
        # their OLD-column starts at the same offset.
        data_lines = [ln for ln in lines if ln.startswith("  R   ")]
        self.assertEqual(len(data_lines), 2)
        a_idx = data_lines[0].index("spec/a.md")
        b_idx = data_lines[1].index("spec/b.md")
        self.assertEqual(a_idx, b_idx)


class JsonSerialisation(unittest.TestCase):
    def setUp(self) -> None:
        from conftest_shim import load_placeholder_linter
        self.chk = load_placeholder_linter()

    def test_scored_row_to_json_has_int_and_scored_label(self) -> None:
        row = self.chk._DiffIntakeRow("R", 92, "spec/a.md", "spec/b.md")
        d = self.chk._intake_row_to_json(row)
        self.assertEqual(d["score"], 92)
        self.assertEqual(d["score_status"], "scored")
        self.assertEqual(d["kind"], "R")
        self.assertEqual(d["old"], "spec/a.md")
        self.assertEqual(d["new"], "spec/b.md")

    def test_unscored_row_to_json_has_null_and_unscored_label(self) -> None:
        """Critical: ``score`` is ``null`` (not ``0``, not ``-1``)
        so downstream Optional[int] typing works, and the labelled
        enum carries the human-readable distinction."""
        row = self.chk._DiffIntakeRow("R", None, "spec/a.md", "spec/b.md")
        d = self.chk._intake_row_to_json(row)
        self.assertIsNone(d["score"])
        self.assertEqual(d["score_status"], "unscored")

    def test_score_zero_is_scored_not_unscored(self) -> None:
        """``0`` is a real similarity score (git can emit ``R0``
        for "completely different content but rename detected").
        Must NOT be conflated with unscored."""
        row = self.chk._DiffIntakeRow("R", 0, "spec/a.md", "spec/b.md")
        d = self.chk._intake_row_to_json(row)
        self.assertEqual(d["score"], 0)
        self.assertEqual(d["score_status"], "scored")

    def test_render_json_produces_single_parseable_document(self) -> None:
        rows = [
            self.chk._DiffIntakeRow("R", 92, "spec/a.md", "spec/x.md"),
            self.chk._DiffIntakeRow("C", None, "spec/b.md", "spec/y.md"),
        ]
        buf = io.StringIO()
        self.chk._render_rename_intake_json(rows, buf)
        # Must be exactly one JSON document followed by one newline.
        text = buf.getvalue()
        self.assertTrue(text.endswith("\n"))
        doc = json.loads(text)
        self.assertIn("rename_intake", doc)
        self.assertEqual(doc["rename_intake"]["row_count"], 2)
        self.assertEqual(len(doc["rename_intake"]["rows"]), 2)
        self.assertEqual(doc["rename_intake"]["rows"][0]["score_status"],
                         "scored")
        self.assertEqual(doc["rename_intake"]["rows"][1]["score_status"],
                         "unscored")
        self.assertIsNone(doc["rename_intake"]["rows"][1]["score"])

    def test_render_json_empty_table_still_valid(self) -> None:
        buf = io.StringIO()
        self.chk._render_rename_intake_json([], buf)
        doc = json.loads(buf.getvalue())
        self.assertEqual(doc["rename_intake"]["row_count"], 0)
        self.assertEqual(doc["rename_intake"]["rows"], [])


class EndToEndJsonMode(unittest.TestCase):
    """Verify ``--json --diff-rename-log`` keeps STDOUT a single
    parseable verdict document AND emits the labelled JSON intake
    on STDERR (text table must NOT appear in this mode)."""

    def test_json_mode_emits_labelled_intake_to_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec = root / "spec"
            spec.mkdir()
            (spec / "intro.md").write_text("# Intro\n\nClean content.\n")
            # Hand-crafted --changed-files payload exercising both
            # a scored R row and an unscored arrow row.
            cf = root / "changed.txt"
            cf.write_text(
                "R087\tspec/legacy.md\tspec/intro.md\n"
                "spec/old.md => spec/intro.md\n"
            )
            rc, out, err = _run(
                "--root", "spec",
                "--changed-files", str(cf),
                "--diff-rename-log",
                "--json",
                cwd=root,
            )
            # STDOUT is a single parseable JSON document (the
            # verdict — empty list when no violations).
            self.assertEqual(rc, 0, msg=f"stderr={err!r}")
            json.loads(out)
            # STDERR carries the JSON intake, NOT the text table.
            self.assertNotIn("rename/copy intake (", err,
                "text-table banner leaked into --json mode stderr")
            # Find the JSON intake line (other diagnostics may
            # share STDERR, so scan line by line).
            intake_doc = None
            for line in err.splitlines():
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    candidate = json.loads(line)
                except ValueError:
                    continue
                if "rename_intake" in candidate:
                    intake_doc = candidate
                    break
            self.assertIsNotNone(intake_doc,
                f"no rename_intake JSON on stderr; got: {err!r}")
            rows = intake_doc["rename_intake"]["rows"]
            self.assertEqual(intake_doc["rename_intake"]["row_count"], 2)
            statuses = sorted(r["score_status"] for r in rows)
            self.assertEqual(statuses, ["scored", "unscored"])
            # Scored row: score is the integer git emitted.
            scored = next(r for r in rows
                          if r["score_status"] == "scored")
            self.assertEqual(scored["score"], 87)
            # Unscored row: score is null (not 0, not omitted).
            unscored = next(r for r in rows
                            if r["score_status"] == "unscored")
            self.assertIsNone(unscored["score"])


if __name__ == "__main__":
    unittest.main()