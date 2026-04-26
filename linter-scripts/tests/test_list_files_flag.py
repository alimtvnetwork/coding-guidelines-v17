"""End-to-end tests for the ``--list-files`` diagnostic flag.

The flag prints exactly which `.md` files were discovered and how
each will be classified for the active allowlist settings, then
exits 0 without linting. Coverage:

* **Full-tree mode** — every discovered file is `linted`; hidden
  directories (``.foo/``) are excluded just like the main scan.
* **Diff mode (--changed-files)** — files in the changed set are
  `linted`; the rest are `cross-file-only` (still scanned for
  cross-file P-007 bullets, but no per-file violations).
* **Empty changed set** — emits a clean ``[]`` in JSON mode and a
  friendly text banner otherwise; never falls through to the
  "no spec changes" PASS message that would confuse a JSON consumer.
* **JSON output is single-document** — no leading "diff-mode active"
  banner that would break ``json.loads(stdout)``.
* **Schema** — every JSON row is exactly
  ``{"path": str, "status": str, "reason": str}``.
* **Sort order** — listing is sorted by ``path`` so diffs over time
  are stable.

The tests subprocess the linter (rather than calling ``main()``
in-process) so we exercise argparse + module-load + stdout flushing
the same way CI invokes it.
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
    """Build a tiny spec tree: 3 valid `.md` files plus a hidden
    sibling that must be excluded by ``iter_markdown_files``."""
    spec = td / "spec"
    spec.mkdir()
    (spec / "a.md").write_text("# A\n", encoding="utf-8")
    (spec / "b.md").write_text("# B\n", encoding="utf-8")
    sub = spec / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("# C\n", encoding="utf-8")
    hidden = spec / ".hidden"
    hidden.mkdir()
    (hidden / "x.md").write_text("# X\n", encoding="utf-8")
    return spec


class ListFilesFullTree(unittest.TestCase):
    """Full-tree mode: every discovered file is ``linted``."""

    def test_text_listing_marks_all_linted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _make_repo(tdp)
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--list-files", cwd=tdp)
        self.assertEqual(rc, 0, f"stderr={err}")
        # Banner mentions the configured extensions so authors can
        # eyeball whether their --extension list took effect. The
        # default is ``md`` only, no leading-backtick decoration.
        self.assertIn("3 .md file(s) discovered", out)
        self.assertIn("(full-tree mode)", out)
        self.assertIn("3 linted, 0 cross-file-only", out)
        # Status column on every listing row must be ``linted``;
        # ignore the summary banner and trailing footer.
        listing = [l for l in out.splitlines()
                   if l.startswith("  ") and not l.startswith("  Run")]
        self.assertTrue(listing)
        for line in listing:
            self.assertIn("linted", line)
            self.assertNotIn("cross-file-only", line,
                             f"unexpected cross-file row: {line}")

    def test_json_listing_schema_and_sort(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _make_repo(tdp)
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--list-files", "--json", cwd=tdp)
        self.assertEqual(rc, 0, f"stderr={err}")
        payload = json.loads(out)
        self.assertEqual(len(payload), 3)
        # Schema is exact — no stray keys leak through.
        for row in payload:
            self.assertEqual(set(row), {"path", "status", "reason"},
                             f"unexpected schema: {row}")
            self.assertEqual(row["status"], "linted")
            self.assertTrue(row["reason"].startswith("full-tree"))
        # Sorted by path → ``sub/c.md`` lands after ``b.md``.
        self.assertEqual([r["path"] for r in payload],
                         ["spec/a.md", "spec/b.md", "spec/sub/c.md"])

    def test_hidden_dirs_excluded(self) -> None:
        # The fixture includes ``spec/.hidden/x.md``; the listing
        # must omit it, mirroring ``iter_markdown_files``.
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _make_repo(tdp)
            rc, out, _ = _run("--root", "spec", "--repo-root", ".",
                              "--list-files", "--json", cwd=tdp)
        self.assertEqual(rc, 0)
        paths = [r["path"] for r in json.loads(out)]
        self.assertFalse(any(".hidden" in p for p in paths),
                         f"hidden dir leaked: {paths}")


class ListFilesDiffMode(unittest.TestCase):
    """Diff mode (via ``--changed-files``, no git required)."""

    def test_classifies_linted_vs_cross_file_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _make_repo(tdp)
            cf = tdp / "changed.txt"
            cf.write_text("spec/a.md\nspec/sub/c.md\n", encoding="utf-8")
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--changed-files", str(cf),
                                "--list-files", "--json", cwd=tdp)
        self.assertEqual(rc, 0, f"stderr={err}")
        by_path = {r["path"]: r for r in json.loads(out)}
        self.assertEqual(by_path["spec/a.md"]["status"], "linted")
        self.assertEqual(by_path["spec/sub/c.md"]["status"], "linted")
        # The unchanged file is scanned only for cross-file P-007.
        self.assertEqual(by_path["spec/b.md"]["status"], "cross-file-only")
        # Reason mentions P-007 (the rule that requires cross-file
        # bullet collection) so an operator can map the status back
        # to a concrete rule without checking the docs.
        self.assertIn("P-007", by_path["spec/b.md"]["reason"])
        self.assertIn("unchanged", by_path["spec/b.md"]["reason"])

    def test_empty_changed_set_emits_clean_json_array(self) -> None:
        # An empty ``--changed-files`` document used to fall through
        # to the "no spec changes" PASS branch which prints ``[]``
        # in JSON mode but ALSO would have skipped --list-files
        # entirely in an earlier draft. Keep the regression locked.
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _make_repo(tdp)
            cf = tdp / "empty.txt"; cf.write_text("", encoding="utf-8")
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--changed-files", str(cf),
                                "--list-files", "--json", cwd=tdp)
        self.assertEqual(rc, 0, f"stderr={err}")
        self.assertEqual(out.strip(), "[]",
                         f"expected bare empty JSON array, got: {out!r}")

    def test_empty_changed_set_text_message(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _make_repo(tdp)
            cf = tdp / "empty.txt"; cf.write_text("", encoding="utf-8")
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--changed-files", str(cf),
                                "--list-files", cwd=tdp)
        self.assertEqual(rc, 0, f"stderr={err}")
        self.assertIn("no `.md` files", out)

    def test_json_output_is_single_document(self) -> None:
        # Regression guard: the diff-mode "ℹ️" banner that the
        # linter prints in human mode must NOT appear in --json
        # --list-files output, otherwise json.loads(stdout) breaks.
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _make_repo(tdp)
            cf = tdp / "changed.txt"
            cf.write_text("spec/a.md\n", encoding="utf-8")
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--changed-files", str(cf),
                                "--list-files", "--json", cwd=tdp)
        self.assertEqual(rc, 0, f"stderr={err}")
        # The whole thing must round-trip through json.loads.
        json.loads(out)  # raises if any banner leaked


class ListFilesIsReadOnly(unittest.TestCase):
    """The flag must not actually lint, write caches, or emit
    violations — even when the tree contains broken placeholders."""

    def test_does_not_emit_violations(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec = tdp / "spec"; spec.mkdir()
            # Bare TODO would normally trip P-001.
            (spec / "bad.md").write_text("<!-- TODO -->\n",
                                         encoding="utf-8")
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--list-files", "--json", cwd=tdp)
        self.assertEqual(rc, 0, f"stderr={err}")  # not 1
        payload = json.loads(out)
        # Listing emits the file as linted; no P-001 row.
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["path"], "spec/bad.md")
        self.assertEqual(payload[0]["status"], "linted")
        self.assertNotIn("code", payload[0])
        self.assertNotIn("message", payload[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
