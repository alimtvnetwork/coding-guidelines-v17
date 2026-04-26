"""Pin the CLI flag matrix that gates ``rename_intake`` JSON
emission and the per-record presence of the ``similarity`` key.

The matrix is documented in ``README-rename-intake.md`` under
*"CLI flags that gate `rename_intake` JSON emission"*. This module
executes each row of the worked truth-table as a real subprocess
invocation so the documented contract and the implementation can
never silently diverge.

Concretely we pin three things:

1. **Emission gate** — only ``--list-changed-files`` AND ``--json``
   together produce a JSON array on STDERR. Either flag alone (or
   neither) yields no JSON document on STDERR.

2. **`similarity` key inclusion** — controlled exclusively by
   ``--with-similarity``. When OFF the key is **omitted entirely**
   from every record (not ``null``); when ON it is **present on
   every record** (value may be a sub-object or ``null``).

3. **No-op flags** — ``--similarity-legend`` is a no-op in
   ``--json`` mode, and ``--similarity-labels`` only ever ADDS a
   ``score_kind`` field to non-null ``similarity`` objects without
   changing whether the key itself is present.
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


def _setup(td: Path) -> tuple[Path, Path]:
    spec = td / "spec"
    spec.mkdir()
    (spec / "intro.md").write_text("# spec\nplain prose.\n")
    (spec / "copy.md").write_text("# spec\nplain prose.\n")
    payload = td / "changed.txt"
    # One scored R, one plain M — exercises both the
    # similarity-bearing and the similarity:null record shapes.
    payload.write_text(
        "R087\tspec/intro.md\tspec/copy.md\n"
        "M\tspec/intro.md\n"
    )
    return spec, payload


def _try_parse_json_array(text: str) -> list | None:
    """Return the parsed JSON array if ``text`` is one, else None.

    The audit array is emitted as a single ``print`` so STDERR is
    *exactly* one JSON document followed by a trailing newline. We
    don't try to fish a JSON document out of a noisy stream — if
    STDERR isn't a clean JSON array, the gate did not fire.
    """
    s = text.strip()
    if not s.startswith("["):
        return None
    try:
        v = json.loads(s)
    except json.JSONDecodeError:
        return None
    return v if isinstance(v, list) else None


# ---------------------------------------------------------------
# (1) Emission gate: only --list-changed-files + --json emits JSON
# ---------------------------------------------------------------
class EmissionGate(unittest.TestCase):
    def _invoke(self, *extra: str) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec, payload = _setup(tdp)
            return _run(
                "--root", str(spec),
                "--changed-files", str(payload),
                *extra, cwd=tdp,
            )

    def test_neither_flag_no_json_array(self) -> None:
        code, _out, err = self._invoke()
        self.assertEqual(code, 0, msg=f"err={err!r}")
        self.assertIsNone(_try_parse_json_array(err),
            msg="without --list-changed-files no audit is built")

    def test_json_alone_no_audit_on_stderr(self) -> None:
        code, _out, err = self._invoke("--json")
        self.assertEqual(code, 0, msg=f"err={err!r}")
        self.assertIsNone(_try_parse_json_array(err),
            msg="--json alone re-shapes STDOUT only; no audit")

    def test_list_alone_emits_text_table_not_json(self) -> None:
        code, _out, err = self._invoke("--list-changed-files")
        self.assertEqual(code, 0, msg=f"err={err!r}")
        self.assertIsNone(_try_parse_json_array(err),
            msg="--list-changed-files alone emits text, not JSON")
        # Sanity: the text-mode audit header should be present.
        self.assertIn("changed-file audit", err)

    def test_both_flags_emit_json_array(self) -> None:
        code, _out, err = self._invoke(
            "--list-changed-files", "--json")
        self.assertEqual(code, 0, msg=f"err={err!r}")
        arr = _try_parse_json_array(err)
        self.assertIsNotNone(arr,
            msg="--list-changed-files + --json must emit "
                f"`rename_intake` JSON; stderr={err!r}")
        self.assertGreaterEqual(len(arr), 1)


# ---------------------------------------------------------------
# (2) similarity key presence — controlled by --with-similarity
# ---------------------------------------------------------------
class SimilarityKeyPresence(unittest.TestCase):
    def _invoke_json(self, *extra: str) -> list:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec, payload = _setup(tdp)
            code, _out, err = _run(
                "--root", str(spec),
                "--changed-files", str(payload),
                "--list-changed-files", "--json",
                *extra, cwd=tdp,
            )
            self.assertEqual(code, 0, msg=f"err={err!r}")
            arr = _try_parse_json_array(err)
            self.assertIsNotNone(arr,
                msg=f"expected JSON array on STDERR; got {err!r}")
            return arr

    def test_without_flag_similarity_key_is_absent_on_every_row(
            self) -> None:
        records = self._invoke_json()
        self.assertGreaterEqual(len(records), 1)
        for r in records:
            self.assertEqual(set(r), {"path", "status", "reason"},
                msg=f"legacy schema must omit `similarity`; got "
                    f"keys={sorted(r)} on record {r!r}")
            self.assertNotIn("similarity", r,
                msg="key must be absent (popped), not present "
                    "with a null value, when flag is OFF")

    def test_with_flag_similarity_key_is_present_on_every_row(
            self) -> None:
        records = self._invoke_json("--with-similarity")
        self.assertGreaterEqual(len(records), 2)
        for r in records:
            self.assertIn("similarity", r,
                msg=f"--with-similarity must add `similarity` to "
                    f"every record; missing in {r!r}")
            self.assertEqual(set(r),
                {"path", "status", "reason", "similarity"})

    def test_with_flag_value_is_object_or_null(self) -> None:
        records = self._invoke_json("--with-similarity")
        shapes = set()
        for r in records:
            sim = r["similarity"]
            if sim is None:
                shapes.add("null")
            else:
                self.assertEqual(set(sim),
                    {"kind", "score", "old_path"},
                    msg=f"similarity object schema drift: {sim!r}")
                shapes.add("object")
        # Our fixture has both an R row and a plain M row, so both
        # shapes must appear — pins that the documented "object OR
        # null" trichotomy is real, not theoretical.
        self.assertEqual(shapes, {"null", "object"},
            msg=f"expected both shapes; saw {shapes}")


# ---------------------------------------------------------------
# (3) No-op flags in JSON mode + --similarity-labels additivity
# ---------------------------------------------------------------
class NoOpAndAdditiveFlags(unittest.TestCase):
    def _invoke_json(self, *extra: str) -> tuple[list, str]:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec, payload = _setup(tdp)
            code, _out, err = _run(
                "--root", str(spec),
                "--changed-files", str(payload),
                "--list-changed-files", "--json",
                *extra, cwd=tdp,
            )
            self.assertEqual(code, 0, msg=f"err={err!r}")
            arr = _try_parse_json_array(err)
            self.assertIsNotNone(arr,
                msg=f"expected JSON array; got {err!r}")
            return arr, err

    def test_legend_flag_is_no_op_in_json_mode(self) -> None:
        # Same input, three legend modes — JSON output must be
        # byte-identical (modulo trailing whitespace).
        a, _ = self._invoke_json("--with-similarity",
            "--similarity-legend", "auto")
        b, _ = self._invoke_json("--with-similarity",
            "--similarity-legend", "on")
        c, _ = self._invoke_json("--with-similarity",
            "--similarity-legend", "off")
        self.assertEqual(a, b,
            msg="--similarity-legend must not affect JSON output")
        self.assertEqual(b, c,
            msg="--similarity-legend must not affect JSON output")

    def test_labels_only_adds_score_kind_to_non_null_similarity(
            self) -> None:
        records = self._invoke_json("--with-similarity",
            "--similarity-labels")[0]
        saw_object_with_label = False
        saw_null_without_label = False
        for r in records:
            self.assertIn("similarity", r)
            sim = r["similarity"]
            if sim is None:
                # No sub-object means no place to attach a label —
                # the record's key set must stay the legacy 4-tuple.
                self.assertEqual(set(r),
                    {"path", "status", "reason", "similarity"})
                saw_null_without_label = True
            else:
                self.assertIn("score_kind", sim,
                    msg=f"--similarity-labels must add score_kind "
                        f"to non-null similarity objects; missing "
                        f"in {sim!r}")
                self.assertIn(sim["score_kind"],
                    {"rename-similarity", "copy-similarity",
                     "unscored"},
                    msg=f"unexpected score_kind: {sim!r}")
                saw_object_with_label = True
        self.assertTrue(saw_object_with_label,
            msg="fixture must produce at least one object "
                "similarity to exercise the label injection")
        self.assertTrue(saw_null_without_label,
            msg="fixture must also produce at least one null "
                "similarity to exercise the no-injection path")

    def test_labels_off_omits_score_kind(self) -> None:
        records = self._invoke_json("--with-similarity")[0]
        for r in records:
            sim = r["similarity"]
            if isinstance(sim, dict):
                self.assertNotIn("score_kind", sim,
                    msg="score_kind must be opt-in via "
                        "--similarity-labels")


if __name__ == "__main__":
    unittest.main()