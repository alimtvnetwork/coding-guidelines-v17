"""Unit tests for ``--similarity-csv`` export.

Exercises ``_write_similarity_csv`` directly so the cases stay
hermetic (no git, no temp repo) while still covering every shape the
CLI flag will encounter in the wild:

* plain A/M/D rows (no rename → empty similarity cells)
* scored R/C rows (kind + integer score + old_path)
* unscored R/C rows (score cell stays empty, distinct from "0")
* the literal score 0 (rendered as ``"0"``, NOT empty)
* paths with commas / quotes (RFC 4180 quoting round-trips)
* writing to a real file vs writing to STDOUT (``"-"``)

The header row is asserted byte-for-byte so a future re-ordering of
the column contract trips immediately.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "check_placeholder_comments_csv",
    _HERE.parent / "check-placeholder-comments.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

_ChangedFileAudit = _MOD._ChangedFileAudit
_RenameSimilarity = _MOD._RenameSimilarity
_write_similarity_csv = _MOD._write_similarity_csv
_SIMILARITY_CSV_HEADER = _MOD._SIMILARITY_CSV_HEADER


def _read_csv(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))


def test_header_is_stable_six_columns() -> None:
    assert _SIMILARITY_CSV_HEADER == (
        "path", "status", "reason", "kind", "score", "old_path",
    )


def test_plain_row_writes_empty_similarity_cells(tmp_path: Path) -> None:
    rows = [_ChangedFileAudit(
        path="readme.md", status="matched", reason="ok",
    )]
    out = tmp_path / "audit.csv"
    _write_similarity_csv(rows, str(out))
    grid = _read_csv(out.read_text(encoding="utf-8"))
    assert grid[0] == list(_SIMILARITY_CSV_HEADER)
    # Plain row → kind/score/old_path all empty.
    assert grid[1] == ["readme.md", "matched", "ok", "", "", ""]


def test_scored_rename_writes_integer_score(tmp_path: Path) -> None:
    rows = [_ChangedFileAudit(
        path="docs/new.md", status="matched", reason="ok",
        similarity=_RenameSimilarity(
            kind="R", score=92, old_path="docs/old.md",
        ),
    )]
    out = tmp_path / "audit.csv"
    _write_similarity_csv(rows, str(out))
    grid = _read_csv(out.read_text(encoding="utf-8"))
    assert grid[1] == ["docs/new.md", "matched", "ok",
                       "R", "92", "docs/old.md"]


def test_unscored_rename_leaves_score_cell_empty(tmp_path: Path) -> None:
    """Authored payload without a percentage → ``score=None``."""
    rows = [_ChangedFileAudit(
        path="b.md", status="matched", reason="ok",
        similarity=_RenameSimilarity(
            kind="R", score=None, old_path="a.md",
        ),
    )]
    out = tmp_path / "audit.csv"
    _write_similarity_csv(rows, str(out))
    grid = _read_csv(out.read_text(encoding="utf-8"))
    # kind + old_path populated, score cell EMPTY (not "0", not "-").
    assert grid[1] == ["b.md", "matched", "ok", "R", "", "a.md"]


def test_zero_score_is_distinct_from_unscored(tmp_path: Path) -> None:
    """``score=0`` must render as ``"0"`` so spreadsheets can tell
    "git rated them dissimilar" apart from "no score recorded"."""
    rows = [
        _ChangedFileAudit(
            path="zero.md", status="matched", reason="ok",
            similarity=_RenameSimilarity(
                kind="C", score=0, old_path="src.md",
            ),
        ),
        _ChangedFileAudit(
            path="none.md", status="matched", reason="ok",
            similarity=_RenameSimilarity(
                kind="C", score=None, old_path="src.md",
            ),
        ),
    ]
    out = tmp_path / "audit.csv"
    _write_similarity_csv(rows, str(out))
    grid = _read_csv(out.read_text(encoding="utf-8"))
    assert grid[1][4] == "0"   # explicit zero
    assert grid[2][4] == ""    # unscored
    # And they're definitely not the same string.
    assert grid[1][4] != grid[2][4]


def test_paths_with_commas_and_quotes_roundtrip(tmp_path: Path) -> None:
    rows = [_ChangedFileAudit(
        path='weird, name.md', status="matched",
        reason='says "hi", with comma',
        similarity=_RenameSimilarity(
            kind="R", score=50, old_path='old, "name".md',
        ),
    )]
    out = tmp_path / "audit.csv"
    _write_similarity_csv(rows, str(out))
    # Use csv.reader (RFC 4180-aware) to confirm round-trip.
    grid = _read_csv(out.read_text(encoding="utf-8"))
    assert grid[1] == ["weird, name.md", "matched",
                       'says "hi", with comma',
                       "R", "50", 'old, "name".md']


def test_dash_target_writes_to_stdout(capsys) -> None:  # type: ignore[no-untyped-def]
    rows = [_ChangedFileAudit(
        path="a.md", status="matched", reason="ok",
    )]
    _write_similarity_csv(rows, "-")
    captured = capsys.readouterr()
    grid = _read_csv(captured.out)
    assert grid[0] == list(_SIMILARITY_CSV_HEADER)
    assert grid[1] == ["a.md", "matched", "ok", "", "", ""]


def test_empty_rows_still_writes_header(tmp_path: Path) -> None:
    out = tmp_path / "audit.csv"
    _write_similarity_csv([], str(out))
    grid = _read_csv(out.read_text(encoding="utf-8"))
    assert grid == [list(_SIMILARITY_CSV_HEADER)]


def test_mixed_batch_preserves_input_order(tmp_path: Path) -> None:
    rows = [
        _ChangedFileAudit(path="1.md", status="matched", reason="ok"),
        _ChangedFileAudit(
            path="2.md", status="matched", reason="ok",
            similarity=_RenameSimilarity(
                kind="R", score=80, old_path="0.md"),
        ),
        _ChangedFileAudit(
            path="3.md", status="ignored-deleted", reason="gone"),
    ]
    out = tmp_path / "audit.csv"
    _write_similarity_csv(rows, str(out))
    grid = _read_csv(out.read_text(encoding="utf-8"))
    assert [r[0] for r in grid[1:]] == ["1.md", "2.md", "3.md"]