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

  P-001  Placeholder *intent text* must be a complete imperative
         sentence so reviewers see actionable language. Specifically:

           * Wording follows the marker (``TODO:`` / ``FIXME:`` for
             legacy comments, ``reason="…"`` for ``<spec-placeholder>``).
           * It must be non-empty and start with a recognised
             imperative verb (``activate``, ``add``, ``link``,
             ``replace``, ``wire``, ``update``, ``write``, ``create``,
             ``document``, ``cross-reference``). Extend the allowlist
             via ``--allow-verb <verb>`` (repeatable).
           * It must end with a period — half-sentences like
             ``activate later`` are rejected; ``Activate when target is
             created.`` passes.

         The verb is matched case-insensitively. Articles/auxiliaries
         like ``please`` are stripped before the check so
         ``please add the link.`` passes.
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
  P-007  Two or more placeholder bullets must not point at the same
         target ``.md`` file (anchor ignored — duplicates pointing at
         different sections of the same file still collapse to one
         pending activation). Detected within a file and across files.

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
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


# --- HTML-comment placeholder (legacy form) ---------------------------
# Opening marker must be on the same line as ``<!--`` so we can detect
# placeholder intent without scanning the whole comment first.
PLACEHOLDER_OPEN_RE = re.compile(r"<!--\s*(TODO|FIXME)\b[^\n]*$")
# Capture the wording that follows the marker so P-001 can lint it.
PLACEHOLDER_INTENT_RE = re.compile(
    r"<!--\s*(?P<marker>TODO|FIXME)\s*:?\s*(?P<text>[^\n]*?)\s*$"
)
COMMENT_CLOSE = "-->"

# --- Custom-tag placeholder (preferred form) --------------------------
# Single-line opener pattern: ``<spec-placeholder ...>`` (attributes
# optional). The closer is ``</spec-placeholder>`` on its own line or
# at end-of-line. Self-closing ``<spec-placeholder/>`` is rejected as
# P-004 (empty block).
TAG_OPEN_RE = re.compile(r"<spec-placeholder\b[^>]*>")
TAG_SELF_CLOSE_RE = re.compile(r"<spec-placeholder\b[^>]*/\s*>")
TAG_CLOSE = "</spec-placeholder>"
# Capture the ``reason="…"`` attribute on the opening tag (single or
# double quotes). Absent reason → P-001 with a "missing reason" hint.
TAG_REASON_RE = re.compile(
    r"<spec-placeholder\b[^>]*?\breason\s*=\s*(?P<q>[\"'])(?P<text>.*?)(?P=q)",
    re.IGNORECASE,
)

# Curated set of imperative verbs that signal actionable intent. Kept
# deliberately small — authors who want a different verb can extend
# the set via ``--allow-verb`` rather than the linter silently accepting
# any leading word. All entries are lowercase; matching is
# case-insensitive.
DEFAULT_INTENT_VERBS: frozenset[str] = frozenset({
    "activate",
    "add",
    "link",
    "replace",
    "wire",
    "update",
    "write",
    "create",
    "document",
    "cross-reference",
})

# Soft prefixes that authors may stack before the imperative verb
# without the wording becoming non-actionable. Stripped (case-
# insensitively) before the verb-match check.
INTENT_PREFIXES: tuple[str, ...] = ("please ",)

BULLET_LINK_RE = re.compile(r"^-\s+\[[^\]]+\]\(([^)\s]+)\)\s*$")


# --- Suggested-patch fix hints ----------------------------------------
# Per-rule one-line replacement scaffold inserted into the suggested
# `git apply` patch in place of the offending post-state line. The
# linter cannot infer the author's correct fix — these are TODO
# markers labelled with the rule code so a reviewer doing a copy-
# paste apply immediately sees what kind of edit is required.
#
# Rules NOT in this table (e.g. the structural P-006 "missing closer"
# where the violation line is the *opener*, not a wrong line in
# place) fall back to ``_RULE_FIX_FALLBACK``. Adding a more specific
# hint later is purely additive and does not break the schema.
_RULE_FIX_HINTS: dict[str, str] = {
    "P-001": '<!-- TODO(P-001): replace with a complete imperative '
             'reason="…" (e.g. reason="Document RAG eviction policy"). -->',
    "P-002": "- [TODO(P-002): describe target](relative/path/to/spec.md)",
    "P-003": "- [TODO(P-003): use a relative .md path](relative/path/to/spec.md)",
    "P-004": "- [TODO(P-004): add at least one bullet](relative/path/to/spec.md)",
    "P-005": "<!-- TODO(P-005): remove the blank line above; "
             "placeholder bodies must be contiguous. -->",
    "P-006": "<!-- TODO(P-006): add a matching closing marker "
             "(--> or </spec-placeholder>) below this opener. -->",
    "P-007": "- [TODO(P-007): point at a different target — "
             "duplicate of an earlier placeholder](relative/path/to/different-spec.md)",
    "P-008": "<!-- TODO(P-008): see linter rule docs for the exact fix. -->",
}
_RULE_FIX_FALLBACK = (
    "<!-- TODO: see linter-scripts/check-placeholder-comments.py "
    "for the rule's required fix. -->"
)


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    code: str
    message: str


# Default extension allowlist for spec discovery. Kept as a tuple so
# the value is hashable + cache-segment-friendly. Extending this set
# at runtime is exposed via ``--extension`` (repeatable) and feeds
# both the file iterator and the cache-segment naming below.
DEFAULT_EXTENSIONS: tuple[str, ...] = ("md",)


def iter_markdown_files(
    root: Path,
    *,
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS,
) -> Iterable[Path]:
    """Yield every file under ``root`` matching one of ``extensions``,
    sorted by path with hidden directories (``.foo/``) excluded.

    ``extensions`` is a tuple of bare extension strings without the
    leading dot (e.g. ``("md", "mdx")``). The function unions the
    per-extension globs into a single sorted, deduplicated stream so
    a future ``--extension md --extension mdx`` run can't yield the
    same path twice (e.g. on a case-insensitive filesystem).
    """
    seen: set[Path] = set()
    candidates: list[Path] = []
    for ext in extensions:
        for p in root.rglob(f"*.{ext}"):
            if p in seen:
                continue
            seen.add(p)
            candidates.append(p)
    for p in sorted(candidates):
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


def _validate_intent(rel: str, line_no: int, marker: str, text: str,
                     out: list[Violation], verbs: frozenset[str]) -> None:
    """Apply P-001 to a placeholder's intent text.

    ``marker`` is shown verbatim in the message ("TODO:", "FIXME:",
    or "reason"). ``text`` is the wording that follows it (already
    stripped of surrounding whitespace). ``verbs`` is the active
    imperative-verb allowlist for this run.
    """
    if not text:
        out.append(Violation(rel, line_no, "P-001",
            f"Placeholder `{marker}` is empty — describe the pending action "
            "(e.g. `Activate when target is created.`)."))
        return

    # Strip soft prefixes (e.g. "please ") so they don't shadow the verb.
    lowered = text.lower()
    for prefix in INTENT_PREFIXES:
        if lowered.startswith(prefix):
            text = text[len(prefix):]
            lowered = text.lower()
            break

    if not text:
        out.append(Violation(rel, line_no, "P-001",
            f"Placeholder `{marker}` has no actionable wording after `please`."))
        return

    # Extract the leading word (or hyphenated compound like
    # ``cross-reference``). Compare case-insensitively.
    head_match = re.match(r"[A-Za-z][A-Za-z-]*", text)
    head = head_match.group(0).lower() if head_match else ""
    if head not in verbs:
        sample = ", ".join(sorted(list(verbs))[:6])
        out.append(Violation(rel, line_no, "P-001",
            f"Placeholder `{marker}` must start with an imperative verb "
            f"(got `{head or text[:20]}`). Allowed verbs include: {sample}…. "
            "Extend with `--allow-verb <verb>` if needed."))
        return

    if not text.rstrip().endswith("."):
        out.append(Violation(rel, line_no, "P-001",
            f"Placeholder `{marker}` wording must end with a period "
            f"(got `{text.rstrip()[-30:]}`)."))
        return


def _validate_body(rel: str, open_line: int, body: list[tuple[int, str]],
                   out: list[Violation],
                   bullets: list[tuple[int, str]] | None = None) -> int:
    """Apply P-002/P-003/P-005 to a body and return valid bullet count.

    When ``bullets`` is provided, every valid bullet is appended as
    ``(line, target)`` for later cross-block duplicate analysis (P-007).
    """
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
        if bullets is not None:
            bullets.append((ln, target))
    return bullet_count


def lint_file(path: Path, repo_root: Path,
              valid_bullets: list[tuple[str, int, str]] | None = None,
              intent_verbs: frozenset[str] = DEFAULT_INTENT_VERBS,
              ) -> list[Violation]:
    """Lint one markdown file.

    When ``valid_bullets`` is provided, every successfully-validated
    bullet is appended as ``(rel_file, line, target)`` so the caller
    can run cross-file duplicate detection (P-007).

    ``intent_verbs`` controls the imperative-verb allowlist for P-001;
    defaults to ``DEFAULT_INTENT_VERBS`` and can be widened from the
    CLI via ``--allow-verb``.
    """
    rel = str(path.relative_to(repo_root))
    text = path.read_text(encoding="utf-8")
    lines = strip_inline_code(strip_code_fences(text)).splitlines()
    out: list[Violation] = []
    file_bullets: list[tuple[int, str]] = []

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
            # P-001: validate `reason="…"` wording. A missing attribute
            # is itself a P-001 ("placeholder has no documented intent").
            reason_match = TAG_REASON_RE.search(line)
            reason_text = reason_match.group("text").strip() if reason_match else ""
            if not reason_match:
                out.append(Violation(rel, open_line, "P-001",
                    "`<spec-placeholder>` is missing a `reason=\"…\"` attribute "
                    "describing why the link is pending."))
            else:
                _validate_intent(rel, open_line, "reason", reason_text, out, intent_verbs)
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
            bullet_count = _validate_body(rel, open_line, body, out, file_bullets)
            if bullet_count == 0:
                out.append(Violation(rel, open_line, "P-004",
                    "`<spec-placeholder>` block contains no valid bullet rows."))
            continue

        # ---- HTML-comment placeholder (legacy) ----------------------
        m = PLACEHOLDER_OPEN_RE.search(line)
        if not m:
            i += 1
            continue
        # P-001: lint the wording that follows the marker.
        intent_match = PLACEHOLDER_INTENT_RE.search(line)
        if intent_match:
            marker = intent_match.group("marker") + ":"
            intent_text = intent_match.group("text").strip()
            # Trim a trailing ``-->`` if the open + close share a line —
            # P-004 below will catch the structural problem; here we
            # just need clean intent text.
            if intent_text.endswith(COMMENT_CLOSE):
                intent_text = intent_text[: -len(COMMENT_CLOSE)].rstrip()
            _validate_intent(rel, i + 1, marker, intent_text, out, intent_verbs)
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
        bullet_count = _validate_body(rel, open_line, body, out, file_bullets)
        if bullet_count == 0:
            out.append(Violation(rel, open_line, "P-004",
                "Placeholder block contains no valid bullet rows."))

    # ---- P-007 within-file duplicates ------------------------------
    # Resolve each bullet to a canonical (file, target_path) key. We
    # strip the anchor because two placeholders pointing at different
    # sections of the same target file still collapse to a single
    # activation step, which is what P-007 is designed to surface.
    seen: dict[str, tuple[int, str]] = {}
    for ln, target in file_bullets:
        key = _canonical_target(rel, target, repo_root)
        if key in seen:
            first_ln, first_target = seen[key]
            out.append(Violation(rel, ln, "P-007",
                f"Duplicate placeholder target `{target}` — already "
                f"declared at L{first_ln} as `{first_target}` "
                "(anchor differences are ignored)."))
        else:
            seen[key] = (ln, target)

    if valid_bullets is not None:
        for ln, target in file_bullets:
            valid_bullets.append((rel, ln, target))

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


def _canonical_target(source_rel: str, target: str, repo_root: Path) -> str:
    """Resolve a placeholder bullet's link to a canonical repo-relative
    path string. Anchor is stripped so different anchors on the same
    target file collapse to the same key. Path resolution is purely
    syntactic (no I/O) — the target file may not exist yet, which is
    the whole point of placeholders.
    """
    path_part = target.split("#", 1)[0]
    source_dir = (repo_root / source_rel).parent
    try:
        resolved = (source_dir / path_part).resolve()
        return str(resolved.relative_to(repo_root.resolve()))
    except (ValueError, OSError):
        # Fall back to the literal path if it escapes the repo root —
        # still gives consistent grouping for duplicate detection.
        return path_part


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default="spec",
        help="Directory to scan recursively for markdown files (default: spec).")
    ap.add_argument("--repo-root", default=".",
        help="Repository root for relative path reporting (default: cwd).")
    ap.add_argument("--json", action="store_true",
        help="Emit findings as JSON instead of human text.")
    ap.add_argument("--allow-verb", action="append", default=[],
        metavar="VERB",
        help="Add an extra imperative verb to the P-001 allowlist "
             "(repeatable). Use lowercase, hyphens allowed.")
    ap.add_argument("--extension", action="append", default=None,
        metavar="EXT",
        help="Restrict spec discovery to files with this extension "
             "(repeatable, no leading dot, case-sensitive). Default "
             "is `md`. Each unique sorted allowlist gets its own "
             "physical cache subdirectory under --cache-dir (e.g. "
             "`<cache-dir>/ext-md/`, `<cache-dir>/ext-md+mdx/`) so "
             "switching the allowlist never reads a sentinel written "
             "for a different file set — even if a future bug made "
             "the content hash collide. Side benefit: `rm -rf "
             "<cache-dir>/ext-mdx/` nukes one allowlist's sentinels "
             "without touching the others.")
    ap.add_argument("--cache-dir", default=None, metavar="DIR",
        help="Enable a content-addressed PASS cache. On a hit (the linter "
             "script + every scanned `.md` hash to the same key as a "
             "previously-cached PASS) the scan is skipped and exit 0 is "
             "returned immediately. Misses run normally and write a fresh "
             "sentinel only on success. Stale or poisoned sentinels are "
             "ignored because the key is recomputed from the working tree "
             "every run. Sentinels are stored under an extension-derived "
             "subdirectory (see --extension) so different allowlists "
             "never share a sentinel pool.")
    ap.add_argument("--no-cache-write", action="store_true",
        help="With --cache-dir, read the sentinel but never write it. "
             "Useful for read-only / forked-repo CI runs.")
    ap.add_argument("--diff-base", default=None, metavar="REF",
        help="Diff-mode: only report per-file violations (P-001…P-006, "
             "P-008, within-file P-007) for `.md` files changed vs. "
             "REF (e.g. `origin/main`, `HEAD~1`, or a SHA). Resolved "
             "with `git diff --name-only --diff-filter=AM REF...HEAD` "
             "so renames + deletions are excluded. Cross-file P-007 "
             "still scans the full tree so new duplicates introduced "
             "by a changed file always surface, even if the colliding "
             "first declaration lives in an unchanged file. Mutually "
             "exclusive with --changed-files.")
    ap.add_argument("--changed-files", default=None, metavar="PATH",
        help="Diff-mode: read the changed-file list from PATH (one "
             "repo-relative path per line, blanks/`#` comments ignored) "
             "instead of invoking git. Use `-` to read from stdin. "
             "Same semantics as --diff-base for cross-file P-007. "
             "Mutually exclusive with --diff-base.")
    ap.add_argument("--diff-empty-passes", action="store_true",
        help="With --diff-base/--changed-files, when the resolved "
             "changed-file set has no `.md` under --root, exit 0 "
             "without scanning. Default behaviour is the same; this "
             "flag is accepted for explicitness in CI configs.")
    ap.add_argument("--github", dest="github", action="store_true",
        default=None,
        help="Emit one GitHub Actions `::error file=…,line=…,title=…::` "
             "workflow command per violation in addition to the human-"
             "readable summary, so each finding lights up inline on "
             "the PR diff with its rule code (P-001 … P-008). Auto-"
             "enabled when the `GITHUB_ACTIONS` env var is `true` "
             "(i.e. inside any GitHub Actions runner). Use "
             "`--no-github` to force-disable.")
    ap.add_argument("--no-github", dest="github", action="store_false",
        help="Disable GitHub Actions annotations even when the "
             "`GITHUB_ACTIONS` env var would auto-enable them.")
    ap.add_argument("--diff-context", type=int, default=3, metavar="N",
        help="When --diff-base is set, fetch N lines of unified-diff "
             "context around each violation (via `git diff -UN <base> "
             "-- <file>`) and print the post-state excerpt under the "
             "human-readable summary so authors can patch without "
             "switching to git. Default 3; 0 disables. Ignored in "
             "--changed-files mode (no diff-base to query). In --json "
             "mode, excerpts are suppressed by default to keep the "
             "schema byte-identical for legacy consumers; pass "
             "`--json-excerpts` to emit them as a structured array.")
    ap.add_argument("--json-excerpts", action="store_true",
        help="Only meaningful with --json + --diff-base. Adds an "
             "`excerpt` array to each violation row containing the "
             "post-state diff window around the violation line. Each "
             "element is `{\"line\": int, \"kind\": \"+\"|\" \", "
             "\"text\": str, \"focus\": bool}` — `focus` marks the "
             "exact violation line so consumers don't need to re-do "
             "the centering math. The schema is additive: violations "
             "with no available excerpt simply omit the key, so "
             "parsers that don't know about it are unaffected. "
             "Window size is governed by --diff-context.")
    ap.add_argument("--suggest-patch", action="store_true",
        help="Under each human-readable diff excerpt, append a "
             "`git apply`-style unified-diff scaffold that removes "
             "the offending line and inserts a rule-specific TODO "
             "marker in its place. Designed for copy-paste: pipe the "
             "block (between the `--- BEGIN SUGGESTED PATCH ---` and "
             "`--- END SUGGESTED PATCH ---` fences) into "
             "`git apply -p0` and the file is staged with a clearly "
             "marked spot to fix. The replacement text is a TODO "
             "hint, not a real fix — the linter cannot infer the "
             "author's intent. No-op without --diff-base (no post-"
             "state line numbers available outside diff mode).")
    ap.add_argument("--json-suggest-patch", action="store_true",
        help="Only meaningful with --json + --diff-base. Adds a "
             "`suggested_patch` string field to each violation row "
             "containing the same `git apply`-ready unified diff as "
             "--suggest-patch. The schema is strictly additive: "
             "violations the linter can't generate a patch for "
             "(e.g. line not in any captured hunk) simply omit the "
             "key, so legacy parsers keying off `file`/`line`/`code`/"
             "`message` keep working unchanged.")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    repo_root = Path(args.repo_root).resolve()
    if not root.is_dir():
        print(f"error: --root {args.root!r} is not a directory", file=sys.stderr)
        return 2

    if args.diff_base and args.changed_files:
        print("error: --diff-base and --changed-files are mutually exclusive",
              file=sys.stderr)
        return 2

    if args.diff_context < 0:
        print(f"error: --diff-context must be >= 0 (got {args.diff_context})",
              file=sys.stderr)
        return 2

    # Tri-state: --github → True, --no-github → False, neither → auto.
    if args.github is None:
        github_annotations = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    else:
        github_annotations = args.github

    intent_verbs = DEFAULT_INTENT_VERBS | {v.lower() for v in args.allow_verb}

    # ---- Resolve --extension allowlist ---------------------------
    # ``--extension`` is repeatable; ``None`` (no flag passed) keeps
    # the historical ``("md",)`` behaviour. We normalise to lowercase,
    # strip any leading dot the user typed by accident, and dedupe via
    # ``dict.fromkeys`` so the FIRST occurrence wins (preserves the
    # CLI order in error messages without affecting the cache segment,
    # which sorts independently). The result is a tuple so it can
    # flow through ``iter_markdown_files`` and the cache key as a
    # hashable, append-safe value.
    if args.extension is None:
        extensions = DEFAULT_EXTENSIONS
    else:
        cleaned = [e.lstrip(".").lower() for e in args.extension if e.strip()]
        if not cleaned:
            print("error: --extension requires at least one non-empty value",
                  file=sys.stderr)
            return 2
        extensions = tuple(dict.fromkeys(cleaned))

    # ---- Resolve diff-mode changed-file allowlist (if any) -------
    # ``changed_md`` is None ⇒ full-tree mode (legacy behaviour).
    # ``changed_md`` is a set of resolved Paths ⇒ diff mode: only
    # those files emit per-file violations. Cross-file P-007 still
    # walks every `.md` so a changed file colliding with an
    # unchanged target is reported.
    changed_md: set[Path] | None = None
    if args.diff_base or args.changed_files:
        try:
            changed_md = _resolve_changed_md(
                repo_root, root,
                diff_base=args.diff_base,
                changed_files=args.changed_files,
            )
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if not args.json:
            print(f"ℹ️  placeholder-comments: diff-mode active — "
                  f"{len(changed_md)} changed `.md` file(s) under {args.root}/")
        if not changed_md:
            # Nothing under --root changed → fast PASS. Cross-file P-007
            # has nothing new to report by definition (no new bullets).
            if args.json:
                print("[]")
            else:
                print(f"✅ placeholder-comments: no spec changes vs. diff base, "
                      "skipping scan.")
            return 0

    # ---- Cache fast-path ------------------------------------------
    # The cache key fingerprints every input that can change the
    # linter's verdict: the linter script itself, the resolved root,
    # the imperative-verb allowlist (P-001 widening), and every `.md`
    # under the root. A hit short-circuits the scan; a miss falls
    # through to the full lint and writes a sentinel only if the
    # scan ends clean (exit 0).
    #
    # Diff mode bypasses the PASS-cache: the cache is keyed on the
    # full-tree fingerprint, but a diff-mode run only inspects a
    # subset of files, so its PASS verdict is *narrower* and must
    # never satisfy a future full-tree query. Skipping cache I/O
    # entirely keeps the invariant trivial: only full-tree PASSes
    # are ever cached.
    cache_key: str | None = None
    sentinel: Path | None = None
    if args.cache_dir and changed_md is None:
        cache_key = _compute_cache_key(root, intent_verbs,
                                       extensions=extensions)
        # Sentinels live under a per-extension-allowlist subdirectory
        # so different ``--extension`` runs are physically segregated
        # on disk. The segment name is deterministic from the sorted
        # extensions: ``ext-md``, ``ext-md+mdx``, etc. Long or
        # otherwise filesystem-hostile allowlists fall back to a
        # short-hash form (see ``_cache_segment``) to keep the path
        # legal on Windows + tar-friendly. ``mkdir(parents=True)``
        # below creates the segment directory on first PASS.
        segment = _cache_segment(extensions)
        sentinel = Path(args.cache_dir) / segment / f"{cache_key}.pass"
        if sentinel.is_file():
            if not args.json:
                print(f"✅ placeholder-comments: cache hit "
                      f"({segment}/{cache_key[:12]}…), "
                      f"skipping scan of {args.root}/")
            else:
                print("[]")
            return 0

    violations: list[Violation] = []
    cross_file_bullets: list[tuple[str, int, str]] = []
    for md in iter_markdown_files(root, extensions=extensions):
        if changed_md is not None and md.resolve() not in changed_md:
            # Unchanged file: still collect its bullets so cross-file
            # P-007 can detect a new collision introduced by a
            # changed file, but suppress its per-file violations.
            _collect_bullets_only(md, repo_root, cross_file_bullets)
            continue
        violations.extend(lint_file(md, repo_root, cross_file_bullets, intent_verbs))

    # ---- P-007 cross-file duplicates -------------------------------
    # Group every valid bullet across the scan by canonical target.
    # Within-file duplicates are already reported above, so we only
    # surface groups whose entries span ≥2 distinct files. The
    # *second* and later occurrences are flagged, pointing back at
    # the first declaration site for fast triage.
    #
    # In diff mode, only collisions whose *later* side lives in a
    # changed file are reported — an unchanged file colliding with
    # another unchanged file is pre-existing and out of scope for
    # the push under review.
    by_target: dict[str, list[tuple[str, int, str]]] = {}
    for rel, ln, target in cross_file_bullets:
        by_target.setdefault(_canonical_target(rel, target, repo_root), []).append(
            (rel, ln, target)
        )
    changed_rels: set[str] | None = None
    if changed_md is not None:
        changed_rels = {
            str(p.relative_to(repo_root)) for p in changed_md
            if p.is_relative_to(repo_root)
        }
    for key, entries in by_target.items():
        files_seen = {e[0] for e in entries}
        if len(files_seen) < 2:
            continue
        first_rel, first_ln, first_target = entries[0]
        for rel, ln, target in entries[1:]:
            if rel == first_rel:
                continue  # already reported by the within-file pass
            if changed_rels is not None and rel not in changed_rels:
                continue  # pre-existing collision in unchanged file
            violations.append(Violation(rel, ln, "P-007",
                f"Duplicate placeholder target `{target}` — also declared at "
                f"`{first_rel}:L{first_ln}` as `{first_target}` "
                "(anchor differences are ignored)."))

    # ---- Pre-fetch diff excerpts once for both human + JSON modes
    # (only when the user actually wants them). Excerpts are bounded
    # by changed-file count, not violation count — a single bad
    # block tripping P-001 + P-002 + P-004 still costs one git
    # invocation per file, not three.
    diff_excerpts: dict[str, _DiffExcerpts] = {}
    want_excerpts = (
        violations
        and args.diff_base
        and args.diff_context > 0
        and changed_md is not None
        and (not args.json or args.json_excerpts)
    )
    # Suggested patches reuse the same ``_DiffExcerpts`` data (post-
    # state line index + hunk windows) so we widen the fetch trigger
    # to also cover --suggest-patch / --json-suggest-patch when
    # excerpts themselves are off (e.g. --diff-context=0 but the
    # author still wants a copy-paste fix scaffold).
    want_patches = (
        violations
        and args.diff_base
        and changed_md is not None
        and ((not args.json and args.suggest_patch)
             or (args.json and args.json_suggest_patch))
    )
    if want_excerpts or want_patches:
        affected = sorted({v.file for v in violations
                           if (repo_root / v.file).resolve() in changed_md})
        for rel in affected:
            # When only patches are requested, fetch a minimal
            # 1-line context so suggest_patch() still has the
            # above/below anchor rows it uses for hunk math. The
            # excerpt renderer would emit a tiny window in that
            # case, but we already gate human/JSON excerpt output
            # on ``want_excerpts`` separately so nothing leaks.
            ctx = args.diff_context if want_excerpts else max(
                1, args.diff_context,
            )
            excerpt = _fetch_diff_excerpts(
                repo_root, args.diff_base, rel, ctx,
            )
            if excerpt is not None:
                diff_excerpts[rel] = excerpt

    if args.json:
        # Backward-compatible: when --json-excerpts is OFF the
        # payload is byte-identical to the legacy schema (only the
        # four Violation fields). When ON, an ``excerpt`` array is
        # appended to violations that have one — never present as
        # ``null`` or ``[]``, so legacy parsers that key only off
        # ``file``/``line``/``code``/``message`` keep working
        # without seeing a new always-present field.
        if not args.json_excerpts and not args.json_suggest_patch:
            print(json.dumps([asdict(v) for v in violations], indent=2))
        else:
            payload: list[dict[str, object]] = []
            for v in violations:
                row = asdict(v)
                excerpt = diff_excerpts.get(v.file)
                if excerpt is not None and args.json_excerpts:
                    snippet = excerpt.render_structured(
                        v.line, args.diff_context,
                    )
                    if snippet:
                        row["excerpt"] = snippet
                if excerpt is not None and args.json_suggest_patch:
                    patch_text = excerpt.suggest_patch(v.file, v.line, v.code)
                    if patch_text:
                        row["suggested_patch"] = patch_text
                payload.append(row)
            # ``ensure_ascii=False`` so non-ASCII spec content
            # (e.g. quoted UTF-8 paths from the rename hardening)
            # round-trips as readable characters instead of
            # ``\uXXXX`` escapes. Still valid JSON; downstream
            # parsers don't care.
            print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if not violations:
            print(f"✅ placeholder-comments: no malformed blocks under {args.root}/")
        else:
            print(f"❌ placeholder-comments: {len(violations)} violation(s):\n")
            for v in violations:
                print(f"  {v.file}:{v.line}  [{v.code}] {v.message}")
                excerpt = diff_excerpts.get(v.file)
                if excerpt is not None and args.diff_context > 0:
                    snippet = excerpt.render(v.line, args.diff_context)
                    if snippet:
                        # Two-space indent under the violation line
                        # so the excerpt is visually attached to it
                        # in the log without breaking grep on the
                        # leading `<file>:<line>` shape.
                        for sline in snippet:
                            print(f"    {sline}")
                if excerpt is not None and args.suggest_patch:
                    patch_text = excerpt.suggest_patch(v.file, v.line, v.code)
                    if patch_text:
                        # Wrap the patch in clear fences so authors
                        # can mouse-select the body and pipe it
                        # straight into ``git apply -p0 --recount``.
                        # Indented to nest visually under the
                        # violation, but the fences themselves stay
                        # at column 4 so awk/sed extraction is
                        # trivial (look for the literal sentinel).
                        print("    --- BEGIN SUGGESTED PATCH "
                              "(git apply -p0 --recount) ---")
                        for pline in patch_text.rstrip("\n").split("\n"):
                            print(f"    {pline}")
                        print("    --- END SUGGESTED PATCH ---")
            print("\n  See linter-scripts/check-placeholder-comments.py for rule docs.")

    # ---- GitHub Actions annotations (always after the human summary)
    # so a reviewer scrolling the log sees the digest first, then the
    # auto-attached inline annotations on the PR diff. Workflow
    # commands go to STDOUT regardless of --json so JSON consumers
    # still get clean output on a separate channel (the annotations
    # stream is interleaved but parseable by the runner, not by us).
    if github_annotations and violations:
        for line in _format_github_annotations(violations):
            print(line)

    # ---- Persist sentinel on clean runs only ----------------------
    # Failed runs MUST NOT poison the cache: a future "fix" might
    # re-introduce the same hash via revert, and we'd then skip the
    # scan and miss the regression. Only PASS gets cached.
    if sentinel is not None and not violations and not args.no_cache_write:
        try:
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text(
                f"placeholder-comments PASS\nkey={cache_key}\n",
                encoding="utf-8",
            )
        except OSError as e:
            # Cache write failures are advisory — never fail the run.
            print(f"::warning::placeholder-comments: cache write failed: {e}",
                  file=sys.stderr)

    return 1 if violations else 0


def _resolve_changed_md(repo_root: Path, root: Path, *,
                        diff_base: str | None,
                        changed_files: str | None) -> set[Path]:
    """Resolve the set of `.md` files under ``root`` that are changed.

    Two input modes:
      * ``diff_base`` → invoke
        ``git diff --name-status -M -C --diff-filter=AMRC
        <base>...HEAD`` from ``repo_root``. The triple-dot syntax
        compares HEAD against the merge-base with ``<base>``, which
        matches GitHub's PR diff and survives force-pushes / rebases
        on the base branch. The ``AMRC`` filter keeps Added,
        Modified, Renamed, and Copied paths and drops deletes + type
        changes (a deleted file can't carry a new violation in the
        post-state). For ``R``/``C`` rows we take the *new* path so
        the linter re-checks the file under its post-rename location
        — that's where the placeholder block lives now, and a rename
        commit often touches it (e.g. updated back-pointer hints).
        ``-M`` enables rename detection (default 50 % similarity)
        and ``-C`` enables copy detection so the new sibling of a
        copy is also linted.
      * ``changed_files`` → read newline-delimited paths from the
        given file (``-`` = stdin). Blank lines and ``#`` comments are
        ignored. Useful for CI runners that compute the diff
        themselves (e.g. ``dorny/paths-filter``) or for local testing
        without a git invocation. Renames may be expressed on a
        single line as either ``OLD\\tNEW`` (tab-separated, matches
        ``git diff --name-status`` output verbatim) or
        ``OLD => NEW`` (matches ``git status -s`` rename arrows). In
        both forms the OLD path is discarded and the NEW path is
        linted as a normal change.

    Returned paths are absolute + resolved and filtered to:
      * extension ``.md``
      * residing under ``root`` (so a README change doesn't trigger a
        spec scan)
      * actually present on disk (a Modified path that was reverted
        in a later commit of the same push won't exist)
    """
    # Each entry is the post-state repo-relative path. Rename/copy
    # rows contribute only their NEW side; deletes contribute nothing
    # (the diff-filter / parser drops them upstream).
    raw: list[str] = []
    if diff_base:
        try:
            proc = subprocess.run(
                ["git", "diff", "--name-status", "-M", "-C",
                 "--diff-filter=AMRC",
                 f"{diff_base}...HEAD"],
                cwd=repo_root, check=True, capture_output=True, text=True,
            )
        except FileNotFoundError as e:
            raise RuntimeError(f"git not found on PATH: {e}") from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"git diff vs. {diff_base!r} failed (exit {e.returncode}): "
                f"{e.stderr.strip() or '(no stderr)'}"
            ) from e
        raw = _parse_name_status(proc.stdout)
    else:
        assert changed_files is not None
        if changed_files == "-":
            lines = sys.stdin.read().splitlines()
        else:
            try:
                lines = Path(changed_files).read_text(encoding="utf-8").splitlines()
            except OSError as e:
                raise RuntimeError(
                    f"--changed-files {changed_files!r} unreadable: {e}"
                ) from e
        raw = _normalise_changed_lines(lines)
    out: set[Path] = set()
    for line in raw:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if not s.endswith(".md"):
            continue
        p = (repo_root / s).resolve()
        try:
            p.relative_to(root)
        except ValueError:
            continue
        if not p.is_file():
            continue
        out.add(p)
    return out


# `git diff --name-status -M` emits one of:
#   A\tpath          (added)
#   M\tpath          (modified)
#   D\tpath          (deleted)              — pre-filtered, never seen here
#   R<score>\told\tnew  (renamed, score 0–100)
#   C<score>\told\tnew  (copied,  score 0–100)
#   T\tpath          (type change)          — pre-filtered, never seen here
# Tabs are the field separator; we split on tab and key off the first
# character of column 0 to decide which column carries the new path.
_NAME_STATUS_RE = re.compile(r"^([AMDRCTUX])(\d{0,3})$")


# Git emits paths in C-quoted form (``"path\twith\ttab"``) when
# ``core.quotePath`` is true (the default) and the path contains a
# byte that isn't safe for the terminal — tabs, newlines, control
# chars, non-ASCII bytes when ``core.quotePath=true``. The quoting
# is a strict subset of C string escapes: surrounding double quotes,
# backslash escapes for ``\a \b \t \n \v \f \r " \\``, and
# ``\NNN`` octal triplets for arbitrary bytes. A path that doesn't
# need escaping is output bare (no quotes). We MUST decode quoted
# paths before splitting on tab — otherwise an embedded ``\t`` in a
# valid filename would be mistaken for a column separator.
#
# Reference: ``git help config`` → ``core.quotePath``;
# ``quote.c::quote_c_style_counted`` in git's source.
# Match a *run* of consecutive ``\NNN`` octal escapes so we can
# decode them as a single UTF-8 byte sequence. Decoding triplet-by-
# triplet would split a multi-byte character (e.g. ``é`` =
# ``\303\251``) across two ``bytes.decode`` calls and each half
# would emit a U+FFFD replacement char. A single ``re.sub`` over
# the whole run hands the bytes to the codec atomically, which is
# the only way to get correct round-trips for non-ASCII paths.
_C_OCT_RUN_RE = re.compile(r"(?:\\[0-7]{1,3})+")
_C_ESC_TBL = {
    "a": "\a", "b": "\b", "t": "\t", "n": "\n",
    "v": "\v", "f": "\f", "r": "\r",
    '"': '"', "\\": "\\",
}


def _unquote_git_path(field: str) -> str:
    """Reverse git's C-style path quoting if ``field`` is wrapped in
    double quotes; otherwise return ``field`` unchanged.

    Tolerant of malformed input: a stray ``\\x`` (where ``x`` is not
    a recognised escape) is passed through verbatim rather than
    raising — this matches how a human would copy-paste the row out
    of ``git status`` and into ``--changed-files``. Also tolerant of
    a trailing CR (Windows line endings) which can survive
    ``splitlines()`` when the file is opened in binary or has lone
    ``\\r`` separators upstream.
    """
    s = field
    # Strip a single trailing CR — harmless on POSIX paths (NUL is
    # the only forbidden byte besides ``/``) and silently fixes
    # Windows-runner inputs.
    if s.endswith("\r"):
        s = s[:-1]
    if not (len(s) >= 2 and s.startswith('"') and s.endswith('"')):
        return s
    inner = s[1:-1]
    # First expand ``\NNN`` octal byte escapes. We decode each
    # *run* of escapes as one UTF-8 byte string so a multi-byte
    # character split across triplets (``\303\251`` = ``é``)
    # round-trips correctly. ``errors="replace"`` keeps malformed
    # input visible (U+FFFD) rather than raising — same posture as
    # the rest of the linter, which never crashes on weird git
    # output, only logs the violation site.
    def _oct_run_sub(m: "re.Match[str]") -> str:
        run = m.group(0)
        try:
            buf = bytes(int(t, 8) for t in run.split("\\")[1:])
        except ValueError:
            return run
        return buf.decode("utf-8", "replace")
    inner = _C_OCT_RUN_RE.sub(_oct_run_sub, inner)
    # Then expand single-char escapes.
    out: list[str] = []
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "\\" and i + 1 < len(inner):
            esc = inner[i + 1]
            out.append(_C_ESC_TBL.get(esc, "\\" + esc))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _parse_name_status(stdout: str) -> list[str]:
    """Extract the post-state path from each ``git diff --name-status``
    row, mapping renames + copies to their NEW side.

    Unknown / malformed rows are skipped silently — the linter's job
    is to lint placeholders, not to police git plumbing output.

    Hardened against git's path-quoting and whitespace edge cases:

    * Tabs are the field separator. C-quoted paths
      (``"with\\ttab.md"``) are decoded *before* the tab split would
      see them, so an embedded literal tab inside a filename can't
      masquerade as a column separator.
    * Trailing CR on the row (CRLF input from a Windows-piped diff)
      is stripped per-field by :func:`_unquote_git_path`.
    * The R/C arm requires a non-empty *new* path (``cols[2]``) but
      tolerates an empty *old* path slot — git never emits one, but
      hand-rolled diff payloads occasionally do, and there's no
      reason to discard the row when its NEW side is well-formed.
    * Whitespace-only paths (``"   "``) are kept as-is — POSIX
      permits them, and ``Path.is_file()`` downstream will resolve
      whether the file actually exists.
    """
    out: list[str] = []
    for line in stdout.splitlines():
        if not line:
            continue
        # Drop a trailing CR on the *row* before column splitting so
        # the last field doesn't get a stray ``\r`` glued onto it.
        # Per-field stripping handles the in-quote case; this handles
        # the bare (unquoted) case for the row's last path.
        if line.endswith("\r"):
            line = line[:-1]
        cols = line.split("\t")
        if len(cols) < 2:
            continue
        m = _NAME_STATUS_RE.match(cols[0])
        if not m:
            continue
        kind = m.group(1)
        if kind in ("R", "C"):
            # Rename / copy: cols = [R<score>, old, new]. Take new.
            # ``cols[2]`` is required; ``cols[1]`` (old) may be empty
            # in pathological inputs — we don't need it for linting.
            if len(cols) >= 3 and cols[2] != "":
                out.append(_unquote_git_path(cols[2]))
        elif kind in ("A", "M"):
            # Add / modify: cols = [A|M, path]. Take path.
            if cols[1] != "":
                out.append(_unquote_git_path(cols[1]))
        # D / T / U / X intentionally dropped — see docstring.
    return out


# Two textual rename conventions accepted in `--changed-files` input:
#   1. Tab-separated, matches `git diff --name-status` verbatim:
#        R087\tspec/old.md\tspec/new.md
#      Any leading status token is tolerated (we just take the last
#      tab-separated column as the new path).
#   2. Arrow-separated, matches `git status -s` short output:
#        spec/old.md => spec/new.md
#      Whitespace around the arrow is ignored.
# The arrow form is intentionally permissive on the surrounding
# whitespace because it's authored by humans (or by `git status -s`
# which left-pads the row with two status columns + a space).
# ``\S`` at each end was too strict — it rejected paths that
# legitimately start or end with a space (rare but POSIX-legal). We
# now anchor on ``=>`` and let the path bodies be any non-empty
# trimmed run; trimming is done *after* the split so embedded
# whitespace inside the path is preserved.
_RENAME_ARROW_RE = re.compile(r"^\s*(?P<old>.+?)\s*=>\s*(?P<new>.+?)\s*$")


def _normalise_changed_lines(lines: list[str]) -> list[str]:
    """Collapse rename-bearing rows in a ``--changed-files`` payload
    down to their post-rename path.

    Plain paths (no tab, no ``=>``) pass through unchanged. Comments
    and blanks are *not* stripped here — the caller does that on the
    normalised output so we don't lose alignment with the source line
    numbers in error messages.

    Hardened against the same whitespace + quoting edge cases as
    :func:`_parse_name_status`:

    * Tab rows: instead of dropping every empty column (which
      silently re-indexes ``R\\t\\told\\tnew`` to ``[R, old, new]``
      and then ``cols[-1]`` is correct, but ``R<score>\\told\\t\\t``
      would re-index to ``[R<score>, old]`` and steal ``old`` as the
      "new" path), we keep the column count intact and pick the
      last non-empty field. Quoted fields are unquoted; trailing
      CR is stripped.
    * Arrow rows: the regex no longer requires ``\\S`` at the path
      boundaries, so a path with a leading/trailing space round-
      trips correctly. The ``new`` group is unquoted to match what
      a user pasted from ``git status``.
    * A line that contains *only* whitespace (or a CR-only line on
      Windows input) is passed through verbatim so the caller's
      blank/comment filter can still discard it on the same line
      number.
    """
    out: list[str] = []
    for line in lines:
        # Strip a trailing CR for the whole row before any other
        # parsing. We don't ``rstrip()`` — that would eat legitimate
        # trailing spaces in a path. Only ``\r`` is dropped.
        if line.endswith("\r"):
            line = line[:-1]
        # Tab form: take the last tab-separated column. Works for
        # both `R<score>\told\tnew` (3 cols) and unscored `R\told\tnew`
        # (rare, e.g. when authors hand-edit the file).
        if "\t" in line:
            # Preserve column positions: split without filtering, so
            # padding tabs from copy-pasted output (e.g. an extra
            # ``\t`` after the ``R<score>`` token in some tooling)
            # don't shift our column index. Then pick the last
            # *non-empty* field as the post-rename path.
            cols = line.split("\t")
            new_col = ""
            for c in reversed(cols):
                if c != "":
                    new_col = c
                    break
            if new_col:
                out.append(_unquote_git_path(new_col))
            continue
        # Arrow form: `OLD => NEW`.
        m = _RENAME_ARROW_RE.match(line)
        if m:
            new_path = m.group("new")
            # Trim at boundaries (regex already did greedy-min) but
            # don't touch interior whitespace. Then unquote in case
            # the user pasted a C-quoted form from ``git status``.
            out.append(_unquote_git_path(new_path.strip()))
            continue
        out.append(line)
    return out


# ---- Diff-excerpt rendering (used by the human summary in diff mode)
#
# We keep the parser tiny and tolerant: only the post-state side of a
# unified diff matters (that's where line numbers in violations come
# from), and any malformed hunk gracefully degrades to "no excerpt"
# rather than failing the run. The shape captured per file is:
#
#     {post_line_no: (kind, text)}
#
# where ``kind`` is one of:
#     "+"   line added in the post-state (highlighted in the snippet)
#     " "   context line carried over from both sides
# Removed lines (``-``) are dropped because they don't have a
# post-state line number a violation could reference. The renderer
# slices a ±context window around the violation line, falling back
# to "no diff context available" if the line isn't part of the
# fetched hunks (e.g. a P-007 collision pointing at a hunk that
# wasn't included in the unified diff).

_HUNK_HEADER_RE = re.compile(
    r"^@@\s*-\d+(?:,\d+)?\s+\+(?P<start>\d+)(?:,(?P<count>\d+))?\s*@@"
)


@dataclass(frozen=True)
class _Hunk:
    """One post-state hunk window inside a parsed unified diff.

    ``start`` / ``end`` are inclusive 1-indexed post-state line
    numbers covering every ``+`` and `` `` row this hunk emitted.
    A single-line hunk has ``start == end``. A diff with no
    post-state coverage (rare: pure-deletion file, an empty added
    file) yields zero hunks; the parent ``_DiffExcerpts.hunks``
    list is empty in that case and the renderer returns ``[]``.
    """
    start: int
    end: int

    def contains(self, line: int) -> bool:
        return self.start <= line <= self.end

    def distance_to(self, line: int) -> int:
        """Minimum line-count distance from ``line`` to this hunk
        window. Returns 0 when the line is inside the hunk."""
        if line < self.start:
            return self.start - line
        if line > self.end:
            return line - self.end
        return 0


@dataclass(frozen=True)
class _DiffExcerpts:
    """Post-state line index for one file's `git diff -UN` output.

    ``lines[N]`` is ``(kind, text)`` for post-state line ``N`` (1-
    indexed). ``min_line`` / ``max_line`` describe the union of all
    hunk windows so the renderer can detect "violation outside any
    hunk" cleanly.

    ``hunks`` lists each hunk as a discrete ``_Hunk`` range so the
    renderer can pick the best match for a violation that lives
    between hunks (e.g. a P-007 cross-file collision that points at
    a placeholder block far away from the changed lines). Without
    this list the old renderer would silently emit an empty excerpt
    when the violation fell in the *gap* between two hunks but
    inside the global ``[min_line, max_line]`` bounds — visible to
    the bounds check but not to the line-by-line lookup.
    """
    lines: dict[int, tuple[str, str]]
    min_line: int
    max_line: int
    hunks: tuple[_Hunk, ...] = ()

    def _select_hunk(self, line: int) -> _Hunk | None:
        """Pick the best hunk to use as context for ``line``.

        Selection rules, in order:

        1. If a hunk *contains* ``line``, return it (zero distance).
        2. Otherwise return the hunk with the smallest distance to
           ``line``. Ties are broken in *post-state line order* —
           the earlier hunk wins, which keeps output deterministic
           and matches how a human reads a file top-to-bottom.
        3. No hunks → ``None`` (caller emits "no excerpt").
        """
        if not self.hunks:
            return None
        # Single pass: find the minimum distance and earliest hunk
        # at that distance. ``min(..., key=...)`` over an empty
        # iterable would raise; the early ``not self.hunks`` guard
        # above prevents that.
        return min(self.hunks,
                   key=lambda h: (h.distance_to(line), h.start))

    def render(self, line: int, context: int) -> list[str]:
        """Return a list of human-readable excerpt lines centered on
        ``line`` with up to ``context`` lines on each side, or [] if
        no relevant excerpt is available.

        When the violation line falls between hunks, the renderer
        selects the *nearest* hunk (see :meth:`_select_hunk`) and
        prepends a one-line breadcrumb so the reader knows the
        excerpt is not centered on the violation line itself but on
        the closest changed region. This is far more useful than the
        old behaviour of returning an empty list, which made the
        violation line look like it had no diff context at all.
        """
        if not self.lines:
            return []
        hunk = self._select_hunk(line)
        if hunk is None:
            return ["(line not in current diff hunks — view file directly)"]
        # Window selection:
        #   * Violation INSIDE the hunk → ±context around the
        #     violation line, clamped to hunk bounds. Mirrors the
        #     classic single-hunk behaviour.
        #   * Violation OUTSIDE every hunk → render the *entire*
        #     selected hunk (capped at 2*context+1 lines so we
        #     don't blow up output for a huge nearby hunk). This
        #     is what "best matching hunk context" means: the user
        #     gets to actually see the changed region near their
        #     violation, not just a breadcrumb.
        if hunk.contains(line):
            lo = max(hunk.start, line - context)
            hi = min(hunk.end, line + context)
        else:
            cap = 2 * context + 1
            if hunk.end - hunk.start + 1 <= cap:
                lo, hi = hunk.start, hunk.end
            elif line < hunk.start:
                # Hunk is below the violation: take its leading edge.
                lo, hi = hunk.start, hunk.start + cap - 1
            else:
                # Hunk is above the violation: take its trailing edge.
                lo, hi = hunk.end - cap + 1, hunk.end
        out: list[str] = []
        if not hunk.contains(line):
            # Violation is between hunks (or outside the whole diff
            # but still within the global ±context tolerance). Tell
            # the reader we're showing the *nearest* changed region
            # so they don't assume the excerpt is centered on the
            # violation line itself.
            delta = hunk.distance_to(line)
            out.append(
                f"  ℹ︎ violation at L{line}; nearest changed hunk "
                f"@ L{hunk.start}-{hunk.end} (Δ {delta} line"
                f"{'s' if delta != 1 else ''})"
            )
        for ln in range(lo, hi + 1):
            entry = self.lines.get(ln)
            if entry is None:
                continue
            kind, text = entry
            marker = "►" if ln == line else " "
            sigil = "+" if kind == "+" else " "
            # ``ln:5`` keeps gutter widths aligned for files up to
            # 99,999 lines — well past anything we'll encounter in
            # spec/.
            out.append(f"{marker} {ln:5d} {sigil} {text}")
        return out

    def render_structured(self, line: int,
                          context: int) -> list[dict[str, object]]:
        """Return a JSON-friendly window around ``line``.

        Each element is ``{"line": <int>, "kind": "+"|" ", "text":
        <str>, "focus": <bool>, "nearest": <bool>}`` for one post-
        state line in the ±``context`` window. Pure data — no
        Unicode markers, no gutter padding, no truncation. The
        text payload is the raw post-state line content (no
        leading ``+``/`` `` sigil); the sigil is moved to the
        typed ``kind`` field so a JSON consumer doesn't have to
        strip it.

        ``focus`` is ``True`` only on the row whose ``line`` equals
        the violation line, regardless of whether that row is in
        the same hunk as the excerpt (it usually is; for a between-
        hunks violation the focus row simply doesn't appear in the
        excerpt). ``nearest`` is ``True`` on every row of the
        excerpt when the violation is *not* in this hunk — flagging
        the whole window as a fallback to the nearest changed
        region rather than the violation site itself.

        Returns ``[]`` (not a sentinel string like the human
        renderer) when:

        * no hunks were captured for this file, OR
        * no hunk is reachable as nearest (only happens when
          ``hunks`` is empty — see above).

        Returning ``[]`` rather than a "no data" object means the
        caller can simply omit the ``excerpt`` key when the list is
        empty — keeping the JSON schema strictly additive (legacy
        consumers see no new keys on violations the linter has no
        excerpt for).
        """
        if not self.lines:
            return []
        hunk = self._select_hunk(line)
        if hunk is None:
            return []
        # Same window logic as the human renderer — see render()
        # for the rationale. The ``cap`` keeps the JSON payload
        # bounded for consumers when a giant nearby hunk would
        # otherwise dump hundreds of rows per violation.
        if hunk.contains(line):
            lo = max(hunk.start, line - context)
            hi = min(hunk.end, line + context)
        else:
            cap = 2 * context + 1
            if hunk.end - hunk.start + 1 <= cap:
                lo, hi = hunk.start, hunk.end
            elif line < hunk.start:
                lo, hi = hunk.start, hunk.start + cap - 1
            else:
                lo, hi = hunk.end - cap + 1, hunk.end
        is_nearest = not hunk.contains(line)
        out: list[dict[str, object]] = []
        for ln in range(lo, hi + 1):
            entry = self.lines.get(ln)
            if entry is None:
                continue
            kind, text = entry
            out.append({
                "line": ln,
                "kind": kind,             # "+" (added) or " " (context)
                "text": text,
                "focus": ln == line,      # exact violation line
                "nearest": is_nearest,    # True ⇒ this row is from
                                          # the *nearest* hunk, not
                                          # the violation's own
            })
        return out


    def suggest_patch(self, file: str, line: int,
                      rule_code: str) -> str:
        """Return a ``git apply``-ready unified-diff scaffold that
        replaces the violation line with a TODO marker keyed off
        ``rule_code``.

        Returns ``""`` (empty string — *not* ``None``) when no
        post-state line for ``line`` was captured (violation outside
        every hunk, or pure-removal file). Callers treat ``""`` as
        "no patch available" and simply omit the suggestion.

        The emitted diff is intentionally minimal: at most one line
        of pre-existing context above and below the violation line
        (whatever the captured hunk has — the patch is shorter at
        hunk boundaries). Headers use ``a/<path>`` / ``b/<path>``
        and post-state line numbers on both sides; downstream users
        run ``git apply -p0 --recount`` (documented in the human
        renderer's fence) so any pre/post line drift is reconciled
        automatically.

        For a context line (``kind == " "``) the patch *swaps* the
        bad line for the TODO. For an added line (``kind == "+"``)
        the patch keeps the bad addition and inserts the TODO
        immediately after — the linter cannot safely delete an
        added line because the surrounding pre-state coordinates
        would shift; the author then manually removes the bad
        addition once they've written the real fix.
        """
        entry = self.lines.get(line)
        if entry is None:
            return ""
        kind, text = entry
        # Pre-existing context (one line above + below if available
        # in the captured hunk; the parser only stores ``+`` and
        # `` `` rows so anything we get back is safe to render).
        above = self.lines.get(line - 1)
        below = self.lines.get(line + 1)
        replacement = _RULE_FIX_HINTS.get(rule_code, _RULE_FIX_FALLBACK)

        body: list[str] = []
        # Anchor lines must use a leading single space — git's
        # tolerance for missing-space context lines is undefined
        # across versions; we always emit the canonical form.
        if above is not None:
            body.append(f" {above[1]}")
        if kind == "+":
            # Pure insertion: keep the bad ``+`` line, then add the
            # TODO immediately after it. The author removes the bad
            # line manually once they write the real fix.
            body.append(f" {text}")
            body.append(f"+{replacement}")
        else:
            # Context line in the post-state ⇒ it exists in the
            # pre-state too, so a swap (`-bad` / `+todo`) lands
            # cleanly with ``git apply --recount``.
            body.append(f"-{text}")
            body.append(f"+{replacement}")
        if below is not None:
            body.append(f" {below[1]}")

        # Hunk math: pre-state and post-state both span ``hunk_len``
        # lines starting at ``hunk_start`` (the row above the
        # violation, or the violation itself when it's the first
        # line of the file). For a swap, pre and post counts match.
        # For an insertion (`+` violation), post is one larger than
        # pre — git accepts mismatched counts and ``--recount``
        # would fix them anyway, but we emit the precise numbers so
        # vanilla ``git apply -p0`` works without the flag.
        hunk_start = line if above is None else line - 1
        ctx_above = 0 if above is None else 1
        ctx_below = 0 if below is None else 1
        if kind == "+":
            pre_len = ctx_above + 1 + ctx_below          # bad + ctx
            post_len = ctx_above + 2 + ctx_below         # bad + TODO + ctx
        else:
            pre_len = ctx_above + 1 + ctx_below          # bad + ctx
            post_len = ctx_above + 1 + ctx_below         # TODO + ctx

        header = (f"@@ -{hunk_start},{pre_len} "
                  f"+{hunk_start},{post_len} @@")
        return (
            f"--- a/{file}\n"
            f"+++ b/{file}\n"
            f"{header}\n"
            + "\n".join(body)
            + "\n"
        )


def _parse_unified_diff_post(stdout: str) -> _DiffExcerpts:
    """Parse `git diff -UN` output and index post-state lines only.

    File-header / index / mode lines are ignored — we already know
    which file we asked about. Hunk headers (``@@ -a,b +c,d @@``)
    reset the post-state line counter; ``+`` and `` `` rows advance
    it; ``-`` rows are skipped (no post-state coordinate).

    In addition to the flat ``lines`` index, we record each hunk
    as a discrete ``_Hunk(start, end)`` range so a multi-hunk file
    can route a violation to the *nearest* hunk's window rather
    than blindly slicing the global min/max range. A hunk that
    covers no post-state lines (e.g. pure removals — ``+`` count
    of 0 in the header) is dropped from the list because it has no
    coordinate a violation could land on.
    """
    lines: dict[int, tuple[str, str]] = {}
    cur_post = 0
    in_hunk = False
    min_line = 10**9
    max_line = 0
    hunks: list[_Hunk] = []
    cur_hunk_start: int | None = None
    cur_hunk_last: int | None = None

    def _flush_hunk() -> None:
        # Capture the in-progress hunk's [start, end] range. We
        # use the ``last`` post-line we actually wrote to (rather
        # than ``cur_post``, which has already been incremented
        # past it) so single-line hunks get start == end.
        nonlocal cur_hunk_start, cur_hunk_last
        if cur_hunk_start is not None and cur_hunk_last is not None:
            hunks.append(_Hunk(start=cur_hunk_start, end=cur_hunk_last))
        cur_hunk_start = None
        cur_hunk_last = None

    for raw in stdout.splitlines():
        if raw.startswith("@@"):
            _flush_hunk()
            m = _HUNK_HEADER_RE.match(raw)
            if not m:
                in_hunk = False
                continue
            cur_post = int(m.group("start"))
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if not raw:
            # Blank line inside a hunk = a context line whose payload
            # is empty. Treat as " " (context) to keep the line
            # counter honest.
            lines[cur_post] = (" ", "")
            min_line = min(min_line, cur_post)
            max_line = max(max_line, cur_post)
            if cur_hunk_start is None:
                cur_hunk_start = cur_post
            cur_hunk_last = cur_post
            cur_post += 1
            continue
        kind = raw[0]
        body = raw[1:]
        if kind == "+":
            lines[cur_post] = ("+", body)
            min_line = min(min_line, cur_post)
            max_line = max(max_line, cur_post)
            if cur_hunk_start is None:
                cur_hunk_start = cur_post
            cur_hunk_last = cur_post
            cur_post += 1
        elif kind == " ":
            lines[cur_post] = (" ", body)
            min_line = min(min_line, cur_post)
            max_line = max(max_line, cur_post)
            if cur_hunk_start is None:
                cur_hunk_start = cur_post
            cur_hunk_last = cur_post
            cur_post += 1
        elif kind == "-":
            # Removed line — no post-state coordinate. Skip silently.
            pass
        elif kind == "\\":
            # `\ No newline at end of file` marker — ignore.
            pass
        else:
            # Unknown row inside a hunk (extra header from combined
            # diff, etc.). Be defensive: bail out of this hunk so we
            # don't desync the line counter.
            _flush_hunk()
            in_hunk = False
    # Capture the final hunk (the last ``@@`` block has no
    # successor header to trigger a flush).
    _flush_hunk()

    if max_line == 0:
        return _DiffExcerpts(lines={}, min_line=0, max_line=0, hunks=())
    return _DiffExcerpts(lines=lines, min_line=min_line,
                         max_line=max_line, hunks=tuple(hunks))


def _fetch_diff_excerpts(repo_root: Path, diff_base: str, rel_path: str,
                         context: int) -> _DiffExcerpts | None:
    """Run `git diff -U<context> <base>...HEAD -- <rel_path>` and
    return the parsed post-state excerpt, or ``None`` if git fails
    (missing binary, unreachable base, file not in diff, etc.).

    Failures are silent on purpose: the violation summary is still
    printed without an excerpt — we never want a missing snippet to
    fail the lint run, only to degrade gracefully.
    """
    try:
        proc = subprocess.run(
            ["git", "diff", f"-U{context}", f"{diff_base}...HEAD",
             "--", rel_path],
            cwd=repo_root, check=True, capture_output=True, text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    if not proc.stdout.strip():
        return None
    return _parse_unified_diff_post(proc.stdout)


def _collect_bullets_only(path: Path, repo_root: Path,
                          bullets_out: list[tuple[str, int, str]]) -> None:
    """Cross-file P-007 helper for diff mode.

    Re-uses ``lint_file`` to extract every valid bullet from an
    unchanged file but discards the per-file violations. The bullets
    are needed so a *changed* file's new bullet can collide with a
    pre-existing target in an unchanged file and still trip P-007.
    """
    # ``lint_file`` already appends to ``bullets_out`` via its
    # ``valid_bullets`` parameter; we drop the violations list.
    lint_file(path, repo_root, bullets_out, DEFAULT_INTENT_VERBS)


# Per-rule one-liner shown in the annotation title so reviewers see
# *why* the line is flagged without opening the linter docs. Keep
# each entry ≤ ~50 chars — GitHub truncates long titles in the diff
# gutter tooltip.
RULE_TITLES: dict[str, str] = {
    "P-001": "Placeholder intent must be an imperative sentence",
    "P-002": "Placeholder body must be `- [text](link)` bullets",
    "P-003": "Placeholder link must be a relative `.md` path",
    "P-004": "Placeholder block must contain ≥1 valid bullet",
    "P-005": "Placeholder block must not contain blank lines",
    "P-006": "Placeholder opener has no matching closer",
    "P-007": "Duplicate placeholder target",
    "P-008": "Placeholder opener missing `@path:line` back-pointer",
}

# GitHub Actions workflow commands use `,` and `:` as field separators
# and `\n` / `\r` as line terminators. Any of these in the message
# corrupt the annotation, so we URL-style escape them per the
# documented contract:
# https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions
_ANNOTATION_ESCAPES: tuple[tuple[str, str], ...] = (
    ("%", "%25"),  # MUST be first — every other replacement uses %.
    ("\r", "%0D"),
    ("\n", "%0A"),
    (":", "%3A"),
    (",", "%2C"),
)


def _escape_annotation(value: str) -> str:
    out = value
    for src, dst in _ANNOTATION_ESCAPES:
        out = out.replace(src, dst)
    return out


def _format_github_annotations(violations: list[Violation]) -> Iterable[str]:
    """Yield one ``::error file=…,line=…,col=1,title=…::message`` per
    violation, preserving input order.

    * ``file`` is the repo-relative path stored on ``Violation`` —
      matches GitHub's checkout layout so the gutter pin lands on the
      right file in the PR diff.
    * ``line`` is the 1-indexed source line of the offending opener.
    * ``col=1`` is included so the annotation pins to the gutter
      rather than column 0 (some renderers hide col=0 entirely).
    * ``title`` is ``"<P-NNN> <one-liner>"`` so the rule code is the
      first thing reviewers see in the diff tooltip; unknown codes
      degrade to just the bare code (forward-compatible with future
      P-009+ rules added before this map is updated).
    * The message body is the full ``Violation.message`` so the
      remediation hint stays visible when the user clicks through.
    """
    for v in violations:
        title = RULE_TITLES.get(v.code)
        head = f"{v.code} {title}" if title else v.code
        yield (
            f"::error file={_escape_annotation(v.file)},"
            f"line={v.line},col=1,"
            f"title={_escape_annotation(head)}::"
            f"{_escape_annotation(v.message)}"
        )


def _compute_cache_key(
    root: Path,
    intent_verbs: frozenset[str] | set[str],
    *,
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS,
) -> str:
    """Build a SHA-256 fingerprint of every input that affects the verdict.

    Inputs (in deterministic order):
      1. The absolute, resolved scan root.
      2. The sorted, canonicalised imperative-verb allowlist.
      3. The sorted, canonicalised extension allowlist (so a future
         ``--extension mdx`` run can never collide with the default
         ``--extension md`` set, even before the cache-segment
         directory split would catch it on disk).
      4. The SHA-256 of the linter script itself (so a logic change
         invalidates every cached PASS automatically).
      5. For every file matching ``extensions`` under the root
         (sorted by path, dotfiles excluded — same filter as
         ``iter_markdown_files``):
         ``<repo-relative-path>\\0<sha256-of-bytes>\\n``

    Anything outside this set (mtimes, permissions, sibling files,
    environment variables) is intentionally excluded so the key is
    reproducible across machines and CI shards.
    """
    h = hashlib.sha256()
    # Schema tag bumped to v2 when the extension allowlist became
    # part of the key. A v1 sentinel would have been written without
    # the ``exts=`` line, so its hash domain is disjoint from v2 —
    # old sentinels are inert (never collide with new lookups) rather
    # than dangerous, but the explicit version tag documents intent.
    h.update(b"placeholder-comments-cache-v2\n")
    h.update(f"root={root}\n".encode("utf-8"))
    h.update(("verbs=" + ",".join(sorted(intent_verbs)) + "\n").encode("utf-8"))
    h.update(("exts=" + ",".join(sorted(extensions)) + "\n").encode("utf-8"))
    try:
        script_bytes = Path(__file__).resolve().read_bytes()
        h.update(b"script=" + hashlib.sha256(script_bytes).hexdigest().encode() + b"\n")
    except OSError:
        # __file__ unreadable (zipapp / frozen). Fall back to a stable
        # tag so the cache still works, just with coarser invalidation.
        h.update(b"script=unknown\n")
    for md in iter_markdown_files(root, extensions=extensions):
        try:
            data = md.read_bytes()
        except OSError:
            continue
        rel = str(md.relative_to(root)).encode("utf-8")
        h.update(rel + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n")
    return h.hexdigest()


# Filesystem-safe extension chars: lowercase ASCII letters + digits.
# Anything outside this set (dots in compound extensions like
# ``tar.gz``, unicode, slashes) forces the segment name into the
# hash-suffix form so we never produce a path that would explode on
# Windows, NTFS, or a tarball extracted on a case-insensitive FS.
_SAFE_EXT_RE = re.compile(r"^[a-z0-9]+$")

# Cap the readable form before we fall back to a hash. NTFS' 255-char
# filename limit is the binding constraint, but we want headroom for
# the surrounding ``ext-`` prefix, ``+`` joiners, AND the eventual
# ``<key>.pass`` filename inside the segment directory. 64 chars
# leaves the segment well under any practical limit while still
# accommodating ~10 typical extensions joined by ``+``.
_MAX_SEGMENT_BODY_LEN = 64


def _cache_segment(extensions: tuple[str, ...]) -> str:
    """Derive a filesystem-safe, deterministic cache subdirectory
    name from the active extension allowlist.

    Format::

        ext-<sorted-extensions-joined-by-plus>           (readable form)
        ext-h<10-char-sha256>                            (hash fallback)

    The readable form is preferred because it makes cache contents
    self-describing (``ls cache/`` shows ``ext-md/``, ``ext-md+mdx/``
    at a glance). We fall back to the hash form when ANY extension
    contains a character outside ``[a-z0-9]`` (so we never emit a
    Windows-illegal path), or when the joined name would exceed
    :data:`_MAX_SEGMENT_BODY_LEN`. The fallback is keyed on the same
    sorted-and-joined string the readable form would have used, so
    two runs with identical allowlists always land in the same
    bucket regardless of which branch they took.

    The function is pure: same input → same output, no I/O. That
    matters because the segment is consulted both on read (cache
    fast-path) and write (sentinel persistence), and any drift would
    silently bypass the cache.
    """
    # Sort to canonicalise: ``("mdx", "md")`` and ``("md", "mdx")``
    # MUST share a segment. Empty input is defensive — the CLI
    # validator rejects it earlier, but a programmatic caller might
    # not. Treat it as "default" so we still produce a stable name.
    if not extensions:
        return "ext-default"
    body = "+".join(sorted(extensions))
    if (len(body) <= _MAX_SEGMENT_BODY_LEN
            and all(_SAFE_EXT_RE.match(e) for e in extensions)):
        return f"ext-{body}"
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:10]
    return f"ext-h{digest}"


if __name__ == "__main__":
    sys.exit(main())