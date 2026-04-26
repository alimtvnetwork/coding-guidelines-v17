"""Unit tests for ``_parse_unified_diff_post`` in
``linter-scripts/check-placeholder-comments.py``.

Covers the three edge classes called out by the spec:

* **Blank lines** — empty rows inside a hunk are valid context
  (a context line whose payload happens to be empty); the parser
  must still advance the post-state line counter so subsequent
  lines stay correctly numbered.
* **Missing hunks** — completely empty diff, file-headers only,
  malformed ``@@`` header, and lines outside any hunk must all
  produce an empty ``_DiffExcerpts`` rather than crashing or
  generating bogus line numbers.
* **Removed-line gaps** — ``-`` rows must NOT advance the post-
  state line counter (they have no post-state coordinate); the
  next ``+`` / `` `` row keeps the counter the parser was on.

Each test is a pure-function check on synthetic diff text — no
git invocation, no temp files. Tests assert the post-state
``lines`` map plus ``min_line`` / ``max_line`` because those three
together are the public contract consumed by ``render()``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Make the shim importable when the tests are invoked directly
# (``python3 linter-scripts/tests/test_placeholder_diff_parser.py``)
# as well as through the unittest discovery runner.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest_shim import load_placeholder_linter  # noqa: E402

chk = load_placeholder_linter()
_parse = chk._parse_unified_diff_post
_DiffExcerpts = chk._DiffExcerpts


def _diff(*lines: str) -> str:
    """Join hunk lines with newlines and a trailing newline so the
    parser sees them the way ``git diff`` actually emits them."""
    return "\n".join(lines) + "\n"


class ParseEmptyAndHeaderOnly(unittest.TestCase):
    """Diffs with no hunks must yield an empty excerpt.

    These cases really happen: ``git diff -U0 base...HEAD --
    file.md`` against an unchanged file emits the empty string;
    against a binary file or a mode-only change it emits header
    rows but no ``@@`` block. Either way the renderer must see
    zero lines and return early.
    """

    def test_empty_string(self) -> None:
        ex = _parse("")
        self.assertEqual(ex.lines, {})
        self.assertEqual(ex.min_line, 0)
        self.assertEqual(ex.max_line, 0)

    def test_only_whitespace(self) -> None:
        # ``"\n\n\n"`` splits into three empty rows. None of them
        # can be inside a hunk (no ``@@`` was ever seen), so the
        # parser must drop them.
        ex = _parse("\n\n\n")
        self.assertEqual(ex.lines, {})
        self.assertEqual(ex.max_line, 0)

    def test_file_headers_only_no_hunk(self) -> None:
        # Real shape of a binary-file diff: ``--- a/f``, ``+++ b/f``
        # and a ``Binary files ... differ`` line, with no hunk.
        ex = _parse(_diff(
            "diff --git a/spec/x.md b/spec/x.md",
            "index abc..def 100644",
            "--- a/spec/x.md",
            "+++ b/spec/x.md",
            "Binary files a/spec/x.md and b/spec/x.md differ",
        ))
        self.assertEqual(ex.lines, {})
        self.assertEqual(ex.min_line, 0)
        self.assertEqual(ex.max_line, 0)

    def test_malformed_hunk_header_drops_payload(self) -> None:
        # ``@@ broken @@`` doesn't match _HUNK_HEADER_RE → the
        # parser must reset ``in_hunk`` and ignore the rows that
        # follow until the next valid header. Otherwise an
        # attacker-controlled diff (or just a weird tool output)
        # could inject phantom post-state lines.
        ex = _parse(_diff(
            "@@ broken @@",
            "+phantom",
            " also-phantom",
        ))
        self.assertEqual(ex.lines, {})

    def test_lines_before_any_hunk_are_ignored(self) -> None:
        # ``+`` rows before the first ``@@`` are git's own
        # ``+++ b/file`` line. Parser must NOT confuse them for
        # added content — the ``in_hunk`` guard handles this.
        ex = _parse(_diff(
            "--- a/f",
            "+++ b/f",
            "+ this looks like an addition but is the file header",
            " and this is a stray context-looking row",
        ))
        self.assertEqual(ex.lines, {})


class ParseBlankLines(unittest.TestCase):
    """A blank line inside a hunk is a valid context line.

    ``git diff`` emits each context line as `` <text>`` with a
    leading space. For an empty source line that becomes a single
    space (``" "``); after Python's ``splitlines()`` on the diff
    text, the row may arrive as ``""`` (empty string) when the
    leading-space char itself was stripped by the producer (some
    git pagers do this). The parser must treat the empty row as
    a context line whose payload is ``""`` so downstream line
    numbers stay correct.
    """

    def test_blank_context_line_advances_counter(self) -> None:
        ex = _parse(_diff(
            "@@ -10,3 +10,3 @@",
            " before",
            "",                # blank context line — payload ""
            " after",
        ))
        # Lines 10/11/12 must all be present, 11 must be empty.
        self.assertEqual(ex.lines[10], (" ", "before"))
        self.assertEqual(ex.lines[11], (" ", ""))
        self.assertEqual(ex.lines[12], (" ", "after"))
        self.assertEqual(ex.min_line, 10)
        self.assertEqual(ex.max_line, 12)

    def test_two_consecutive_blank_lines(self) -> None:
        ex = _parse(_diff(
            "@@ -5,1 +5,3 @@",
            "+head",
            "",
            "",
            "+tail",
        ))
        self.assertEqual(ex.lines[5], ("+", "head"))
        self.assertEqual(ex.lines[6], (" ", ""))
        self.assertEqual(ex.lines[7], (" ", ""))
        self.assertEqual(ex.lines[8], ("+", "tail"))

    def test_blank_added_line_via_plus_space(self) -> None:
        # ``+`` followed by nothing (a literal added blank line)
        # — the body slice ``raw[1:]`` is ``""``. Counter still
        # advances; line is recorded as added with empty text.
        ex = _parse(_diff(
            "@@ -1,1 +1,3 @@",
            " keep",
            "+",               # added blank line
            "+done",
        ))
        self.assertEqual(ex.lines[1], (" ", "keep"))
        self.assertEqual(ex.lines[2], ("+", ""))
        self.assertEqual(ex.lines[3], ("+", "done"))

    def test_blank_outside_hunk_ignored(self) -> None:
        # The ``in_hunk`` guard short-circuits the empty-row branch
        # so a blank line BEFORE the first ``@@`` doesn't allocate
        # a phantom ``lines[0]`` entry.
        ex = _parse(_diff(
            "diff --git a/f b/f",
            "",                # blank between header lines — ignored
            "@@ -1,1 +1,1 @@",
            "+only",
        ))
        self.assertNotIn(0, ex.lines)
        self.assertEqual(ex.lines[1], ("+", "only"))


class ParseRemovedLineGaps(unittest.TestCase):
    """Removed (``-``) rows must NOT advance the post-state counter.

    The cardinal rule of unified diff parsing on the post-state
    side: a ``-`` row exists only on the pre-state side, has no
    post-state coordinate, and therefore must not bump the line
    counter. Getting this wrong produces excerpts that are off by
    the deletion count on every subsequent line — a bug that's
    invisible in a single-hunk smoke test but corrupts every
    multi-hunk file with deletions.
    """

    def test_single_removal_does_not_shift_counter(self) -> None:
        ex = _parse(_diff(
            "@@ -10,3 +10,2 @@",
            " keep1",          # post-line 10
            "-removed",        # NO post-line — counter stays at 11
            " keep2",          # post-line 11
        ))
        self.assertEqual(ex.lines[10], (" ", "keep1"))
        self.assertEqual(ex.lines[11], (" ", "keep2"))
        self.assertNotIn(12, ex.lines,
                         "removed line must not allocate post-line 12")
        self.assertEqual(ex.max_line, 11)

    def test_multiple_removals_then_addition(self) -> None:
        # Three deletions followed by two additions — classic
        # "replace 3 lines with 2" hunk. Post-state must be
        # 20 (context), 21 (added), 22 (added).
        ex = _parse(_diff(
            "@@ -20,4 +20,3 @@",
            " ctx",            # 20
            "-gone1",
            "-gone2",
            "-gone3",
            "+new1",           # 21 — counter must NOT have advanced past 21
            "+new2",           # 22
        ))
        self.assertEqual(ex.lines[20], (" ", "ctx"))
        self.assertEqual(ex.lines[21], ("+", "new1"))
        self.assertEqual(ex.lines[22], ("+", "new2"))
        self.assertEqual(ex.min_line, 20)
        self.assertEqual(ex.max_line, 22)

    def test_removal_at_hunk_start_keeps_counter_at_header_value(self) -> None:
        # Header says post starts at line 50. First non-header row
        # is a ``-`` deletion. Counter must STILL be 50 when the
        # following ``+`` arrives.
        ex = _parse(_diff(
            "@@ -50,2 +50,1 @@",
            "-removed-first",
            "+kept",
        ))
        self.assertEqual(ex.lines, {50: ("+", "kept")})
        self.assertEqual(ex.min_line, 50)
        self.assertEqual(ex.max_line, 50)

    def test_pure_deletion_hunk_yields_no_post_state(self) -> None:
        # ``+0`` post-state count (every line removed): no post-
        # coordinate exists at all, so the resulting excerpt is
        # empty even though the diff was non-trivial.
        ex = _parse(_diff(
            "@@ -10,3 +10,0 @@",
            "-line10",
            "-line11",
            "-line12",
        ))
        self.assertEqual(ex.lines, {})
        self.assertEqual(ex.max_line, 0)

    def test_no_newline_marker_does_not_advance_counter(self) -> None:
        # ``\ No newline at end of file`` is a metadata row — must
        # be ignored without advancing the post-state counter.
        ex = _parse(_diff(
            "@@ -1,1 +1,1 @@",
            "-old",
            "\\ No newline at end of file",
            "+new",
            "\\ No newline at end of file",
        ))
        self.assertEqual(ex.lines, {1: ("+", "new")})
        self.assertEqual(ex.max_line, 1)


class ParseMultiHunkAndDefensive(unittest.TestCase):
    """Cross-cutting correctness for multi-hunk inputs and the
    parser's defensive aborts on malformed payloads."""

    def test_two_hunks_record_independent_line_numbers(self) -> None:
        # Two hunks far apart. The parser must reset the post-
        # state counter at each ``@@`` header so lines 100-101
        # don't get confused with lines 5-6.
        ex = _parse(_diff(
            "@@ -5,1 +5,2 @@",
            " a",               # 5
            "+b",               # 6
            "@@ -100,1 +100,2 @@",
            " x",               # 100
            "+y",               # 101
        ))
        self.assertEqual(ex.lines[5], (" ", "a"))
        self.assertEqual(ex.lines[6], ("+", "b"))
        self.assertEqual(ex.lines[100], (" ", "x"))
        self.assertEqual(ex.lines[101], ("+", "y"))
        self.assertEqual(ex.min_line, 5)
        self.assertEqual(ex.max_line, 101)
        # CRITICAL: the gap between hunks is NOT populated.
        for ln in range(7, 100):
            self.assertNotIn(ln, ex.lines,
                             f"phantom line {ln} between hunks")

    def test_unknown_intra_hunk_row_aborts_current_hunk(self) -> None:
        # An unrecognised first character inside a hunk (``?`` is
        # never emitted by ``git diff`` but might arrive from a
        # combined-diff or a buggy filter) must trip the defensive
        # fall-through that flips ``in_hunk = False`` so subsequent
        # rows can't desync the line counter.
        ex = _parse(_diff(
            "@@ -1,1 +1,3 @@",
            "+kept",            # 1
            "?garbage",         # aborts hunk
            "+would-have-been-2",
            "@@ -10,1 +10,1 @@",
            "+resumed",         # 10 — fresh hunk recovers
        ))
        self.assertEqual(ex.lines.get(1), ("+", "kept"))
        self.assertNotIn(2, ex.lines)
        self.assertEqual(ex.lines[10], ("+", "resumed"))

    def test_unscored_hunk_header_uses_implicit_count_of_one(self) -> None:
        # ``@@ -5 +5 @@`` (no ``,N``) is a valid git emission for a
        # single-line change. The parser only needs ``+<start>`` so
        # this must work.
        ex = _parse(_diff(
            "@@ -5 +5 @@",
            "+only",
        ))
        self.assertEqual(ex.lines, {5: ("+", "only")})

    def test_returned_object_is_a_diffexcerpts(self) -> None:
        # Cheap structural assertion so a future refactor that
        # accidentally returns a tuple gets caught immediately.
        ex = _parse("")
        self.assertIsInstance(ex, _DiffExcerpts)


class RenderInteractsWithParser(unittest.TestCase):
    """Smoke checks that a parsed diff renders the expected window
    so a regression in the parser's bookkeeping shows up not just
    in the dict but in the human-facing output too."""

    def test_render_centers_on_violation_line(self) -> None:
        ex = _parse(_diff(
            "@@ -1,1 +1,5 @@",
            "+a",
            "+b",
            "+c",
            "+d",
            "+e",
        ))
        out = ex.render(line=3, context=1)
        # Should include exactly lines 2, 3, 4 (3 ± 1) with the
        # focus marker on 3.
        self.assertEqual(len(out), 3)
        self.assertIn("+ b", out[0])
        self.assertTrue(out[1].lstrip().startswith("►"))
        self.assertIn("+ c", out[1])
        self.assertIn("+ d", out[2])

    def test_render_empty_when_no_hunks(self) -> None:
        self.assertEqual(_parse("").render(line=1, context=3), [])

    def test_render_far_outside_returns_sentinel(self) -> None:
        ex = _parse(_diff(
            "@@ -1,1 +1,1 @@",
            "+only",
        ))
        out = ex.render(line=999, context=2)
        self.assertEqual(len(out), 1)
        self.assertIn("not in current diff hunks", out[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)