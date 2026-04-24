"""Test-only import shim for BOOL-NEG-001.

The check lives in `checks/boolean-column-negative/sql.py`. The hyphenated
folder name is not a valid Python module identifier, so this shim loads it
via importlib.util and re-exports the scanning primitives in a form unit
tests can call directly (without going through the SARIF emitter).

Production code paths are unaffected: `run-all.sh` invokes the script
directly via `python3 checks/boolean-column-negative/sql.py ...`.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SQL_PATH = _HERE / "boolean-column-negative" / "sql.py"

_spec = importlib.util.spec_from_file_location("_bool_neg_sql", _SQL_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Cannot load BOOL-NEG-001 module from {_SQL_PATH}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def scan_text(text: str) -> list[dict[str, Any]]:
    """Scan SQL text and return a plain-dict finding list for assertions.

    Bypasses file I/O and the SARIF emitter so tests stay fast and
    framework-free.
    """
    findings: list[dict[str, Any]] = []
    for block in _mod.CREATE_TABLE_RE.finditer(text):
        body = block.group("body")
        body_offset = block.start("body")
        for match in _mod.NEG_PREFIX_RE.finditer(body):
            name = match.group(1)
            if name in _mod.ALLOWLIST:
                continue
            abs_offset = body_offset + match.start()
            line_no = text.count("\n", 0, abs_offset) + 1
            findings.append({
                "rule_id": "BOOL-NEG-001",
                "column": name,
                "line": line_no,
                "message": (
                    f"Boolean column '{name}' uses a forbidden Not/No prefix."
                ),
            })
    return findings
