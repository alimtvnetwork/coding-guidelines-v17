---
name: spec-link-checker
description: SPEC-LINK-001 markdown cross-link checker — fence-aware, GitHub-flavored slugs, inline-identifier filter, warning-level SARIF.
type: feature
---
SPEC-LINK-001 lives at `linters-cicd/checks/spec-links/markdown.py` with shared logic in `linters-cicd/checks/_lib/markdown_links.py`.

**What it checks:**
- Every relative markdown link `[text](path.md)` resolves to an existing file
- Every anchor `[text](path.md#slug)` matches a heading slug in the target file
- Pure self-anchors `[text](#slug)` match a heading in the current file

**What it skips:**
- External links: `http://`, `https://`, `mailto:`, `tel:`, `ftp://`, `javascript:`
- Fenced code blocks (` ``` ` and `~~~`)
- Inline-identifier patterns like `[val](AppError)` — no `/`, no real extension, identifier-shaped
- Setext headings (`Foo\n===`) — project uses ATX exclusively

**Slug algorithm (GitHub-flavored):**
1. Lowercase
2. Strip everything except `[a-z0-9 _-]`
3. Replace spaces with hyphens, collapse repeats
4. Disambiguate duplicates with `-1`, `-2`, ... suffix

**Severity:** warning (does not block CI). Registered in `linters-cicd/checks/registry.json` as `SPEC-LINK-001`.

**Run:** `python3 linters-cicd/checks/spec-links/markdown.py --path spec --format text`

**Known baseline:** 54 real cross-link warnings exist in `spec/` as of v4.17.0 — mostly stale renumbering in `14-update/` and `mem://` resolver gaps. Cleaning these up is a follow-up task, not blocked by the linter.
