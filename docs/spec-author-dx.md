# Spec-Author Developer Experience — Deep Dive

**Author:** Lovable AI · **Date:** 2026-04-26
**Companion to:** `docs/guidelines-audit.md`

---

## Goal

Reduce the time from "I have a spec idea" to "CI is green and the doc is live in the viewer" from ~30 min to under 5 min, without lowering the quality bar set by `linter-scripts/validate-guidelines.py`.

---

## Current author flow (measured pain points)

| Step | Today | Friction |
|------|-------|----------|
| 1. Find the right module / number | Read `01-spec-authoring.md` (475 lines) → `19-gap-analysis.md` → `spec-index.md` | 3 hops, easy to pick a duplicate prefix |
| 2. Write the metadata header | Type from memory or copy from a sibling | Drift in version / date / scoring fields |
| 3. Write content | Free-form markdown | Catches `not`/`no` boolean names, missing alt text, broken links only at commit time |
| 4. Validate | `python linter-scripts/validate-guidelines.py` locally | 8–15 s feedback loop, no in-editor squiggles |
| 5. Sync derived artifacts | 4 commands in a specific order | If skipped → `Drift detected in version.json` in CI |
| 6. Open PR | CI re-runs validator + cross-link checker + spec-tree drift check | Same checks as step 4 — should be a no-op but often catches step-5 mistakes |

---

## Recommended improvements (ranked by leverage)

### 1. `spec/_template.md` (shipped in this PR)
Eliminates step 2 friction. Authors `cp` and edit. Already in repo.

### 2. `00-strictly-avoid-quickref.md` (shipped in this PR)
30-second read; eliminates the most common review-time rejections (boolean negatives, magic strings, swallowed errors, version drift).

### 3. VS Code task — one-button validate
✅ **Shipped** in `.vscode/tasks.json`. Open the Command Palette → *Tasks: Run Task* → pick one of:

- **Spec: Validate** (default test task) — `validate-guidelines.py` + `check-spec-cross-links.py`
- **Spec: Sync derived artifacts** — `sync-spec-tree.mjs` + `sync-version.mjs`
- **Spec: Validate + Sync (full pre-commit)** — runs all four in order
- **Spec: Run all check-* guards** — full `scripts/hooks/pre-commit` mirror; use when CI fails and you can't tell which guard tripped

Reference shape:

```jsonc
{
  "label": "Spec: Validate",
  "type": "shell",
  "command": "python linter-scripts/validate-guidelines.py && python linter-scripts/check-spec-cross-links.py --root spec --repo-root .",
  "group": "test",
  "presentation": { "reveal": "silent", "panel": "dedicated" },
  "problemMatcher": []
}
```

Next iteration: pair with a custom `problemMatcher` once the validator emits `file:line: message` lines so violations land in the Problems panel inline.

### 4. Pre-commit hook expansion
✅ **Shipped** in `scripts/hooks/pre-commit`. The hook now runs three phases in addition to the original `linter-scripts/check-*` guards:

1. **Spec guards** — when staged paths touch `spec/` or `.lovable/`, the hook runs `validate-guidelines.py` and `check-spec-cross-links.py`.
2. **Sync** — `sync-spec-tree.mjs` and `sync-version.mjs` always run.
3. **Auto re-stage** — if the sync phase changes `src/data/specTree.json` or `version.json`, the hook `git add`s them so the commit stays consistent.

Net effect: an author cannot commit a spec change that would later trip the CI drift checker. Step 5 of the current flow becomes a no-op.

Install once per clone:

```bash
bash scripts/hooks/install-hooks.sh
```

### 4b. Per-change validation report

✅ **Shipped** in `scripts/spec-change-report.mjs`. Generates a styled HTML + PDF report scoping validator + cross-link findings to the spec files you actually changed.

```bash
# Default — staged + unstaged + untracked spec files
node scripts/spec-change-report.mjs

# Full repo (useful for baseline / nightly)
node scripts/spec-change-report.mjs --all

# Only what's in the git index (mirrors what the pre-commit hook sees)
node scripts/spec-change-report.mjs --staged

# Only modified-but-unstaged + untracked (in-flight work, no commit yet)
node scripts/spec-change-report.mjs --unstaged

# Skip PDF rendering (HTML only — fastest, no headless browser needed)
node scripts/spec-change-report.mjs --html-only        # alias: --no-pdf

# Choose deep-link scheme for finding rows
node scripts/spec-change-report.mjs --editor vscode    # default; works in VS Code + Cursor
node scripts/spec-change-report.mjs --editor cursor    # native cursor:// scheme
node scripts/spec-change-report.mjs --editor none      # plain text (e.g. for emailing the report)

# Custom output dir
node scripts/spec-change-report.mjs --out ./reports

# Show full usage and exit codes
node scripts/spec-change-report.mjs --help
```

`--all`, `--staged`, and `--unstaged` are mutually exclusive — picking more than one exits with code `3` and prints the usage block.

**Deep links.** When a finding is rendered, both the file header and each `L###` line cell become clickable: clicking opens your editor at the exact line (`vscode://file/<abs-path>:<line>` or `cursor://file/...`). Cross-link findings additionally render an `open target` link that jumps to the destination file the broken reference resolved to.

The default scheme is auto-detected from `$TERM_PROGRAM` (Cursor → `cursor`, otherwise → `vscode`). Override with `--editor`. Use `--editor none` to produce a portable HTML/PDF that contains no editor URIs (useful when sending the report to someone who isn't on your machine).

Output (default `/mnt/documents/`):

- `spec-change-report-<timestamp>.html` — always
- `spec-change-report-<timestamp>.pdf`  — when `wkhtmltopdf` or Chromium is available **and** `--html-only` was not passed

Exit codes: `0` clean · `1` findings · `2` validator crash · `3` invalid CLI flags.


### 5. Live preview wired into the docs viewer
The viewer already reads `src/data/specTree.json`. Add a dev-mode watch (or `bun run sync:watch`) that re-runs `sync-spec-tree.mjs` on `spec/**/*.md` save. Authors see their doc render in the live preview within ~1 s.

### 6. Frontmatter linter (specific to spec metadata)
Today the validator checks header presence but not content. Add micro-rules:

- `Version` is semver
- `Updated` is ISO `YYYY-MM-DD` and ≥ git's last-modified date
- `AI Confidence` ∈ {Production-Ready, High, Medium, Low, Draft}
- `Ambiguity` ∈ {None, Low, Medium, High, Critical}
- Exactly one H1
- Scoring table present when file is `00-overview.md`

Each rule is a 5-line Python check. Output format `path:line:col: SPEC-XXX message` so editors and CI both render it identically.

### 7. Auto-bump helper
`scripts/bump-spec.mjs <path> [patch|minor|major]` that:

- Bumps `Version` in the file's frontmatter
- Updates `Updated` to today
- Re-runs the three sync scripts
- Stages the diff

Removes the most common "I forgot to bump" PR comment.

### 8. Scaffold command
`scripts/new-spec.mjs <module-name> <file-name>`:

- Picks the next free numeric prefix in the chosen module
- Copies `spec/_template.md`
- Pre-fills title, version `1.0.0`, today's date
- Adds an entry stub to `99-consistency-report.md`
- Echoes the file path so the author can `code $(...)` straight into it

### 9. CODE-RED-024 in-editor lint for TS / TSX
Authors of *code* (not specs) keep tripping on bare `true` / `false` positional args. Add an ESLint rule (`no-restricted-syntax` with a tight selector) that flags `CallExpression > Literal[value=true|false]` outside test files. The fix is "import a named flag from `@/constants/boolFlags`."

### 10. Cross-link auto-fix
`check-spec-cross-links.py` reports broken links. A `--fix` flag that uses fuzzy matching against existing files would resolve 80 % of typos in one keystroke.

---

## Suggested rollout

| Wave | Items | Cost | Payoff |
|------|-------|------|--------|
| **Now (this PR)** | 1, 2 | shipped | Authors can write a valid spec without reading the long-form guide |
| **Wave 2 (this PR)** | 3, 4 | shipped | One-button validate + commit hook covers most CI failures locally |
| **Following sprint** | 5, 6 | ~2 days | Real-time preview + frontmatter linter |
| **Backlog** | 7, 8, 9, 10 | varies | Polish — every item independently shippable |

---

## What I'm explicitly not recommending

- **Web-based spec editor.** The Monaco-based editor in `MonacoMarkdownEditor.tsx` is sufficient for previewing; writing happens in the author's IDE. A custom web editor adds maintenance burden without a clear payoff.
- **AI-generated specs from prose prompts.** Spec quality depends on author intent. AI-assisted scaffolding (item 8) is fine; AI-authored specs are not.
- **Loosening the validator.** Every rule it enforces was added because it failed silently before. Keep the gate strict; lower the friction *around* the gate instead.

---

*See `docs/guidelines-audit.md` for the audit and the 3 quick wins shipped alongside this doc.*