"""Matrix tests: legend visibility across {auto,on,off} × {text,json}.

The ``--similarity-legend`` flag governs whether a human-readable
cheat-sheet for the rename/copy intake table is appended after the
``totals:`` footer. Two output streams are at play:

* **text mode** (default) — the audit table is rendered to STDERR
  as column-aligned prose. The legend, when emitted, is appended to
  the *same* STDERR stream so machine consumers parsing the table
  up to the totals line keep working byte-for-byte.

* **JSON mode** (``--json``) — the audit payload is serialised as a
  single JSON document on STDOUT. The legend MUST be suppressed
  unconditionally so the JSON document stays parseable and STDERR
  stays free of prose that a downstream JSON consumer might
  accidentally pick up.

This module pins the full 3×2 matrix (mode × output format) plus a
couple of cross-mode invariants (no legend on STDOUT in text mode,
no legend tokens anywhere in JSON mode). The earlier
``test_similarity_legend_flag`` module covers resolver branches and
help-text examples; this one is dedicated to the user's explicit
ask: *"verify the legend is present or hidden based on the new
flag across both text and JSON output modes"*.
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

# A token that only appears in the rendered legend, never in the
# audit table itself or in any JSON key. Matching on this string
# (rather than the bare word "legend") avoids false positives from
# unrelated diagnostic copy that might mention legends in passing.
LEGEND_MARKER = "legend:"


def _run(*args: str, cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run([sys.executable, str(LINTER), *args],
                       cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _make_repo(td: Path) -> Path:
    spec = td / "spec"
    spec.mkdir()
    (spec / "intro.md").write_text("# spec\nplain prose.\n")
    (spec / "copy.md").write_text("# spec\nplain prose.\n")
    return spec


def _write_rename_payload(td: Path) -> Path:
    """A single R-record so the audit table has at least one
    similarity-bearing row to attach the legend to."""
    payload = td / "changed.txt"
    payload.write_text("R087\tspec/intro.md\tspec/copy.md\n")
    return payload


# ---------------------------------------------------------------
# Text-mode matrix: auto / on / off
# ---------------------------------------------------------------
class TextModeLegendMatrix(unittest.TestCase):
    """Text-mode (no ``--json``) legend visibility per flag value.

    Subprocess STDERR is a pipe (not a TTY), so ``auto`` resolves to
    *off* — same shape as a CI runner. Explicit ``on`` overrides
    that and forces emission; explicit ``off`` suppresses it.
    """

    def _invoke(self, legend: str) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec = _make_repo(tdp)
            payload = _write_rename_payload(tdp)
            return _run(
                "--root", str(spec),
                "--changed-files", str(payload),
                "--list-changed-files",
                "--with-similarity",
                "--similarity-legend", legend,
                cwd=tdp,
            )

    def test_text_auto_hides_legend_on_pipe(self) -> None:
        code, out, err = self._invoke("auto")
        self.assertEqual(code, 0, msg=f"stderr={err!r}")
        self.assertNotIn(LEGEND_MARKER, err,
            msg="auto mode under a non-TTY pipe must hide the "
                "legend (preserves the legacy STDERR byte stream)")
        self.assertNotIn(LEGEND_MARKER, out,
            msg="legend must never appear on STDOUT in text mode")
        # Sanity: the table itself still rendered.
        self.assertIn("totals:", err)

    def test_text_on_shows_legend_on_stderr(self) -> None:
        code, out, err = self._invoke("on")
        self.assertEqual(code, 0, msg=f"stderr={err!r}")
        self.assertIn(LEGEND_MARKER, err,
            msg="`--similarity-legend on` must emit the legend "
                "on STDERR even when the stream is a pipe")
        # Cross-stream invariant: STDOUT stays clean.
        self.assertNotIn(LEGEND_MARKER, out,
            msg="legend prose must never leak onto STDOUT")
        # Legend ordering: must come AFTER the totals footer so
        # tools parsing up to `totals:` see no schema drift.
        i_totals = err.find("totals:")
        i_legend = err.find(LEGEND_MARKER)
        self.assertGreater(i_totals, -1)
        self.assertGreater(i_legend, i_totals,
            msg="legend must follow `totals:` to keep legacy "
                "log scrapers byte-for-byte stable")

    def test_text_off_hides_legend_on_stderr(self) -> None:
        code, out, err = self._invoke("off")
        self.assertEqual(code, 0, msg=f"stderr={err!r}")
        self.assertNotIn(LEGEND_MARKER, err,
            msg="`--similarity-legend off` must suppress the "
                "legend regardless of stream type")
        self.assertNotIn(LEGEND_MARKER, out)
        # Sanity: table still rendered (off only hides the legend).
        self.assertIn("totals:", err)
        self.assertIn("spec/copy.md", err)


# ---------------------------------------------------------------
# JSON-mode matrix: auto / on / off — legend must NEVER appear
# ---------------------------------------------------------------
class JsonModeLegendMatrix(unittest.TestCase):
    """JSON output must stay legend-free for every flag value.

    The legend is prose intended for humans; emitting it would
    either break the JSON document on STDOUT or pollute STDERR
    in a way that downstream JSON consumers (which often capture
    both streams) might mis-classify. This class pins the
    invariant for all three flag values so a future renderer
    refactor can't silently regress it.
    """

    def _invoke(self, legend: str) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec = _make_repo(tdp)
            payload = _write_rename_payload(tdp)
            return _run(
                "--root", str(spec),
                "--changed-files", str(payload),
                "--list-changed-files",
                "--with-similarity",
                "--similarity-legend", legend,
                "--json",
                cwd=tdp,
            )

    def _assert_json_clean(self, legend: str) -> None:
        code, out, err = self._invoke(legend)
        self.assertEqual(code, 0,
            msg=f"unexpected exit; stdout={out!r} stderr={err!r}")
        # Hard invariant: the legend marker must not appear on
        # either stream — JSON consumers don't want prose anywhere.
        self.assertNotIn(LEGEND_MARKER, out,
            msg=f"[--similarity-legend {legend} --json] "
                "STDOUT must contain only the JSON document")
        self.assertNotIn(LEGEND_MARKER, err,
            msg=f"[--similarity-legend {legend} --json] "
                "STDERR must stay legend-free in JSON mode")
        # And STDOUT must still be valid JSON (proves the matrix
        # entry is meaningful — the linter actually ran in JSON
        # mode rather than silently falling back to text).
        try:
            json.loads(out)
        except json.JSONDecodeError as exc:  # pragma: no cover
            self.fail(f"STDOUT is not valid JSON for "
                      f"`--similarity-legend {legend}`: {exc}; "
                      f"out={out!r}")

    def test_json_auto_hides_legend(self) -> None:
        self._assert_json_clean("auto")

    def test_json_on_still_hides_legend(self) -> None:
        # Even though the user explicitly asked for the legend,
        # JSON mode wins: prose would corrupt the document.
        self._assert_json_clean("on")

    def test_json_off_hides_legend(self) -> None:
        self._assert_json_clean("off")


# ---------------------------------------------------------------
# Cross-cutting invariants that span text + JSON modes
# ---------------------------------------------------------------
class LegendCrossModeInvariants(unittest.TestCase):
    """Invariants that hold across BOTH output formats."""

    def _run_one(self, *, json_mode: bool, legend: str
                 ) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec = _make_repo(tdp)
            payload = _write_rename_payload(tdp)
            args = [
                "--root", str(spec),
                "--changed-files", str(payload),
                "--list-changed-files",
                "--with-similarity",
                "--similarity-legend", legend,
            ]
            if json_mode:
                args.append("--json")
            return _run(*args, cwd=tdp)

    def test_legend_never_lands_on_stdout(self) -> None:
        # Whichever mode/legend combo we pick, STDOUT is reserved
        # for the structured output (JSON document) or empty
        # (text mode renders the audit on STDERR). The legend
        # must NEVER appear there.
        for json_mode in (False, True):
            for legend in ("auto", "on", "off"):
                with self.subTest(json=json_mode, legend=legend):
                    code, out, err = self._run_one(
                        json_mode=json_mode, legend=legend)
                    self.assertEqual(code, 0, msg=f"err={err!r}")
                    self.assertNotIn(LEGEND_MARKER, out,
                        msg=f"STDOUT must be legend-free "
                            f"(json={json_mode}, "
                            f"legend={legend})")

    def test_json_mode_overrides_explicit_on(self) -> None:
        # Direct A/B: same `on` flag, only --json differs. The
        # text invocation emits the legend on STDERR; the JSON
        # invocation must not — proving --json takes precedence.
        _, _, err_text = self._run_one(json_mode=False, legend="on")
        _, out_json, err_json = self._run_one(
            json_mode=True, legend="on")
        self.assertIn(LEGEND_MARKER, err_text,
            msg="baseline: text+on should emit the legend")
        self.assertNotIn(LEGEND_MARKER, err_json,
            msg="--json must override `--similarity-legend on`")
        self.assertNotIn(LEGEND_MARKER, out_json)

    def test_text_on_vs_off_differ_only_by_legend_block(self) -> None:
        # A/B within text mode: the only delta between `on` and
        # `off` output should be the trailing legend block. The
        # audit table itself (everything up to and including
        # `totals:`) must be byte-identical.
        _, _, err_on = self._run_one(json_mode=False, legend="on")
        _, _, err_off = self._run_one(json_mode=False, legend="off")
        # Slice each STDERR up through the totals line and compare.
        def _through_totals(s: str) -> str:
            i = s.find("totals:")
            self.assertGreater(i, -1, msg=f"no totals line in {s!r}")
            # Include the rest of the totals line itself.
            eol = s.find("\n", i)
            return s[: eol + 1] if eol != -1 else s[:]
        self.assertEqual(
            _through_totals(err_on), _through_totals(err_off),
            msg="audit table prefix must be byte-identical "
                "between `--similarity-legend on` and `off`; "
                "only the trailing legend block may differ")


if __name__ == "__main__":
    unittest.main()