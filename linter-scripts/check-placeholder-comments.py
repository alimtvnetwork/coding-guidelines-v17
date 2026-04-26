#!/usr/bin/env python3
"""check-placeholder-comments.py

SPEC-PLACEHOLDER-001 — Lint placeholder HTML comment blocks in spec files.

The cross-link checker (``check-spec-cross-links.py``) ignores links inside
``<!-- ... -->`` comments so that authors can stash pending references
without breaking CI. The trade-off is that *malformed* placeholder blocks
(missing markers, broken bullet rows, stray text) silently slip through —
the very rot the comment was supposed to prevent.

This script validates every placeholder block matching the convention
documented in ``spec/_template.md`` §"Placeholder cross-references":

    <!-- TODO: activate when target is created
    - [Target Title](../NN-module-name/00-overview.md)
    - [Target Title](../NN-module-name/01-file-name.md#section-anchor)
    -->

Rules enforced (lightweight, no AST):

  P-001  Opening ``<!--`` line must include a ``TODO:`` (or ``FIXME:``)
         marker so reviewers can grep pending work.
  P-002  Every non-blank body line must be a markdown bullet
         (``- [text](link)``) — no stray prose, no orphan list markers.
  P-003  Bullet links must be relative paths ending in ``.md``
         (optionally with ``#anchor``); ``http(s)://`` and bare anchors
         are rejected because the comment is meant for *future* internal
         targets, not external references.
  P-004  Block must contain at least one bullet (empty placeholders are
         dead code).
  P-005  Block must not contain blank lines (keeps the snippet contiguous
         per template guidance).

Only multi-line comment blocks that start with the ``TODO:``/``FIXME:``
marker on the opening line are linted. Single-line comments and
non-placeholder comments (e.g. licence headers) are left alone.

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


# Opening marker must be on the same line as ``<!--`` so we can detect
# placeholder intent without scanning the whole comment first.
PLACEHOLDER_OPEN_RE = re.compile(r"<!--\s*(TODO|FIXME)\b[^\n]*$")
BULLET_LINK_RE = re.compile(r"^-\s+\[[^\]]+\]\(([^)\s]+)\)\s*$")
CLOSE_MARKER = "-->"


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


def lint_file(path: Path, repo_root: Path) -> list[Violation]:
    rel = str(path.relative_to(repo_root))
    text = path.read_text(encoding="utf-8")
    lines = strip_inline_code(strip_code_fences(text)).splitlines()
    out: list[Violation] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = PLACEHOLDER_OPEN_RE.search(line)
        if not m:
            i += 1
            continue

        # Single-line ``<!-- TODO ... -->`` — opening + closing on same line.
        # Strip the opener text we already matched and look past it.
        if CLOSE_MARKER in line[m.end():] or CLOSE_MARKER in line[m.start():]:
            # Same-line placeholder is degenerate (no bullets possible).
            out.append(Violation(rel, i + 1, "P-004",
                "Placeholder comment has no bullet rows; remove or expand it."))
            i += 1
            continue

        open_line = i + 1
        body: list[tuple[int, str]] = []
        i += 1
        closed = False
        while i < n:
            cur = lines[i]
            if CLOSE_MARKER in cur:
                # Anything before --> on the close line is body.
                pre = cur.split(CLOSE_MARKER, 1)[0]
                if pre.strip():
                    body.append((i + 1, pre.rstrip()))
                closed = True
                i += 1
                break
            body.append((i + 1, cur.rstrip()))
            i += 1

        if not closed:
            out.append(Violation(rel, open_line, "P-006",
                "Placeholder comment opened but never closed (missing `-->`)."))
            continue

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
            # Strip anchor for extension check.
            path_part = target.split("#", 1)[0]
            if not path_part.endswith(".md"):
                out.append(Violation(rel, ln, "P-003",
                    f"Placeholder link `{target}` must point at a `.md` file."))
                continue
            bullet_count += 1

        if bullet_count == 0:
            out.append(Violation(rel, open_line, "P-004",
                "Placeholder block contains no valid bullet rows."))

    return out


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