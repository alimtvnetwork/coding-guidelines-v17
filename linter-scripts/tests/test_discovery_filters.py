"""Tests for the --extension / --include / --exclude discovery filters.

Coverage matrix:

* **--extension** widens the default ``.md``-only scan to ``.mdx``
  and ``.txt`` and de-duplicates redundant entries (cache-key
  stability).
* **--include** restricts discovery to a glob (full path or basename
  match, ``**`` recursion).
* **--exclude** drops files even if they would otherwise be
  included.
* **--include + --exclude** interact correctly (exclude wins).
* The hidden-directory guard (``.foo/``) is still unconditional —
  no glob can re-enable a hidden file.
* Validation errors (empty extension, malformed glob) exit 2 with
  a friendly stderr message and no stdout output.
* The cache key incorporates extensions + include + exclude so a
  narrower scope cannot satisfy a wider PASS sentinel.
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

chk = load_placeholder_linter()
LINTER = (Path(__file__).resolve().parent.parent
          / "check-placeholder-comments.py")


def _run(*args: str, cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run([sys.executable, str(LINTER), *args],
                       cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _mixed_repo(td: Path) -> Path:
    """Spec tree with mixed extensions and a hidden sibling."""
    spec = td / "spec"
    spec.mkdir()
    (spec / "a.md").write_text("# A\n", encoding="utf-8")
    (spec / "b.mdx").write_text("# B\n", encoding="utf-8")
    (spec / "notes.txt").write_text("plain\n", encoding="utf-8")
    sub = spec / "sub"; sub.mkdir()
    (sub / "c.md").write_text("# C\n", encoding="utf-8")
    (sub / "d.mdx").write_text("# D\n", encoding="utf-8")
    (spec / "CHANGELOG.md").write_text("# CL\n", encoding="utf-8")
    hidden = spec / ".cache"; hidden.mkdir()
    (hidden / "x.md").write_text("# X\n", encoding="utf-8")
    return spec


def _list(td: Path, *flags: str) -> list[str]:
    """Run --list-files --json and return the discovered paths."""
    rc, out, err = _run("--root", "spec", "--repo-root", ".",
                        "--list-files", "--json", *flags, cwd=td)
    assert rc == 0, f"rc={rc} stderr={err}"
    return sorted(r["path"] for r in json.loads(out))


class IterMarkdownFiles(unittest.TestCase):
    """Pure-function tests on the iterator (no subprocess)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tdp = Path(self._tmp.name)
        _mixed_repo(self.tdp)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _names(self, **kwargs) -> list[str]:
        root = self.tdp / "spec"
        return sorted(p.relative_to(root).as_posix()
                      for p in chk.iter_markdown_files(root, **kwargs))

    def test_default_extension_is_md_only(self) -> None:
        # Historical behaviour: only ``.md`` files are discovered.
        self.assertEqual(
            self._names(),
            ["CHANGELOG.md", "a.md", "sub/c.md"],
        )

    def test_multiple_extensions_widen_scan(self) -> None:
        names = self._names(extensions=("md", "mdx", "txt"))
        self.assertIn("b.mdx", names)
        self.assertIn("notes.txt", names)
        self.assertIn("sub/d.mdx", names)

    def test_extension_leading_dot_normalised(self) -> None:
        # ``--extension .md`` and ``--extension md`` must be equivalent.
        self.assertEqual(
            self._names(extensions=(".md",)),
            self._names(extensions=("md",)),
        )

    def test_hidden_dir_unconditionally_excluded(self) -> None:
        # Even a wide-open --include can't pull in `.cache/x.md`.
        names = self._names(include=("**/*.md",))
        self.assertFalse(any(".cache" in n for n in names),
                         f"hidden dir leaked: {names}")

    def test_include_basename_match(self) -> None:
        # No path separator ⇒ matched against basename too.
        self.assertEqual(
            self._names(include=("CHANGELOG.md",)),
            ["CHANGELOG.md"],
        )

    def test_include_full_path_match(self) -> None:
        self.assertEqual(
            self._names(include=("sub/*.md",)),
            ["sub/c.md"],
        )

    def test_include_recursive_glob(self) -> None:
        # ``**`` matches across directory boundaries.
        names = self._names(extensions=("md", "mdx"),
                            include=("**/*.mdx",))
        self.assertEqual(names, ["b.mdx", "sub/d.mdx"])

    def test_exclude_drops_basename_match(self) -> None:
        names = self._names(exclude=("CHANGELOG.md",))
        self.assertNotIn("CHANGELOG.md", names)

    def test_exclude_beats_include(self) -> None:
        # File matches both include and exclude → exclude wins.
        names = self._names(include=("**/*.md",),
                            exclude=("sub/*.md",))
        self.assertNotIn("sub/c.md", names)
        self.assertIn("a.md", names)


class CliEndToEnd(unittest.TestCase):
    """Subprocess tests proving CLI flags reach the iterator."""

    def test_extension_widens_listing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _mixed_repo(tdp)
            paths = _list(tdp,
                          "--extension", "md",
                          "--extension", "mdx",
                          "--extension", "txt")
        self.assertIn("spec/b.mdx", paths)
        self.assertIn("spec/notes.txt", paths)
        self.assertIn("spec/sub/d.mdx", paths)

    def test_include_narrows_listing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _mixed_repo(tdp)
            paths = _list(tdp, "--include", "sub/*.md")
        self.assertEqual(paths, ["spec/sub/c.md"])

    def test_exclude_drops_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _mixed_repo(tdp)
            paths = _list(tdp, "--exclude", "CHANGELOG.md")
        self.assertNotIn("spec/CHANGELOG.md", paths)
        # Other ``.md`` files are still discovered.
        self.assertIn("spec/a.md", paths)
        self.assertIn("spec/sub/c.md", paths)

    def test_combination_with_extension(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _mixed_repo(tdp)
            paths = _list(tdp,
                          "--extension", "md",
                          "--extension", "mdx",
                          "--include", "sub/**",
                          "--exclude", "**/*.md")
        # Only sub/d.mdx survives: in sub/, mdx-only after exclude.
        self.assertEqual(paths, ["spec/sub/d.mdx"])

    def test_invalid_extension_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _mixed_repo(tdp)
            rc, out, err = _run("--root", "spec", "--repo-root", ".",
                                "--list-files", "--extension", "",
                                cwd=tdp)
        self.assertEqual(rc, 2)
        self.assertIn("--extension", err)
        self.assertEqual(out, "",
                         "stdout should stay clean when validation fails")

    def test_empty_include_pattern_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td); _mixed_repo(tdp)
            rc, _, err = _run("--root", "spec", "--repo-root", ".",
                              "--list-files", "--include", "  ",
                              cwd=tdp)
        self.assertEqual(rc, 2)
        self.assertIn("--include", err)


class CacheKeyIncorporatesFilters(unittest.TestCase):
    """The cache key must change when discovery scope changes,
    otherwise a narrow PASS could satisfy a wider query."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "spec"
        _mixed_repo(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _key(self, **kwargs) -> str:
        return chk._compute_cache_key(self.root, frozenset(), **kwargs)

    def test_default_key_is_stable(self) -> None:
        self.assertEqual(self._key(), self._key())

    def test_extension_change_invalidates_key(self) -> None:
        self.assertNotEqual(
            self._key(),
            self._key(extensions=("md", "mdx")),
        )

    def test_include_change_invalidates_key(self) -> None:
        self.assertNotEqual(
            self._key(),
            self._key(include=("sub/*.md",)),
        )

    def test_exclude_change_invalidates_key(self) -> None:
        self.assertNotEqual(
            self._key(),
            self._key(exclude=("CHANGELOG.md",)),
        )

    def test_extension_order_does_not_matter(self) -> None:
        # ``--extension a --extension b`` and ``--extension b
        # --extension a`` produce the same file set ⇒ same key.
        self.assertEqual(
            self._key(extensions=("md", "mdx")),
            self._key(extensions=("mdx", "md")),
        )

    def test_include_order_does_not_matter(self) -> None:
        self.assertEqual(
            self._key(include=("a", "b")),
            self._key(include=("b", "a")),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
