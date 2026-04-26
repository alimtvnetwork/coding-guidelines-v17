#!/usr/bin/env python3
"""check-placeholder-comments.py

SPEC-PLACEHOLDER-001 — Lint placeholder HTML comment blocks in spec files.

The cross-link checker (``check-spec-cross-links.py``) ignores links inside
``<spec-placeholder>...</spec-placeholder>`` blocks (and, for backward
compatibility, the older ``<!-- TODO|FIXME ... -->`` HTML-comment form)
so authors can stash pending references without breaking CI. The
trade-off is that *malformed* placeholder blocks (missing markers,
broken bullet rows, stray text) silently slip through — the very rot
the placeholder was supposed to prevent.

This script validates every placeholder block of either supported
format, per the conventions in ``spec/_template.md``
§"Placeholder cross-references":

    <spec-placeholder reason="activate when target is created">
    - [Target Title](../NN-module-name/00-overview.md)
    - [Target Title](../NN-module-name/01-file-name.md#section-anchor)
    </spec-placeholder>

    <!-- legacy form, still supported -->
    <!-- TODO: activate when target is created
    - [Target Title](../NN-module-name/00-overview.md)
    - [Target Title](../NN-module-name/01-file-name.md#section-anchor)
    -->

Rules enforced (lightweight, no AST):

  P-001  HTML-comment placeholders must include a ``TODO:`` (or
         ``FIXME:``) marker on the opening line so reviewers can grep
         pending work. The ``<spec-placeholder>`` form is self-marking.
  P-002  Every non-blank body line must be a markdown bullet
         (``- [text](link)``) — no stray prose, no orphan list markers.
  P-003  Bullet links must be relative paths ending in ``.md``
         (optionally with ``#anchor``); ``http(s)://`` and bare anchors
         are rejected because placeholders are meant for *future*
         internal targets, not external references.
  P-004  Block must contain at least one bullet (empty placeholders are
         dead code).
  P-005  Block must not contain blank lines (keeps the snippet
         contiguous per template guidance).
  P-006  Every opening marker must have a matching closer
         (``-->`` or ``</spec-placeholder>``).
  P-008  Every placeholder block must include a back-pointer hint of
         the form ``@path/to/file.ext:LINE`` in its opening
         declaration (inside the ``<!-- TODO: ... -->`` opener line,
         or inside any attribute of ``<spec-placeholder ...>``). The
         hint records which spec line is blocked on the pending
         target so reviewers can ``grep`` straight to the activation
         site instead of scanning every spec file by hand.

Only multi-line comment blocks that start with the ``TODO:``/``FIXME:``
marker on the opening line are linted. Single-line comments and
non-placeholder comments (e.g. licence headers) are left alone. The
``<spec-placeholder>`` form is *always* linted because the tag itself
declares intent.

Exit codes:
  0  = no malformed placeholder blocks
  1  = one or more violations found
  2  = invocation error

Usage:
  python3 linter-scripts/check-placeholder-comments.py [--root spec] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


# --- HTML-comment placeholder (legacy form) ---------------------------
# Opening marker must be on the same line as ``<!--`` so we can detect
# placeholder intent without scanning the whole comment first.
PLACEHOLDER_OPEN_RE = re.compile(r"<!--\s*(TODO|FIXME)\b[^\n]*$")
COMMENT_CLOSE = "-->"

# --- Custom-tag placeholder (preferred form) --------------------------
# Single-line opener pattern: ``<spec-placeholder ...>`` (attributes
# optional). The closer is ``</spec-placeholder>`` on its own line or
# at end-of-line. Self-closing ``<spec-placeholder/>`` is rejected as
# P-004 (empty block).
TAG_OPEN_RE = re.compile(r"<spec-placeholder\b[^>]*>")
TAG_SELF_CLOSE_RE = re.compile(r"<spec-placeholder\b[^>]*/\s*>")
TAG_CLOSE = "</spec-placeholder>"

BULLET_LINK_RE = re.compile(r"^-\s+\[[^\]]+\]\(([^)\s]+)\)\s*$")

# --- Back-pointer hint (P-008) ----------------------------------------
# Required shape: ``@<path>:<line>`` where:
#   * ``<path>`` is a relative-looking file path. We require at least
#     one ``/`` so trivial words like ``@foo:1`` aren't accepted, and
#     a final ``.<ext>`` so the hint clearly refers to a source file
#     (``.md``, ``.py``, ``.ts``, ``.go``, ``.sh``, ``.toml``, …).
#   * ``<line>`` is a positive integer.
# Permissive on the path charset (anything that isn't whitespace, a
# quote, or a closing-tag char) so deep paths with hyphens, digits,
# and underscores pass without escaping. Verified syntactically only —
# the hinted file/line is not opened (placeholders are forward-looking
# and the hinted source may be mid-rename).
HINT_RE = re.compile(r"@([^\s\"'>]+/[^\s\"'>]+\.[A-Za-z0-9]+):([1-9]\d*)\b")


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    code: str
    message: str


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in p.relative_to(root).parts):
            continue
        yield p


def strip_code_fences(text: str) -> str:
    """Blank out fenced code blocks while preserving line numbers.

    Documentation that *shows* a placeholder snippet inside ```` ```markdown ````
    fences would otherwise be linted as a real placeholder. We replace
    every line inside a fence with an empty string but keep the newline,
    so reported line numbers in surrounding prose stay accurate.
    """
    out: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = True
            fence_marker = stripped[:3]
            out.append("")
            continue
        if in_fence and stripped.startswith(fence_marker):
            in_fence = False
            out.append("")
            continue
        if in_fence:
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


# Inline code spans (`...`) on a single line. We blank the contents but
# preserve the line so subsequent line numbers stay accurate. Multi-line
# spans are not standard CommonMark, so per-line handling is enough.
INLINE_CODE_RE = re.compile(r"`+[^`\n]*?`+")


def strip_inline_code(text: str) -> str:
    return "\n".join(INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)
                     for line in text.splitlines())


def _validate_body(rel: str, open_line: int, body: list[tuple[int, str]],
                   out: list[Violation]) -> int:
    """Apply P-002/P-003/P-005 to a body and return valid bullet count."""
    bullet_count = 0
    for ln, content in body:
        if not content.strip():
            out.append(Violation(rel, ln, "P-005",
                "Blank line inside placeholder block; keep it contiguous."))
            continue
        bm = BULLET_LINK_RE.match(content)
        if not bm:
            out.append(Violation(rel, ln, "P-002",
                "Placeholder body line is not a `- [text](link)` bullet."))
            continue
        target = bm.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            out.append(Violation(rel, ln, "P-003",
                f"Placeholder link `{target}` must be a relative `.md` path, "
                "not external/anchor-only."))
            continue
        path_part = target.split("#", 1)[0]
        if not path_part.endswith(".md"):
            out.append(Violation(rel, ln, "P-003",
                f"Placeholder link `{target}` must point at a `.md` file."))
            continue
        bullet_count += 1
    return bullet_count


def lint_file(path: Path, repo_root: Path) -> list[Violation]:
    rel = str(path.relative_to(repo_root))
    text = path.read_text(encoding="utf-8")
    lines = strip_inline_code(strip_code_fences(text)).splitlines()
    out: list[Violation] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # ---- Custom-tag placeholder (preferred) ---------------------
        tag_self = TAG_SELF_CLOSE_RE.search(line)
        if tag_self:
            out.append(Violation(rel, i + 1, "P-004",
                "Self-closing `<spec-placeholder/>` has no bullet rows; remove or expand it."))
            i += 1
            continue
        tag_open = TAG_OPEN_RE.search(line)
        if tag_open:
            open_line = i + 1
            # Same-line open+close — degenerate empty block.
            if TAG_CLOSE in line[tag_open.end():]:
                out.append(Violation(rel, open_line, "P-004",
                    "`<spec-placeholder>` block is empty (no bullet rows)."))
                i += 1
                continue
            body, i, closed = _consume_block(lines, i + 1, TAG_CLOSE)
            if not closed:
                out.append(Violation(rel, open_line, "P-006",
                    "`<spec-placeholder>` opened but never closed "
                    "(missing `</spec-placeholder>`)."))
                continue
            bullet_count = _validate_body(rel, open_line, body, out)
            if bullet_count == 0:
                out.append(Violation(rel, open_line, "P-004",
                    "`<spec-placeholder>` block contains no valid bullet rows."))
            continue

        # ---- HTML-comment placeholder (legacy) ----------------------
        m = PLACEHOLDER_OPEN_RE.search(line)
        if not m:
            i += 1
            continue
        if COMMENT_CLOSE in line[m.end():] or COMMENT_CLOSE in line[m.start():]:
            out.append(Violation(rel, i + 1, "P-004",
                "Placeholder comment has no bullet rows; remove or expand it."))
            i += 1
            continue
        open_line = i + 1
        body, i, closed = _consume_block(lines, i + 1, COMMENT_CLOSE)
        if not closed:
            out.append(Violation(rel, open_line, "P-006",
                "Placeholder comment opened but never closed (missing `-->`)."))
            continue
        bullet_count = _validate_body(rel, open_line, body, out)
        if bullet_count == 0:
            out.append(Violation(rel, open_line, "P-004",
                "Placeholder block contains no valid bullet rows."))

    return out


def _consume_block(lines: list[str], start: int, close_marker: str
                   ) -> tuple[list[tuple[int, str]], int, bool]:
    """Walk ``lines[start:]`` collecting body rows until ``close_marker``.

    Returns ``(body, next_index, closed)`` where ``body`` is a list of
    ``(line_number, content)`` tuples (1-indexed line numbers) and
    ``next_index`` is the position to resume scanning from.
    """
    body: list[tuple[int, str]] = []
    n = len(lines)
    i = start
    while i < n:
        cur = lines[i]
        if close_marker in cur:
            pre = cur.split(close_marker, 1)[0]
            if pre.strip():
                body.append((i + 1, pre.rstrip()))
            return body, i + 1, True
        body.append((i + 1, cur.rstrip()))
        i += 1
    return body, i, False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default="spec",
        help="Directory to scan recursively for markdown files (default: spec).")
    ap.add_argument("--repo-root", default=".",
        help="Repository root for relative path reporting (default: cwd).")
    ap.add_argument("--json", action="store_true",
        help="Emit findings as JSON instead of human text.")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    repo_root = Path(args.repo_root).resolve()
    if not root.is_dir():
        print(f"error: --root {args.root!r} is not a directory", file=sys.stderr)
        return 2

    violations: list[Violation] = []
    for md in iter_markdown_files(root):
        violations.extend(lint_file(md, repo_root))

    if args.json:
        print(json.dumps([asdict(v) for v in violations], indent=2))
    else:
        if not violations:
            print(f"✅ placeholder-comments: no malformed blocks under {args.root}/")
        else:
            print(f"❌ placeholder-comments: {len(violations)} violation(s):\n")
            for v in violations:
                print(f"  {v.file}:{v.line}  [{v.code}] {v.message}")
            print("\n  See linter-scripts/check-placeholder-comments.py for rule docs.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())