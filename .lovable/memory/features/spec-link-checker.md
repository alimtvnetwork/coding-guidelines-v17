---
name: spec-link-checker
description: SPEC-LINK-001 markdown cross-link checker — fence-aware, GitHub-flavored slugs (no hyphen collapse), inline-identifier filter, mem:// skip, warning-level SARIF.
type: feature
---
SPEC-LINK-001 lives at `linters-cicd/checks/spec-links/markdown.py` with shared logic in `linters-cicd/checks/_lib/markdown_links.py`.

**What it checks:**
- Every relative markdown link `[text](path.md)` resolves to an existing file
- Every anchor `[text](path.md#slug)` matches a heading slug in the target file
- Pure self-anchors `[text](#slug)` match a heading in the current file

**What it skips:**
- External links: `http://`, `https://`, `mailto:`, `tel:`, `ftp://`, `javascript:`, **`mem://`** (Lovable memory pseudo-protocol)
- Fenced code blocks (` ``` ` and `~~~`)
- Inline-identifier patterns like `[val](AppError)` — no `/`, no real extension, identifier-shaped
- Setext headings (`Foo\n===`) — project uses ATX exclusively

**Slug algorithm (GitHub-flavored):**
1. Lowercase
2. Strip everything except `[a-z0-9 _-]`
3. Replace spaces with hyphens
4. **Do NOT collapse consecutive hyphens** — `Phase 1 — AI` → `phase-1--ai-context-layer` (em-dash strips, both surrounding spaces become hyphens)
5. Disambiguate duplicate slugs with `-1`, `-2`, ... suffix
6. Strip leading/trailing hyphens

The "no collapse" rule is critical — collapsing was a v1.0 bug that produced false positives on every "X — Y" / "X & Y" heading and masked ~10 real anchor breakages.

**Severity:** warning (does not block CI). Registered in `linters-cicd/checks/registry.json` as `SPEC-LINK-001`.

**Run:** `python3 linters-cicd/checks/spec-links/markdown.py --path spec --format text`

**Current baseline (v4.18.0):** 17 warnings — all genuine intra-doc anchor drift in `spec-index.md`, `consolidated-review-guide.md`, `01-cross-language/13-strict-typing.md`. TOC section-number anchors that no longer match heading text after rewrites. Needs per-file content review, not mechanical fix.
