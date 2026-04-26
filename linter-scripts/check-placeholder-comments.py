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
    ap.add_argument("--cache-dir", default=None, metavar="DIR",
        help="Enable a content-addressed PASS cache. On a hit (the linter "
             "script + every scanned `.md` hash to the same key as a "
             "previously-cached PASS) the scan is skipped and exit 0 is "
             "returned immediately. Misses run normally and write a fresh "
             "sentinel only on success. Stale or poisoned sentinels are "
             "ignored because the key is recomputed from the working tree "
             "every run.")
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

    intent_verbs = DEFAULT_INTENT_VERBS | {v.lower() for v in args.allow_verb}

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
        cache_key = _compute_cache_key(root, intent_verbs)
        sentinel = Path(args.cache_dir) / f"{cache_key}.pass"
        if sentinel.is_file():
            if not args.json:
                print(f"✅ placeholder-comments: cache hit "
                      f"({cache_key[:12]}…), skipping scan of {args.root}/")
            else:
                print("[]")
            return 0

    violations: list[Violation] = []
    cross_file_bullets: list[tuple[str, int, str]] = []
    for md in iter_markdown_files(root):
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
        ``git diff --name-only --diff-filter=AM <base>...HEAD`` from
        ``repo_root``. The triple-dot syntax compares HEAD against the
        merge-base with ``<base>``, which matches GitHub's PR diff and
        survives force-pushes / rebases on the base branch. The
        ``AM`` filter keeps Added + Modified paths and drops deletes,
        renames, and type changes — none of which can introduce a
        new placeholder violation in the post-state.
      * ``changed_files`` → read newline-delimited paths from the
        given file (``-`` = stdin). Blank lines and ``#`` comments are
        ignored. Useful for CI runners that compute the diff
        themselves (e.g. ``dorny/paths-filter``) or for local testing
        without a git invocation.

    Returned paths are absolute + resolved and filtered to:
      * extension ``.md``
      * residing under ``root`` (so a README change doesn't trigger a
        spec scan)
      * actually present on disk (a Modified path that was reverted
        in a later commit of the same push won't exist)
    """
    raw: list[str] = []
    if diff_base:
        try:
            proc = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=AM",
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
        raw = proc.stdout.splitlines()
    else:
        assert changed_files is not None
        if changed_files == "-":
            raw = sys.stdin.read().splitlines()
        else:
            try:
                raw = Path(changed_files).read_text(encoding="utf-8").splitlines()
            except OSError as e:
                raise RuntimeError(
                    f"--changed-files {changed_files!r} unreadable: {e}"
                ) from e
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


def _compute_cache_key(root: Path, intent_verbs: frozenset[str] | set[str]) -> str:
    """Build a SHA-256 fingerprint of every input that affects the verdict.

    Inputs (in deterministic order):
      1. The absolute, resolved scan root.
      2. The sorted, canonicalised imperative-verb allowlist.
      3. The SHA-256 of the linter script itself (so a logic change
         invalidates every cached PASS automatically).
      4. For every `.md` under the root (sorted by path, dotfiles
         excluded — same filter as ``iter_markdown_files``):
         ``<repo-relative-path>\\0<sha256-of-bytes>\\n``

    Anything outside this set (mtimes, permissions, sibling files,
    environment variables) is intentionally excluded so the key is
    reproducible across machines and CI shards.
    """
    h = hashlib.sha256()
    h.update(b"placeholder-comments-cache-v1\n")
    h.update(f"root={root}\n".encode("utf-8"))
    h.update(("verbs=" + ",".join(sorted(intent_verbs)) + "\n").encode("utf-8"))
    try:
        script_bytes = Path(__file__).resolve().read_bytes()
        h.update(b"script=" + hashlib.sha256(script_bytes).hexdigest().encode() + b"\n")
    except OSError:
        # __file__ unreadable (zipapp / frozen). Fall back to a stable
        # tag so the cache still works, just with coarser invalidation.
        h.update(b"script=unknown\n")
    for md in iter_markdown_files(root):
        try:
            data = md.read_bytes()
        except OSError:
            continue
        rel = str(md.relative_to(root)).encode("utf-8")
        h.update(rel + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n")
    return h.hexdigest()


if __name__ == "__main__":
    sys.exit(main())