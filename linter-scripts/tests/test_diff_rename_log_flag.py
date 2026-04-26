"""End-to-end + unit tests for the ``--diff-rename-log`` flag.

The flag controls a tri-state diagnostic that prints a rename/copy
intake table (one row per R/C entry from ``git diff --name-status``
or ``--changed-files``) to STDERR. Resolution table:

    flag value | render?
    -----------+--------------------------------------------
    None       | only if intake non-empty AND --json is OFF
    True       | always (force ON; useful for CI banners)
    False      | never (force OFF)

Critical invariants under test:

* **Always STDERR** — even when forced ON in --json mode, the table
  must NOT contaminate STDOUT (which CI parses as JSON).
* **Auto-quiet on JSON** — even when intake has rows, --json mode
  with the auto setting must stay silent (machine consumers haven't
  opted into the diagnostic).
* **Auto-quiet on empty** — no R/C rows ⇒ no header noise; the
  table only appears when there's actually something to audit.
* **Force-ON empty header** — explicit ``--diff-rename-log`` with
  no rows still emits the header + a hint, so a CI banner reads
  "we did look, found 0 renames" rather than appearing absent.
* **Force-OFF wins** — even with intake rows the table is
  suppressed, supporting PRs with hundreds of renames.
* **Both intake sources** — git's ``-M -C`` output AND user-
  supplied ``--changed-files`` rename rows produce identically-
  shaped intake (tested via the ``--changed-files`` path here;
  the git path shares the same parser logic).
* **Verdicts unaffected** — toggling the flag never changes which
  files are scanned or which violations fire.

The unit tests at the bottom exercise ``_render_rename_intake_table``
and ``_normalise_changed_lines`` directly via the shared shim, which
is cheaper than spinning up a subprocess for the formatting corner
cases.
"""

from __future__ import annotations

import io
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


def _make_repo_with_renames(td: Path) -> tuple[Path, Path]:
    """spec/ contains the POST-rename targets (so they exist on
    disk and survive the ``--changed-files`` allowlist filter).
    Returns (spec_root, changed_files_path)."""
    spec = td / "spec"
    spec.mkdir()
    (spec / "intro.md").write_text("# spec\nplain prose.\n")
    (spec / "feature.md").write_text("# spec\nplain prose.\n")
    changed = td / "changed.txt"
    changed.write_text(
        # Tab form, scored: standard ``git diff --name-status -M``.
        "R087\tspec/old-name.md\tspec/intro.md\n"
        # Arrow form, ``git status -s`` style — no score.
        "spec/legacy/intro.md => spec/feature.md\n"
    )
    return spec, changed


def _make_repo_no_renames(td: Path) -> tuple[Path, Path]:
    spec = td / "spec"
    spec.mkdir()
    (spec / "intro.md").write_text("# spec\nplain prose.\n")
    changed = td / "changed.txt"
    changed.write_text("spec/intro.md\n")
    return spec, changed


class DiffRenameLogAuto(unittest.TestCase):
    """The default (no flag) behaviour: auto-quiet on empty + JSON."""

    def test_auto_prints_table_when_rows_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            spec, changed = _make_repo_with_renames(Path(td))
            rc, out, err = _run(
                "--root", str(spec), "--repo-root", td,
                "--changed-files", str(changed),
                cwd=Path(td),
            )
            self.assertEqual(rc, 0)
            # Table on STDERR, never STDOUT.
            self.assertIn("rename/copy intake", err)
            self.assertIn("spec/intro.md", err)
            self.assertNotIn("rename/copy intake", out)

    def test_auto_silent_when_no_rc_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            spec, changed = _make_repo_no_renames(Path(td))
            rc, _, err = _run(
                "--root", str(spec), "--repo-root", td,
                "--changed-files", str(changed),
                cwd=Path(td),
            )
            self.assertEqual(rc, 0)
            self.assertNotIn("rename/copy intake", err)

    def test_auto_silent_in_json_even_with_rows(self) -> None:
        """Machine consumers haven't opted in — the auto branch
        must stay silent in --json mode regardless of intake."""
        with tempfile.TemporaryDirectory() as td:
            spec, changed = _make_repo_with_renames(Path(td))
            rc, out, err = _run(
                "--root", str(spec), "--repo-root", td, "--json",
                "--changed-files", str(changed),
                cwd=Path(td),
            )
            self.assertEqual(rc, 0)
            self.assertNotIn("rename/copy intake", err)
            # STDOUT must remain a single JSON document.
            import json as _json
            _json.loads(out)


class DiffRenameLogForceOn(unittest.TestCase):

    def test_force_on_prints_header_even_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            spec, changed = _make_repo_no_renames(Path(td))
            rc, _, err = _run(
                "--root", str(spec), "--repo-root", td,
                "--diff-rename-log",
                "--changed-files", str(changed),
                cwd=Path(td),
            )
            self.assertEqual(rc, 0)
            self.assertIn("0 row(s)", err)
            # Hint clarifies that the empty body isn't a bug.
            self.assertIn("no rename or copy rows", err)

    def test_force_on_in_json_keeps_stdout_clean(self) -> None:
        """The strongest invariant: even when the operator forces
        the table ON in --json mode, STDOUT must remain a single
        parseable JSON document. Table goes to STDERR only."""
        with tempfile.TemporaryDirectory() as td:
            spec, changed = _make_repo_with_renames(Path(td))
            rc, out, err = _run(
                "--root", str(spec), "--repo-root", td,
                "--json", "--diff-rename-log",
                "--changed-files", str(changed),
                cwd=Path(td),
            )
            self.assertEqual(rc, 0)
            self.assertIn("rename/copy intake", err)
            import json as _json
            _json.loads(out)


class DiffRenameLogForceOff(unittest.TestCase):

    def test_force_off_suppresses_table_even_with_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            spec, changed = _make_repo_with_renames(Path(td))
            rc, _, err = _run(
                "--root", str(spec), "--repo-root", td,
                "--no-diff-rename-log",
                "--changed-files", str(changed),
                cwd=Path(td),
            )
            self.assertEqual(rc, 0)
            self.assertNotIn("rename/copy intake", err)


class DiffRenameLogVerdictNeutrality(unittest.TestCase):
    """Toggling the flag must NOT change which violations fire."""

    def _violation_count(self, *flag: str) -> int:
        """Return the number of P-001 violation lines for the given
        flag set, on a fixture that's guaranteed to fire one."""
        with tempfile.TemporaryDirectory() as td:
            spec, changed = _make_repo_with_renames(Path(td))
            # Inject a guaranteed P-001 into the post-rename target
            # so a real violation surfaces. The rename row points
            # to ``spec/intro.md``; we mutate that file.
            (spec / "intro.md").write_text(
                "# spec\n\n<!-- TODO: -->\n"
            )
            rc, out, _ = _run(
                "--root", str(spec), "--repo-root", td,
                "--changed-files", str(changed),
                *flag,
                cwd=Path(td),
            )
            self.assertEqual(rc, 1)  # violation expected
            return out.count("P-001")

    def test_force_on_off_and_auto_yield_same_violation_count(self) -> None:
        auto = self._violation_count()
        on = self._violation_count("--diff-rename-log")
        off = self._violation_count("--no-diff-rename-log")
        self.assertEqual(auto, on)
        self.assertEqual(auto, off)
        self.assertGreater(auto, 0,
            "fixture should fire at least one P-001")


class RenameIntakeRendererUnit(unittest.TestCase):
    """Direct unit tests on the renderer + the changed-files
    intake parser. Cheaper than subprocess for the formatting
    corner cases (long paths, missing scores, missing old)."""

    def setUp(self) -> None:
        from conftest_shim import load_placeholder_linter
        self.chk = load_placeholder_linter()

    def test_normalise_captures_tab_and_arrow_intake(self) -> None:
        intake: list = []
        out = self.chk._normalise_changed_lines(
            ["R087\tspec/old.md\tspec/new.md",
             "spec/legacy.md => spec/intro.md",
             "spec/plain.md"],
            intake=intake,
        )
        # Post-state paths are the linter's source of truth.
        self.assertEqual(out,
            ["spec/new.md", "spec/intro.md", "spec/plain.md"])
        # Plain row is NOT captured (we can't tell if it was a
        # rename collapsed by upstream tooling).
        self.assertEqual(len(intake), 2)
        self.assertEqual(intake[0].kind, "R")
        self.assertEqual(intake[0].score, 87)
        self.assertEqual(intake[0].old, "spec/old.md")
        self.assertEqual(intake[0].new, "spec/new.md")
        # Arrow form has no score.
        self.assertEqual(intake[1].kind, "R")
        self.assertIsNone(intake[1].score)
        self.assertEqual(intake[1].old, "spec/legacy.md")
        self.assertEqual(intake[1].new, "spec/intro.md")

    def test_normalise_intake_none_skips_allocation(self) -> None:
        """Passing ``intake=None`` must keep the legacy fast path
        identical to the pre-flag behaviour — same return value,
        no side effects."""
        out = self.chk._normalise_changed_lines(
            ["R087\tspec/old.md\tspec/new.md",
             "spec/legacy.md => spec/intro.md"],
        )
        self.assertEqual(out, ["spec/new.md", "spec/intro.md"])

    def test_renderer_truncates_long_old_paths_with_leading_ellipsis(self) -> None:
        """Long OLD paths get a leading ``…`` so the leaf filename
        (the bit operators visually scan for) is preserved."""
        long_old = "spec/" + "a" * 200 + "/leaf.md"
        row = self.chk._DiffIntakeRow(
            kind="R", score=92, old=long_old, new="spec/new.md",
        )
        buf = io.StringIO()
        self.chk._render_rename_intake_table([row], buf)
        text = buf.getvalue()
        self.assertIn("…", text)
        # Tail (the leaf) survives.
        self.assertIn("leaf.md", text)
        # Head (the noise) does NOT appear in full.
        self.assertNotIn("a" * 200, text)

    def test_renderer_aligns_unscored_rows_under_score_column(self) -> None:
        rows = [
            self.chk._DiffIntakeRow("R", 92, "spec/a.md", "spec/x.md"),
            self.chk._DiffIntakeRow("R", None, "spec/b.md", "spec/y.md"),
        ]
        buf = io.StringIO()
        self.chk._render_rename_intake_table(rows, buf)
        lines = buf.getvalue().splitlines()
        # Find the column position of the OLD value in each data
        # row — they must match exactly. If alignment broke, the
        # OLD column would shift by one row vs. the next.
        a_idx = lines[2].index("spec/a.md")
        b_idx = lines[3].index("spec/b.md")
        self.assertEqual(a_idx, b_idx)

    def test_renderer_handles_empty_old_as_unknown(self) -> None:
        row = self.chk._DiffIntakeRow("R", 50, "", "spec/new.md")
        buf = io.StringIO()
        self.chk._render_rename_intake_table([row], buf)
        self.assertIn("(unknown)", buf.getvalue())

    def test_renderer_empty_input_emits_header_and_hint(self) -> None:
        buf = io.StringIO()
        self.chk._render_rename_intake_table([], buf)
        text = buf.getvalue()
        self.assertIn("0 row(s)", text)
        self.assertIn("no rename or copy rows", text)


if __name__ == "__main__":
    unittest.main()