#!/usr/bin/env python3
"""check-spec-cross-links.py

Verifies every internal markdown link inside spec/ resolves to an existing
file (and, when an anchor is present, to an existing heading inside that file).

Exit codes:
  0  = all links resolve
  1  = one or more broken links / missing target sections found
  2  = invocation error

Usage:
  python3 linter-scripts/check-spec-cross-links.py [--root spec] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+?)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "ftp://", "#")
SKIP_SCHEMES = ("mem://", "user-uploads://", "knowledge://")
# Same schemes may appear after a relative-path prefix like ``../mem://...``
# when authors quote a memory URI in prose. Detect those as well.
SKIP_SCHEME_SUBSTRINGS = tuple(SKIP_SCHEMES)


def slugify(text: str) -> str:
    """GitHub-flavored markdown heading slug.

    Mirrors GitHub's behavior: punctuation (including em/en dashes) is
    *removed in place* (not replaced with a space), and only whitespace
    runs collapse into ``-``. A heading like ``2.8 — No Inline``
    therefore becomes ``28--no-inline`` because the spaces *around* the
    em-dash survive as two adjacent separators.
    """
    text = text.strip().lower()
    # Strip punctuation but keep whitespace and hyphens. Punctuation
    # between two spaces leaves the spaces intact, which is what
    # produces the doubled ``--`` in GitHub's slugs.
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    # Replace each whitespace char individually (not runs) so adjacent
    # spaces — typically left over from stripped em-dashes like
    # ``A — B`` -> ``A  B`` -> ``a--b`` — survive as ``--``.
    text = re.sub(r"[ \t]", "-", text)
    return text.strip("-")


def strip_code_fences(text: str) -> str:
    """Replace fenced code blocks with blank lines so example links inside
    aren't validated. Preserves line numbers for accurate reporting.
    """
    out_lines: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        is_open = (stripped.startswith("```") or stripped.startswith("~~~")) and not in_fence
        is_close = in_fence and stripped.startswith(fence_marker)
        if is_open:
            in_fence = True
            fence_marker = "```" if stripped.startswith("```") else "~~~"
            out_lines.append("")
            continue
        if is_close:
            in_fence = False
            out_lines.append("")
            continue
        out_lines.append("" if in_fence else line)
    return "\n".join(out_lines)


# HTML comments may span multiple lines:
#
#     <!-- example placeholder, ignore:
#       - [Related module](../NN-related-module/00-overview.md)
#     -->
#
# We blank out the comment body in-place (replacing each character with a
# space, newlines preserved) so that:
#   1. links inside the comment are no longer matched by MD_LINK_RE, and
#   2. line numbers reported for *real* findings later in the file stay
#      byte-for-byte accurate.
#
# This pairs with `strip_code_fences` and gives spec authors a second,
# more natural way to mark placeholder links as scanner-exempt — no
# allowlist edit, no fenced-code wrapper, no `language-text` hint.
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_html_comments(text: str) -> str:
    """Blank out `<!-- ... -->` regions while preserving offsets.

    Replaces every non-newline character inside a comment with a space.
    Newlines are kept so downstream `text.count("\\n", 0, match.start())`
    line-number arithmetic remains correct.
    """
    def _blank(match: re.Match[str]) -> str:
        body = match.group(0)
        return "".join(ch if ch == "\n" else " " for ch in body)
    return HTML_COMMENT_RE.sub(_blank, text)


def load_allowlist(repo_root: Path) -> set[str]:
    """Load waived broken links from linter-scripts/spec-cross-links.allowlist.
    Format: one `relpath:line:target` entry per line. Lines starting with `#`
    (after optional whitespace) are comments. Anchor fragments inside entries
    are preserved.
    """
    path = repo_root / "linter-scripts" / "spec-cross-links.allowlist"
    if not path.exists():
        return set()
    out: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def collect_headings(path: Path) -> set[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()
    return {slugify(m.group(2)) for m in HEADING_RE.finditer(content)}


def is_external(target: str) -> bool:
    if target.startswith(EXTERNAL_PREFIXES) or target.startswith(SKIP_SCHEMES):
        return True
    # Relative-prefixed memory/upload URIs e.g. ``../mem://foo`` — these
    # are prose references, not real file paths.
    return any(scheme in target for scheme in SKIP_SCHEME_SUBSTRINGS)


def resolve_target(source: Path, target: str, repo_root: Path) -> Path:
    raw = target.split("#", 1)[0]
    if not raw:
        return source
    if raw.startswith("/"):
        return (repo_root / raw.lstrip("/")).resolve()
    return (source.parent / raw).resolve()


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if "26-spec-outsides" in path.parts:
            # Archived sibling-repo snapshots — links intentionally point to
            # files that live in other repositories. Skip rather than waive
            # individually.
            continue
        yield path


def check_link(source: Path, target: str, repo_root: Path) -> tuple[str, str] | None:
    if "#" in target:
        path_part, anchor = target.split("#", 1)
    else:
        path_part, anchor = target, ""
    resolved = resolve_target(source, path_part if path_part else str(source.relative_to(repo_root)), repo_root)
    if not resolved.exists():
        return ("missing-file", str(resolved))
    if not anchor:
        return None
    if resolved.is_dir():
        return ("anchor-on-directory", f"{resolved}#{anchor}")
    headings = collect_headings(resolved)
    if slugify(anchor) not in headings:
        return ("missing-section", f"{resolved}#{anchor}")
    return None


def scan(root: Path, repo_root: Path) -> list[dict]:
    failures: list[dict] = []
    allowlist = load_allowlist(repo_root)
    for md in iter_markdown_files(root):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            failures.append({"file": str(md), "kind": "read-error", "detail": str(exc)})
            continue
        scan_text = strip_code_fences(text)
        # Apply HTML-comment stripping AFTER fence stripping so an
        # `<!-- ... -->` that spans into a code fence (or vice versa)
        # still has its visible-prose links neutralised.
        scan_text = strip_html_comments(scan_text)
        for match in MD_LINK_RE.finditer(scan_text):
            target = match.group(2).strip()
            if is_external(target):
                continue
            line_num = scan_text.count("\n", 0, match.start()) + 1
            issue = check_link(md, target, repo_root)
            if issue is None:
                continue
            kind, detail = issue
            rel_file = str(md.relative_to(repo_root))
            waiver_key = f"{rel_file}:{line_num}:{target}"
            if waiver_key in allowlist:
                continue
            failures.append({
                "file": rel_file,
                "line": line_num,
                "kind": kind,
                "link_text": match.group(1),
                "target": target,
                "detail": detail,
                "waiver_key": waiver_key,
            })
    return failures


def emit_human(failures: list[dict]) -> None:
    if not failures:
        print("OK All internal spec cross-references resolve.")
        return
    print(f"FAIL {len(failures)} broken cross-reference(s) found:\n")
    for f in failures:
        loc = f"{f['file']}:{f.get('line', '?')}"
        print(f"  [{f['kind']}] {loc}")
        print(f"    text:   {f.get('link_text','')}")
        print(f"    target: {f['target']}")
        print(f"    detail: {f['detail']}\n")


def emit_github_annotations(failures: list[dict]) -> None:
    for f in failures:
        msg = f"{f['kind']}: {f['target']} ({f['detail']})"
        line = f.get("line", 1)
        print(f"::error file={f['file']},line={line}::{msg}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify spec/ internal cross-references.")
    p.add_argument("--root", default="spec", help="Spec root directory (default: spec)")
    p.add_argument("--repo-root", default=".", help="Repo root used to resolve absolute links")
    p.add_argument("--json", action="store_true", help="Emit JSON report to stdout")
    p.add_argument("--github", action="store_true", help="Emit GitHub Actions annotations")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    repo_root = Path(args.repo_root).resolve()
    if not root.exists():
        print(f"::error::spec root not found: {root}", file=sys.stderr)
        return 2
    failures = scan(root, repo_root)
    if args.json:
        print(json.dumps({"failures": failures, "count": len(failures)}, indent=2))
    else:
        emit_human(failures)
    if args.github:
        emit_github_annotations(failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
