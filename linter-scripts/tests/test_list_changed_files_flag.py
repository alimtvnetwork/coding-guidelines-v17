"""End-to-end tests for the ``--list-changed-files`` diagnostic flag.

The flag is the diff-mode counterpart to ``--list-files``: it
classifies every post-state path that came out of ``git diff
--name-status`` (or ``--changed-files``) by how the diff-mode
allowlist treated it, then exits 0 without linting. Coverage:

* **All four statuses** — ``linted`` (kept), ``ignored-extension``
  (not `.md`), ``ignored-out-of-root`` (under repo but not under
  ``--root``), ``ignored-missing`` (matched filters but file gone).
* **Order preservation** — rows are emitted in git's original
  order, NOT sorted; the listing is an audit trail of the diff,
  not a deduplicated set.
* **Empty-changed-set escape hatch** — when every changed path
  is non-`.md` (e.g. a code-only PR), ``--list-changed-files``
  must still surface those rows instead of falling through to the
  "no spec changes, fast PASS" branch.
* **JSON schema** — single ``json.loads``-able array of
  ``{"path", "status", "reason"}`` objects, no banner noise on
  stdout.
* **Full-tree no-op** — without ``--diff-base`` / ``--changed-files``
  the flag prints an empty listing + hint and exits 0 (so a CI
  matrix can pass the flag unconditionally).

The tests subprocess the linter (rather than calling ``main()``
in-process) so we exercise argparse + stdout flushing the same
way CI invokes it.
"""

from __future__ import annotations

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


def _make_repo(td: Path) -> Path:
    """Layout::

        td/
          spec/
            intro.md       (exists, will be classified ``linted``)
          README.md        (exists, outside --root=spec/)
          src/
            foo.py         (exists, wrong extension)
    """
    (td / "spec").mkdir()
    (td / "spec" / "intro.md").write_text("# spec\n")
    (td / "README.md").write_text("# readme\n")
    (td / "src").mkdir()
    (td / "src" / "foo.py").write_text("x = 1\n")
    return td


class ListChangedFilesClassification(unittest.TestCase):
    """Verify each of the four classification statuses lands on the
    right row, and that the ``status`` column uses the literal names
    documented in the help text."""

    def test_all_four_statuses_via_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            # Order matters — we assert it round-trips below.
            (root / "changed.txt").write_text(
                "spec/intro.md\n"      # → linted
                "spec/missing.md\n"    # → ignored-missing (file absent)
                "src/foo.py\n"         # → ignored-extension
                "README.md\n"          # → ignored-out-of-root
            )
            rc, out, err = _run(
                "--root", "spec", "--repo-root", ".",
                "--changed-files", "changed.txt",
                "--list-changed-files", "--json",
                cwd=root,
            )
            self.assertEqual(rc, 0, f"stderr={err!r}")
            rows = json.loads(out)
            self.assertEqual(len(rows), 4)
            self.assertEqual(
                [r["status"] for r in rows],
                ["linted", "ignored-missing",
                 "ignored-extension", "ignored-out-of-root"],
            )
            self.assertEqual(
                [r["path"] for r in rows],
                ["spec/intro.md", "spec/missing.md",
                 "src/foo.py", "README.md"],
            )
            # Every row carries a non-empty human reason string —
            # the operator should never see a blank "reason" field.
            for r in rows:
                self.assertTrue(r["reason"],
                                f"reason missing on row {r}")

    def test_order_is_preserved_not_sorted(self) -> None:
        """Rows must come out in the order git reported them, even
        when alphabetic sort would produce a different sequence.
        Operators rely on this to map a diff line back to its row."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            (root / "changed.txt").write_text(
                "src/foo.py\n"     # 'i' > 's', would sort later
                "spec/intro.md\n"
            )
            rc, out, _ = _run(
                "--root", "spec", "--repo-root", ".",
                "--changed-files", "changed.txt",
                "--list-changed-files", "--json",
                cwd=root,
            )
            self.assertEqual(rc, 0)
            rows = json.loads(out)
            self.assertEqual([r["path"] for r in rows],
                             ["src/foo.py", "spec/intro.md"])


class ListChangedFilesEdgeCases(unittest.TestCase):

    def test_code_only_pr_still_emits_ignored_rows(self) -> None:
        """Regression guard: when every changed path is non-`.md`,
        ``changed_md`` is empty. The legacy "fast PASS" branch
        early-returns — but ``--list-changed-files`` must take
        priority and surface the ``ignored-extension`` rows."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            (root / "changed.txt").write_text(
                "src/foo.py\nsrc/bar.py\n"
            )
            rc, out, _ = _run(
                "--root", "spec", "--repo-root", ".",
                "--changed-files", "changed.txt",
                "--list-changed-files", "--json",
                cwd=root,
            )
            self.assertEqual(rc, 0)
            rows = json.loads(out)
            self.assertEqual(len(rows), 2)
            for r in rows:
                self.assertEqual(r["status"], "ignored-extension")

    def test_blank_and_comment_lines_ignored(self) -> None:
        """``--changed-files`` permits blanks + ``#`` comments;
        those must NOT appear as phantom ``ignored-*`` rows."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            (root / "changed.txt").write_text(
                "\n# this is a comment\nspec/intro.md\n   \n"
            )
            rc, out, _ = _run(
                "--root", "spec", "--repo-root", ".",
                "--changed-files", "changed.txt",
                "--list-changed-files", "--json",
                cwd=root,
            )
            self.assertEqual(rc, 0)
            rows = json.loads(out)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "linted")

    def test_full_tree_no_op_json(self) -> None:
        """Without --diff-base / --changed-files, the flag is a
        no-op: empty JSON array, exit 0, no error."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            rc, out, err = _run(
                "--root", "spec", "--repo-root", ".",
                "--list-changed-files", "--json",
                cwd=root,
            )
            self.assertEqual(rc, 0, f"stderr={err!r}")
            self.assertEqual(json.loads(out), [])

    def test_full_tree_no_op_text_includes_hint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            rc, out, _ = _run(
                "--root", "spec", "--repo-root", ".",
                "--list-changed-files",
                cwd=root,
            )
            self.assertEqual(rc, 0)
            # Hint should point the operator at --list-files, not
            # just silently exit.
            self.assertIn("--list-files", out)
            self.assertIn("no-op", out)


class ListChangedFilesOutputHygiene(unittest.TestCase):
    """Stdout in --json mode must be a single ``json.loads``-able
    document — no leading banner, no trailing summary."""

    def test_json_mode_suppresses_diff_mode_banner(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            (root / "changed.txt").write_text("spec/intro.md\n")
            rc, out, _ = _run(
                "--root", "spec", "--repo-root", ".",
                "--changed-files", "changed.txt",
                "--list-changed-files", "--json",
                cwd=root,
            )
            self.assertEqual(rc, 0)
            # Must parse as a single document. No leading
            # ``ℹ️  diff-mode active`` text on stdout.
            self.assertNotIn("diff-mode active", out)
            json.loads(out)  # raises if multi-document

    def test_text_mode_summary_counts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            (root / "changed.txt").write_text(
                "spec/intro.md\nsrc/foo.py\nREADME.md\n"
            )
            rc, out, _ = _run(
                "--root", "spec", "--repo-root", ".",
                "--changed-files", "changed.txt",
                "--list-changed-files",
                cwd=root,
            )
            self.assertEqual(rc, 0)
            # 1 linted, 2 ignored — summary line should reflect it.
            self.assertIn("3 changed path(s)", out)
            self.assertIn("1 linted", out)
            self.assertIn("2 ignored", out)

    def test_does_not_lint_or_emit_violations(self) -> None:
        """The flag is read-only: even if the kept file has a
        clear placeholder violation, exit code is 0 and no
        violation text appears on stdout."""
        with tempfile.TemporaryDirectory() as td:
            root = _make_repo(Path(td))
            # Inject a guaranteed P-001 violation: empty TODO.
            (root / "spec" / "intro.md").write_text(
                "# spec\n\n<!-- TODO: -->\n"
            )
            (root / "changed.txt").write_text("spec/intro.md\n")
            rc, out, _ = _run(
                "--root", "spec", "--repo-root", ".",
                "--changed-files", "changed.txt",
                "--list-changed-files",
                cwd=root,
            )
            self.assertEqual(rc, 0)
            self.assertNotIn("P-001", out)
            self.assertNotIn("violation", out.lower())


if __name__ == "__main__":
    unittest.main()