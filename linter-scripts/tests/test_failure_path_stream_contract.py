"""Pin the failure-path stream contract documented in
``README-rename-intake.md`` under *"Stream behaviour under failure /
exception paths"*.

The contract guarantees that on every documented failure mode:

* STDOUT is **empty** (0 bytes) — no partial JSON, no `[]`, no
  human summary;
* STDERR carries a **single human-readable** ``error: …`` line —
  not a JSON document, so a CI consumer that strict-parses STDERR
  as JSON gets a ``JSONDecodeError`` (telling them "no audit was
  produced") rather than a misleading "zero records" reading;
* the exit code is **2**, never 0 or 1.

It also pins the recoverable cases (malformed payload row → audit
entry, not failure) so a future refactor doesn't accidentally turn
a soft-recover into a hard-fail and silently change the contract.
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


def _run(*args: str, cwd: Path | None = None
         ) -> tuple[int, str, str]:
    r = subprocess.run([sys.executable, str(LINTER), *args],
                       capture_output=True, text=True,
                       cwd=cwd)
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------
# Hard-fail paths: STDOUT must be empty, STDERR is plain text
# ---------------------------------------------------------------
class HardFailureStreamContract(unittest.TestCase):
    """Each failure documented in the README must yield exit 2,
    empty STDOUT, and a non-JSON STDERR error line."""

    def _assert_hard_fail(self, code: int, out: str, err: str,
                          *, expect_in_err: str) -> None:
        # Exit code: documented as 2 for every CLI / git-resolution
        # failure (vs 0 = clean, 1 = violations, traceback = bug).
        self.assertEqual(code, 2,
            msg=f"expected exit 2; got {code}; err={err!r}")
        # STDOUT is fully empty — not even a trailing newline.
        self.assertEqual(out, "",
            msg=f"STDOUT must be empty on hard failure; got "
                f"{out!r}")
        # STDERR carries the human error line, prefixed with
        # ``error:`` so a log scraper can spot it.
        self.assertIn("error:", err,
            msg=f"STDERR missing `error:` prefix; got {err!r}")
        self.assertIn(expect_in_err, err,
            msg=f"STDERR missing expected fragment "
                f"{expect_in_err!r}; got {err!r}")
        # Critically: STDERR must NOT be a JSON document. A CI
        # consumer doing ``json.loads(stderr)`` should fail loudly,
        # not silently parse "[]" as "zero records".
        with self.assertRaises(json.JSONDecodeError,
            msg="STDERR on failure must not be parseable as JSON; "
                "that would mask 'linter crashed' as 'zero rows'"):
            json.loads(err)

    def test_bad_root_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, out, err = _run(
                "--root", "definitely-not-a-real-dir",
                "--diff-base", "HEAD",
                "--list-changed-files", "--json",
                cwd=Path(td))
            self._assert_hard_fail(code, out, err,
                expect_in_err="--root")

    def test_diff_base_with_changed_files_is_mutually_exclusive(
            self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "spec").mkdir()
            payload = tdp / "c.txt"
            payload.write_text("M\tspec/x.md\n")
            code, out, err = _run(
                "--root", str(tdp / "spec"),
                "--diff-base", "HEAD",
                "--changed-files", str(payload),
                "--list-changed-files", "--json",
                cwd=tdp)
            self._assert_hard_fail(code, out, err,
                expect_in_err="mutually exclusive")

    def test_negative_diff_context_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "spec").mkdir()
            payload = tdp / "c.txt"
            payload.write_text("M\tspec/x.md\n")
            code, out, err = _run(
                "--root", str(tdp / "spec"),
                "--changed-files", str(payload),
                "--diff-context", "-1",
                "--list-changed-files", "--json",
                cwd=tdp)
            self._assert_hard_fail(code, out, err,
                expect_in_err="--diff-context")

    def test_unknown_diff_base_ref_fails_cleanly(self) -> None:
        # Run inside a real git worktree (the project's own) so
        # ``git diff`` is invoked and emits a meaningful error
        # rather than failing for missing-binary reasons.
        repo = Path(__file__).resolve().parents[2]
        if not (repo / ".git").exists():
            self.skipTest("not running inside a git worktree; "
                          "git diff resolution can't be exercised")
        code, out, err = _run(
            "--root", str(repo / "linter-scripts"),
            "--diff-base", "totally-bogus-ref-xyz-9999",
            "--list-changed-files", "--with-similarity", "--json",
            cwd=repo)
        self._assert_hard_fail(code, out, err,
            expect_in_err="git diff vs.")


# ---------------------------------------------------------------
# Soft-recover paths: malformed inputs become audit rows, not fails
# ---------------------------------------------------------------
class SoftRecoverPathStreamContract(unittest.TestCase):
    """Inputs that are *not* documented as failures must not flip
    the contract: they produce a normal STDOUT + STDERR pair, and
    STDERR remains a parseable JSON array under ``--json``."""

    def test_malformed_changed_files_row_becomes_audit_entry(
            self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec = tdp / "spec"; spec.mkdir()
            payload = tdp / "bad.txt"
            # A row whose post-state path has no allowed extension —
            # the renderer must classify it as ignored-extension,
            # NOT abort with exit 2.
            payload.write_text("GARBAGE\tno-tab\n")
            code, out, err = _run(
                "--root", str(spec),
                "--changed-files", str(payload),
                "--list-changed-files", "--with-similarity", "--json",
                cwd=tdp)
            # Soft path: exit 0 (no violations, no failure).
            self.assertEqual(code, 0,
                msg=f"malformed row must NOT hard-fail; got "
                    f"exit={code}, err={err!r}")
            # STDOUT is the empty violations array (legacy schema).
            self.assertEqual(out.strip(), "[]",
                msg=f"STDOUT must be the empty violations doc; "
                    f"got {out!r}")
            # STDERR is parseable JSON — the audit array — and
            # contains the bad row classified as ignored-extension.
            audit = json.loads(err)
            self.assertIsInstance(audit, list)
            statuses = {r["status"] for r in audit}
            self.assertIn("ignored-extension", statuses,
                msg=f"bad row should land as ignored-extension; "
                    f"audit={audit!r}")

    def test_zero_changed_files_is_not_a_failure(self) -> None:
        # An empty --changed-files payload is a documented happy-
        # path (fast PASS), not a failure. STDOUT must carry the
        # empty violations array, STDERR must carry a (possibly
        # empty) JSON audit array.
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            spec = tdp / "spec"; spec.mkdir()
            payload = tdp / "empty.txt"
            payload.write_text("")
            code, out, err = _run(
                "--root", str(spec),
                "--changed-files", str(payload),
                "--list-changed-files", "--with-similarity", "--json",
                cwd=tdp)
            self.assertEqual(code, 0,
                msg=f"empty changed-files is happy-path; got "
                    f"exit={code}, err={err!r}")
            self.assertEqual(out.strip(), "[]")
            # STDERR may legitimately be an empty array — pin that
            # it stays parseable JSON and not an error line.
            parsed = json.loads(err)
            self.assertIsInstance(parsed, list,
                msg=f"STDERR must be a JSON array on happy path; "
                    f"got {err!r}")


# ---------------------------------------------------------------
# Disjointness invariant: failure error never leaks onto STDOUT
# ---------------------------------------------------------------
class StreamDisjointnessUnderFailure(unittest.TestCase):
    """Cross-cutting check: across every documented failure shape,
    the ``error:`` token must appear on STDERR and never on STDOUT.
    Pins the "no interleaving" contract from the README."""

    def test_error_token_never_appears_on_stdout(self) -> None:
        cases = [
            (["--root", "nope-not-a-dir",
              "--diff-base", "HEAD",
              "--list-changed-files", "--json"],
             "bad --root"),
            (["--diff-context", "-5",
              "--root", ".",
              "--list-changed-files", "--json"],
             "negative diff-context"),
        ]
        with tempfile.TemporaryDirectory() as td:
            for argv, label in cases:
                with self.subTest(case=label):
                    code, out, err = _run(*argv, cwd=Path(td))
                    self.assertEqual(code, 2,
                        msg=f"[{label}] expected exit 2; "
                            f"got {code}; err={err!r}")
                    self.assertNotIn("error:", out,
                        msg=f"[{label}] error text leaked onto "
                            f"STDOUT: {out!r}")
                    self.assertEqual(out, "",
                        msg=f"[{label}] STDOUT must be empty on "
                            f"hard failure; got {out!r}")
                    self.assertIn("error:", err,
                        msg=f"[{label}] STDERR missing error: "
                            f"prefix; got {err!r}")


if __name__ == "__main__":
    unittest.main()
