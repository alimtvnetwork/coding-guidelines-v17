#!/usr/bin/env python3
"""BOOL-NEG-001 (Go) — Forbid Not/No-prefixed boolean DB column names in Go.

Two complementary scanners run over every ``.go`` file:

1. **Struct-tag scanner** — walks ``type X struct { ... }`` blocks and
   inspects ``bool`` fields for forbidden column names declared via
   ``db:"..."`` (sqlx, jmoiron) or ``gorm:"column:..."`` tags. The
   *struct field name* is also checked because it usually round-trips
   to a column when no explicit tag is set (GORM default mapping).

2. **Embedded-SQL scanner** — locates raw string literals
   (back-tick-delimited) that contain ``CREATE TABLE`` and runs the
   exact same regex/allow-list logic as ``sql.py`` over them. Covers
   ``embed.FS``-style migration constants and inline DDL.

Allow-list and forbidden-prefix regex are kept in lock-step with
``sql.py`` so the two scanners can never drift on what counts as a
violation. Snake-case column names like ``is_not_active`` are
normalized to PascalCase before matching so both naming styles are
caught.

Spec:
- spec/04-database-conventions/01-naming-conventions.md  Rules 2 & 9
- linters-cicd/checks/boolean-column-negative/sql.py     (lock-step)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib.cli import build_parser
from _lib.sarif import Finding, Rule, SarifRun, emit
from _lib.walker import relpath, walk_files


RULE = Rule(
    id="BOOL-NEG-001",
    name="BooleanColumnNegativePrefix",
    short_description=(
        "Database boolean columns must not use Not/No prefixes "
        "(e.g. IsNotActive, HasNoLicense). Detected in Go via "
        "db:\"...\" / gorm:\"column:...\" struct tags and inside "
        "embedded SQL string literals."
    ),
    help_uri_relative="../04-database-conventions/01-naming-conventions.md",
)

EXTENSIONS = [".go"]

# Match Is/Has + Not/No + UpperCamel — same regex as sql.py.
NEG_PREFIX_RE = re.compile(r"\b((?:Is|Has)(?:Not|No)[A-Z][A-Za-z0-9]*)\b")

# Allow-list — must match sql.py exactly. Single source of truth lives
# in the spec; duplicated here only because the two scanners run as
# standalone scripts (no shared state at runtime).
ALLOWLIST = {
    "IsDisabled", "IsInvalid", "IsIncomplete", "IsUnavailable",
    "IsUnread", "IsHidden", "IsBroken", "IsLocked",
    "IsUnpublished", "IsUnverified",
}

# `type Name struct { ... }` — non-greedy so adjacent structs don't merge.
STRUCT_BLOCK_RE = re.compile(
    r"type\s+(?P<name>[A-Z][A-Za-z0-9_]*)\s+struct\s*\{(?P<body>.*?)\}",
    re.DOTALL,
)

# Field line: `FieldName bool [optional ...] `tag:"..."``
# Captures field name, whether it's bool, and the raw backtick tag block.
FIELD_LINE_RE = re.compile(
    r"^\s*(?P<field>[A-Z][A-Za-z0-9_]*)\s+(?P<type>\*?\b\w+\b)"
    r"[^`\n]*(?:`(?P<tag>[^`]*)`)?\s*$",
    re.MULTILINE,
)

# Tag pickers — db:"col" (sqlx) and gorm:"column:col;..." (gorm).
DB_TAG_RE = re.compile(r'\bdb:"([^"]+)"')
GORM_COLUMN_RE = re.compile(r'\bgorm:"[^"]*\bcolumn:([A-Za-z0-9_]+)')

# Back-tick raw string literals containing CREATE TABLE — embedded SQL.
RAW_STRING_RE = re.compile(r"`([^`]*\bCREATE\s+TABLE\b[^`]*)`", re.IGNORECASE)
SQL_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE[^\(]*\((?P<body>.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)


def snake_to_pascal(snake: str) -> str:
    """``is_not_active`` → ``IsNotActive``. Idempotent for PascalCase input."""
    if "_" not in snake:
        return snake[:1].upper() + snake[1:] if snake else snake
    return "".join(part[:1].upper() + part[1:] for part in snake.split("_") if part)


def is_violation(name: str) -> bool:
    """True iff *name* matches the forbidden regex and is not allow-listed."""
    pascal = snake_to_pascal(name)
    if pascal in ALLOWLIST:
        return False
    return NEG_PREFIX_RE.search(pascal) is not None


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_struct_tags(text: str) -> list[tuple[str, int, str]]:
    """Return (column_name, line_number, source_kind) for each violation."""
    out: list[tuple[str, int, str]] = []
    for block in STRUCT_BLOCK_RE.finditer(text):
        body = block.group("body")
        body_offset = block.start("body")
        for field in FIELD_LINE_RE.finditer(body):
            if field.group("type") not in ("bool", "*bool"):
                continue
            tag = field.group("tag") or ""
            field_name = field.group("field")
            abs_line = line_of(text, body_offset + field.start())

            # Pick the column name in priority: gorm column → db tag → field name.
            col = None
            kind = "struct-field"
            gorm_match = GORM_COLUMN_RE.search(tag)
            db_match = DB_TAG_RE.search(tag)
            if gorm_match:
                col, kind = gorm_match.group(1), "gorm-tag"
            elif db_match:
                col, kind = db_match.group(1), "db-tag"
            else:
                col = field_name

            if col and is_violation(col):
                out.append((snake_to_pascal(col), abs_line, kind))
    return out


def scan_embedded_sql(text: str) -> list[tuple[str, int, str]]:
    """Scan back-tick raw strings that hold ``CREATE TABLE`` blocks."""
    out: list[tuple[str, int, str]] = []
    for raw in RAW_STRING_RE.finditer(text):
        sql = raw.group(1)
        sql_offset = raw.start(1)
        for table in SQL_CREATE_TABLE_RE.finditer(sql):
            body = table.group("body")
            body_offset_in_sql = table.start("body")
            for match in NEG_PREFIX_RE.finditer(body):
                name = match.group(1)
                if name in ALLOWLIST:
                    continue
                abs_line = line_of(text, sql_offset + body_offset_in_sql + match.start())
                out.append((name, abs_line, "embedded-sql"))
    return out


def scan(path: Path, root: str) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[Finding] = []
    for name, line, kind in scan_struct_tags(text) + scan_embedded_sql(text):
        findings.append(
            Finding(
                rule_id=RULE.id,
                level="error",
                message=(
                    f"Boolean column '{name}' uses a forbidden Not/No prefix "
                    f"({kind}). Rename to the positive form (e.g. IsActive, "
                    "HasLicense) and derive the inverse as a computed field "
                    "in code. See Rule 2 + Rule 9 in "
                    "04-database-conventions/01-naming-conventions.md."
                ),
                file_path=relpath(path, root),
                start_line=line,
            )
        )
    return findings


def main() -> int:
    args = build_parser("BOOL-NEG-001 boolean-column-negative (go)").parse_args()
    run = SarifRun(
        tool_name="coding-guidelines-boolean-column-negative-go",
        tool_version="1.0.0",
        rules=[RULE],
    )
    for f in walk_files(args.path, EXTENSIONS):
        for finding in scan(f, args.path):
            run.add(finding)
    return emit(run, args.format, args.output)


if __name__ == "__main__":
    sys.exit(main())
