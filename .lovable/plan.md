# Current Plan

**Version:** 4.24.0
**Updated:** 2026-04-24 (session 2)

---

## v4.24.0 — Batch close 11 plan items + Release & Migration UI rewrite + slug rebrand

**Scope:** Single-pass closure of the longest-pending tasks plus a hard UI lock per direct user instruction.

### Done
- **B10** `--strict` flag in `linters-cicd/scripts/load-config.py` — `KNOWN_RUN_KEYS` allow-list rejects unknown TOML keys when set.
- **B11** `--split-by severity` in `linters-cicd/run-all.sh` — emits `*.{error,warning,note}.sarif` siblings.
- **B8** `--total-timeout` wall-clock watchdog + per-file 2 s parse timeouts via new `linters-cicd/checks/_lib/per_file_timeout.py` (SIGALRM); applied to `file-length/universal.py`.
- **B7** PHP plugins for CODE-RED-001..004 — `nested-if/php.py`, `boolean-naming/php.py`, `magic-strings/php.py`, `function-length/php.py` registered in `checks/registry.json`.
- **B2** Playwright landing smoke at `tests/e2e/landing.spec.ts`.
- **09** Offline E2E `tests/installer/check-run-slides-help.sh` — verifies `./run.sh slides` dispatch table.
- **10** Offline E2E `tests/installer/check-install-folders-config.sh` — asserts `install-config.json` declares all 4 canonical folders.
- **B6** Date-bumped `99-consistency-report.md` across 13 spec subfolders.
- **B5** Effective-Score waiver section added to `spec/health-dashboard.md`.
- **12** `spec/04-database-conventions/02-schema-design.md` §6 pinned to naming v3.5.0.
- **UI** `src/components/landing/InstallSection.tsx` — collapsed legacy install list to **two** Release & Migration cards (Windows PowerShell, macOS/Linux Bash). Removed all "skip latest probe" variants per user lock-in.
- **Rebrand** `release-artifacts/release-install.{ps1,sh}` → `alimtvnetwork/coding-guidelines-v17`.
- **Bumps** `package.json` 4.21.0 → 4.24.0; `linters-cicd/VERSION` 3.20.0 → 3.22.0.

### Verification
- `npx vite build` — passes.
- Pending real-repo run of orchestrator with `--strict --total-timeout 60 --split-by severity` (tracked in suggestions).
- Playwright spec needs CI wiring (tracked in suggestions).

### User locks (do not regress)
1. Release & Migration UI: exactly two cards, no skip-probe variants. *"I don't want to discuss this ever again."*
2. Canonical slug `alimtvnetwork/coding-guidelines-v17` everywhere — full `grep -rn` sweep after every rebrand. *"you didn't do all replace in the repo"* — never assume partial coverage is enough.

---

## v4.21.0 — `exclude-paths` Glob Support in `.codeguidelines.toml` + walker.py (Task B9)

**Scope:** Add user-controllable path exclusion across the entire linter pipeline so projects can skip vendored/generated/legacy directories without per-file suppressions. Glob syntax is fnmatch-style (`vendor/**`, `**/*.gen.go`).

### Architecture
- **walker.py** (`checks/_lib/walker.py`): Added optional `exclude_globs: Sequence[str] | None` parameter to `walk_files()` and `walk_files_middle_out()`. Matched against repo-relative posix paths. Directory subtrees are pruned at `os.walk` time so excluded trees pay zero recursion cost. Backward-compatible — defaults to None.
- **cli.py** (`checks/_lib/cli.py`): Added `--exclude-paths` flag (CSV) to the shared `build_parser()` so every check inherits it automatically. New helper `parse_exclude_paths(raw)` splits CSV → clean glob list.
- **load-config.py** (`scripts/load-config.py`): Reads `[run].exclude-paths` from `.codeguidelines.toml` and emits `EXCLUDE_PATHS=...` line. CLI flag overrides TOML.
- **run-all.sh**: New `--exclude-paths` flag, threads through to load-config and to every check invocation. `EXCLUDE_PATHS` exported for xargs subshells. Logged in the run banner.
- **18 check scripts patched** (bulk script with balanced-paren matcher): each `walk_files(args.path, EXTS)` call now becomes `walk_files(args.path, EXTS, exclude_globs=_globs)` where `_globs = parse_exclude_paths(args.exclude_paths)` is injected after `args = ...parse_args()`.

### Done
- `linters-cicd/checks/_lib/walker.py` — fnmatch glob support, directory pruning, helper functions.
- `linters-cicd/checks/_lib/cli.py` — `--exclude-paths` flag + `parse_exclude_paths()` helper.
- `linters-cicd/scripts/load-config.py` — TOML key `[run].exclude-paths`, CLI override precedence.
- `linters-cicd/run-all.sh` — flag parsing, banner line, threading to every check.
- 18 check scripts patched mechanically:
  - boolean-column-negative/{go,sql}.py, boolean-naming/{go,typescript}.py
  - file-length/universal.py, free-text-columns/sql.py, function-length/{go,typescript}.py
  - magic-strings/{go,typescript}.py, missing-desc/sql.py, nested-if/{go,typescript}.py
  - no-else-after-return/{go,typescript}.py, positive-conditions/{go,typescript}.py
  - spec-links/markdown.py
- 2 new test files (11 new tests):
  - `tests/test_walker_exclude_globs.py` — 8 tests covering directory exclusion, filename globs, multi-glob combination, no-op behavior, extension filter coexistence, middle-out compatibility.
  - `tests/test_load_config_exclude_paths.py` — 3 tests for default empty, TOML pickup, CLI-overrides-TOML precedence.
- `linters-cicd/VERSION` 3.19.0 → 3.20.0.
- `package.json` 4.20.0 → 4.21.0.

### Verification
- **102/102 tests pass** (was 91 before).
- `bash run-all.sh --path spec --rules SPEC-LINK-001 --exclude-paths "spec/14-update/**"` → `✅ clean`, banner shows `exclude-paths: spec/14-update/**`.
- All 18 check scripts parse cleanly (AST validation pass).
- Backward-compat: existing invocations without `--exclude-paths` work identically.

### Migration notes for users
Add to project's `.codeguidelines.toml`:
```toml
[run]
exclude-paths = [
    "vendor/**",
    "**/*.gen.go",
    "third_party/**",
]
```
Or pass on CLI: `--exclude-paths "vendor/**,**/*.gen.go"`.

---

## v4.20.0 — SPEC-LINK-001 Wired into `run-all.sh` + Regression Lock (Task: orchestrator wiring)

**Scope:** Confirm SPEC-LINK-001 is dispatched by the central orchestrator (`linters-cicd/run-all.sh`), verify it runs in the full CI sweep, and add a dedicated integration test so the wiring cannot silently regress.

### Investigation
- Read `run-all.sh` end-to-end. Discovered it is **already fully registry-driven** (lines 127–142): the dispatch loop iterates every `(rule_id, lang, script)` triple from `checks/registry.json` with no hardcoded rule list. SPEC-LINK-001 was therefore implicitly wired since v4.17.0.
- Verified empirically:
  - `bash run-all.sh --path spec --rules SPEC-LINK-001` → `✅ clean`, exit 0.
  - Full sweep (no rule filter) shows SPEC-LINK-001/markdown listed alongside the other 17 (rule, lang) pairs and exits clean for that rule.
- TS findings on `spec/` are unrelated noise (TS rules running on a markdown-only path) — not in scope.

### Done
- Created `linters-cicd/tests/test_runall_spec_link_wiring.py` — 2 regression tests:
  1. `test_registry_lists_spec_link_markdown` — asserts `registry.json` carries SPEC-LINK-001/markdown at error level.
  2. `test_runall_dispatches_spec_link_and_exits_clean` — invokes `run-all.sh --rules SPEC-LINK-001 --path spec` as a subprocess and asserts `✅ clean` + exit 0.
- Both tests guard against three failure modes: registry deletion, script removal, dispatch-loop regression (rule filter, language gate).
- Test count: **91/91 pass** (was 89/89). Codegen determinism still green.
- Bumped `linters-cicd/VERSION` 3.18.0 → 3.19.0.

### Why this matters
The error-level promotion in v4.19.0 only has teeth if SPEC-LINK-001 actually runs in CI. v4.20.0 makes that contract testable and self-healing — if anyone accidentally deletes the registry entry or breaks the dispatch loop, CI now fails loudly.

---

## v4.19.0 — SPEC-LINK-001 Zero Baseline + Promotion to Error Level (Task #11b)

**Scope:** Drive SPEC-LINK-001 baseline from 17 → 0, then promote the rule from `warning` → `error` so future broken cross-links fail CI.

### Done

**Scope:** Drive SPEC-LINK-001 baseline from 17 → 0, then promote the rule from `warning` → `error` so future broken cross-links fail CI.

### Done
- **Diagnosis:** All 17 remaining findings shared the same root cause — hand-written anchors used single-hyphen slugs but the actual headings contain `&` or em-dashes, which (per GitHub-flavored slugify) collapse to **double-hyphen** slugs. Examples: `1. Workflow & Process` → `1-workflow--process`, not `1-workflow-process`.
- **Fix script:** `/tmp/fix-anchors.py` with 17 explicit `(file, search, replace)` triples — no regex, just exact-string substitution. Each fix is unique enough to avoid collateral matches. Verified by re-running the linter.
- **17/17 fixes applied** across 9 files:
  - `spec-index.md` (×2) — Self-Update & App Update, App Design System & UI
  - `02-coding-guidelines/consolidated-review-guide.md` (×5) — sections 1, 2, 3, 5, 6 with `&`
  - `02-coding-guidelines/01-cross-language/01-issues-and-fixes-log.md` (×1) — Boolean & Negation Violations
  - `02-coding-guidelines/01-cross-language/11-key-naming-pascalcase.md` (×1) — `1.2 — Abbreviation Standard`
  - `02-coding-guidelines/01-cross-language/13-strict-typing.md` (×3) — `7.2`, `12.`, `6.1` headings
  - `02-coding-guidelines/01-cross-language/02-boolean-principles/00-overview.md` (×1)
  - `02-coding-guidelines/01-cross-language/02-boolean-principles/02-guards-and-extraction.md` (×1) — Rule 3 with em-dash
  - `02-coding-guidelines/01-cross-language/02-boolean-principles/03-parameters-and-conditions.md` (×1) — Rule 2.8
  - `02-coding-guidelines/01-cross-language/15-master-coding-guidelines/03-code-style-and-errors.md` (×1)
  - `16-generic-release/07-known-issues-and-fixes.md` (×1) — Issue #5 with em-dash
- **Promoted SPEC-LINK-001 from warning → error**:
  - `linters-cicd/checks/registry.json` — `level: warning` → `level: error`
  - `linters-cicd/checks/spec-links/markdown.py` — Finding `level="warning"` → `level="error"`, tool version `1.0.0` → `1.1.0`
  - Linter now exits 1 on any new broken cross-link, blocking CI.
- Bumped `linters-cicd/VERSION` 3.17.0 → 3.18.0.

### Verification
- SPEC-LINK-001 scan: **`✅ no findings` (exit 0)** across all 612 spec files.
- 89/89 unit tests pass.
- Codegen determinism harness still green.
- All 3 installer harnesses still green.

### Three-version SPEC-LINK-001 arc — recap
- **v4.17.0**: linter created, 54 findings baseline.
- **v4.18.0**: slugify bugfix + mechanical renumbering, 54 → 17.
- **v4.19.0**: anchor cleanup + promote to error, 17 → 0.

---

## v4.18.0 — SPEC-LINK-001 Baseline Cleanup + Slugify Bugfix (Task #11-followup)

**Scope:** Drive the SPEC-LINK-001 baseline from 54 → 17 warnings, fix a slugify-collapse bug that was masking ~10 real anchor breakages, and add `mem://` to the external-prefix skip list.

### Done
- **Slugify bugfix** (`_lib/markdown_links.py`): the GitHub algorithm does **not** collapse consecutive hyphens. Removed the `re.sub(r"-+", "-", text)` line. Headings like `Phase 1 — AI Context Layer` now correctly slug to `phase-1--ai-context-layer` (em-dash strips to empty, both surrounding spaces become hyphens). The previous collapse turned every "X — Y" / "X & Y" anchor into a false positive **and** masked ~10 real anchor mismatches. Tested by `TestSlugify.test_em_dash_preserves_double_hyphen` + `test_ampersand_preserves_double_hyphen` (regression locks).
- **`mem://` added to `_EXTERNAL_PREFIXES`** — Lovable memory pseudo-protocol is referenced from spec prose but never resolves on disk. Eliminated 2 false positives. Test added in `TestExtractLinks.test_external_links_skipped`.
- **Mechanical 14-update renumbering** — wrote `/tmp/fix-spec-links.py` to remap 9 stale basenames (`07-release-assets.md` → `13-release-assets.md`, ..., `16-update-command-workflow.md` → `22-update-command-workflow.md`). Touched 9 files inside `spec/14-update/`. Removed 32 broken-link findings.
- **13-generic-cli overview rename** — `01-overview.md` → `00-overview.md` across 3 files. Removed 3 findings.
- **02-coding-guidelines/06-cicd-integration/00-overview.md** — fixed depth: `../17-consolidated-guidelines/...` → `../../17-consolidated-guidelines/...`. Removed 1 finding.
- **8 placeholder Mermaid (.mmd) diagram stubs** created under `spec/13-generic-cli/images/` and `spec/14-update/images/`. Each contains a minimal valid Mermaid skeleton + `%% TODO` comment so a human author can fill in the real diagram later. Removed 9 broken-link findings without inventing prose content.
- **Removed dead `MERGE-PROPOSAL.md` row** from `spec/14-update/00-overview.md` (line 108) — that file was never authored. Cosmetic table cleanup.

### Net result
- SPEC-LINK-001 warnings: **54 → 17** (-37, including the 9 newly-exposed by the slugify fix).
- The 17 remaining are all genuine intra-doc anchor drift in `spec-index.md`, `consolidated-review-guide.md`, `01-cross-language/13-strict-typing.md`, etc. — TOC entries that no longer match section numbering after rewrites. These need per-file content review (see follow-up #11b).

### Verification
- 89/89 unit tests pass (was 87 — +2 net for slugify regression locks + mem:// case).
- Codegen determinism harness still green.
- All 3 installer harnesses still green.
- Bumped `linters-cicd/VERSION` 3.16.0 → 3.17.0.

---

## v4.17.0 — SPEC-LINK-001 Cross-Reference Link Checker (Task #11)

**Scope:** Catch broken cross-references (file paths + heading anchors) across the entire `spec/` tree before they ship. Produces SARIF, integrates with the existing `_lib/` infrastructure, and exposes 54 real link-rot issues already present in the spec.

### Done
- **#11**: New shared library `linters-cicd/checks/_lib/markdown_links.py` (200 LOC):
  - `extract_links()` — fence-aware (` ``` ` / `~~~`), title-attr aware, external-prefix skip (`http`/`https`/`mailto`/`tel`/`ftp`/`javascript`).
  - `extract_heading_slugs()` — GitHub-flavored slug algorithm (lowercase, strip non-`[a-z0-9 _-]`, hyphenate spaces, `-1`/`-2` disambiguation for duplicates). ATX headings only (matches project standard).
  - `check_file()` — resolves every relative link; for `.md` targets with anchors, validates against the cached heading-slug set of the target file.
  - `_looks_like_inline_identifier()` — heuristic that filters out `[val](AppError)`-style prose patterns (no `/`, no real extension, identifier-shaped) to eliminate the dominant false-positive class. Halved scan output from 100 → 54 findings.
  - Per-file slug cache so a target file is parsed exactly once even when 50 sources link into it.
- New check `linters-cicd/checks/spec-links/markdown.py` (warning-level SARIF). Tool name `coding-guidelines-spec-links`, version `1.0.0`. Inherits `--path`/`--format`/`--output`/`--version` from `_lib/cli.py`.
- Registered as `SPEC-LINK-001` in `linters-cicd/checks/registry.json` (level: warning, language: markdown).
- New test file `linters-cicd/tests/test_markdown_links_lib.py` — 18 tests across 3 suites:
  - `TestExtractLinks` (6) — anchors, pure-anchor, external skip, fenced-code immunity (both ` ``` ` and `~~~`), title-attr handling.
  - `TestSlugify` (4) — basic, punctuation strip, duplicate disambiguation, fence-isolation.
  - `TestCheckFile` (8) — valid cross-file anchor, missing target file, missing target anchor, valid + broken self-anchor, inline-identifier filter, real `.md` link still validated, slug-cache reuse.
- Bumped `linters-cicd/VERSION` 3.15.0 → 3.16.0.

### Verification
- 87/87 unit tests pass (was 69 — +18 net from the new lib tests).
- Real scan against `spec/` surfaces 54 SPEC-LINK-001 warnings — all legitimate (stale renumbering in `14-update/`, missing `mem://` resolver, broken self-anchors after section rewrites). These are documented as **deliberate non-blocker findings**; SPEC-LINK-001 is warning-level and does not fail CI.
- All 3 installer harnesses still green (153 assertions).
- Codegen determinism harness still green.
- BOOL-NEG-001 v2 fixture still produces exactly 5 findings (no regression).

### Unblocks
- **#11 follow-up** — fix the 54 real cross-link warnings, file-by-file (separate cleanup pass).

---

## v4.16.0 — BOOL-NEG-001 v2: Two-Tier Detection + Replacement Hints (Task #07)

**Scope:** Extend BOOL-NEG-001 from a single-tier "Not/No" check to a two-tier scanner that also catches `Cannot*`/`Dis*`/`Un*` roots, and embed canonical-rename suggestions in every finding. Backed by the codegen inversion table for hint determinism.

### Done
- **#07**: New shared library `linters-cicd/checks/_lib/boolean_naming.py` — single source of truth for forbidden regex, suspect regex, allow-list, and hint generator. Imports the codegen `_FORWARD` table so linter ↔ codegen stay locked together by code, not just convention.
- Tier 1 (error) — `Is/Has + Not/No + UpperCamel`. Same as v1; hints now generated.
- Tier 2 (warning) — `Cannot*`, `(Is|Has)?Dis(abled|allowed|connected)*`, `(Is|Has)?Un[a-z]+...`. Allow-list (10 names) takes precedence in BOTH tiers.
- Replacement hints (4 strategies, in priority order):
  1. `IsNot*` / `HasNo*` → strip the negation (`IsNotActive` → `IsActive`)
  2. Inversion table direct lookup (`IsInactive` → `IsActive`, `HasNoLicense` → `HasLicense`)
  3. `Cannot*` → `Can*` (`CannotEdit` → `CanEdit`)
  4. None when no safe rename exists (suppresses confusing "NotNot" fallbacks)
- Refactored `sql.py` and `go.py` to consume the shared library. Both bumped to tool_version `2.0.0`. SARIF emit unchanged so all downstream consumers (run-all, GH Code Scanning) keep working.
- Added Tier 2 walkers to Go scanner: `scan_struct_tags_v2`, `scan_embedded_sql_v2` (4-tuple return adding tier). v1 walkers preserved as filtered wrappers so the existing test suite + shim keep working without changes.
- `boolean_column_negative_shim.py` now consumes the shared library directly (no more dependency on the SQL module's internals).
- Flipped 2 boundary tests (`TestOutOfScope` → `TestSuspectTier`) in both SQL and Go suites to assert v2 contract: Cannot/DisabledFlag/UnreadStatus now produce exactly one suspect-tier warning; allow-listed `IsDisabled` stays clean.
- New test file `test_boolean_naming_lib.py` — 17 tests across 7 suites covering Tier 1, Tier 2, allow-list precedence in both tiers, no-tier-overlap, all 4 hint strategies, format_message contract, and codegen lock-step assertion.

### Verification
- 69/69 unit tests pass (was 49 — +20 net from new lib tests + flipped boundary tests).
- E2E SQL fixture (8-column table) produces exactly: 2 errors with hints (`IsNotActive`→`IsActive`, `HasNoLicense`→`HasLicense`), 3 warnings (`CannotEdit`→`CanEdit`, `DisabledFlag` no-hint, `UnreadCount` no-hint), and 0 findings for `IsDisabled` + `IsActive` (correct).
- Codegen determinism harness still green — Rule 9 fixtures unchanged.
- All 3 installer harnesses still green (153 assertions).

---

## v4.15.0 — Codegen Wired Into CI (Task #05)

**Scope:** Re-run inverted-field codegen on every CI build and fail loudly on any drift from the committed fixtures. Backed by the bijection + determinism guarantees proven in v4.14.0 (#04).

### Done
- **#05**: New harness under `linters-cicd/codegen/`:
  - `fixtures/sources/User.{go,php,ts}` — 3 hand-written sources covering canonical-table inverse (`IsActive`→`IsInactive`), fallback (`HasLicense`→`HasNoLicense`), and multi-block emit (User + Subscription).
  - `fixtures/expected/User.generated.{go,php,ts}` — committed artifacts (104 lines total) regenerated from sources via the script below.
  - `scripts/regen-codegen-fixtures.sh` — single-command rebuild of expected/ when the inversion table or any emitter intentionally changes.
  - `scripts/verify-codegen-determinism.sh` — re-emits into a temp dir, compares byte-for-byte using a portable Python `difflib` (no `diff` binary dependency), prints unified diff on drift, exits 1.
- Wired into `.github/workflows/ci.yml` lint job as the step **immediately after** `test:linters` so unit-level guarantees and end-to-end drift detection run together.
- Added `npm run codegen:verify` and `npm run codegen:regen` for local use.
- Added `linters-cicd/tests/test_codegen_determinism_harness.py` (5 tests) — exercises the verify script as a black box: happy path, mutated expected/Go fails, mutated expected/PHP fails, regen idempotency.

### Verification
- 50/50 unit tests pass (was 45 — 5 new harness tests).
- `verify-codegen-determinism.sh` runs cleanly on committed fixtures (go=25 lines, php=42 lines, ts=37 lines).
- Drift simulation: mutating `User.generated.go` makes verify exit 1 with a unified diff in stdout (validated in test).
- Idempotency: two back-to-back regens produce byte-identical files.
- All 3 installer harnesses still green (153 assertions).

### Unblocks
- **#07** (extend BOOL-NEG-001 regex to `Cannot`/`Dis-`/`Un-` roots) — codegen is now safely refactorable end-to-end.

---

## v4.14.0 — Codegen Inversion-Table Round-Trip Tests (Task #04)

**Scope:** Lock the Rule 9 codegen contract — every (positive, negative) pair in the inversion table is bijective and the BOOL-NEG-001 allow-list stays in lock-step with codegen's canonical inverses.

### Done
- **#04**: Added `linters-cicd/tests/test_codegen_inversion_table.py` — 14 tests across 6 suites:
  - `TestExplicitTableBijection` — `invert(invert(x)) == x` in BOTH directions for every entry; `_TABLE` size = 2× `_FORWARD` (no merge collisions).
  - `TestNoCollisions` — unique negatives, unique positives, zero positive↔negative overlap.
  - `TestNoSelfInverse` — no entry maps to itself.
  - `TestFallbackContract` — pins the documented one-way fallback (`IsFoo→IsNotFoo`, `IsNotFoo→IsNotNotFoo` — no double-negative collapse). Covers `Is`/`Has`/non-`Is*`/`Has*` paths and short edge cases.
  - `TestBoolNegAllowListLockstep` — every BOOL-NEG-001 allow-listed name appears as a value in `_FORWARD`, guaranteeing linter & codegen never drift.
  - `TestDeterminism` — repeated invocations stable.

### Verification
- 45/45 unit tests pass (13 SQL + 18 Go + 14 inversion-table) in 0.004s.
- All 3 installer harnesses still green (153 assertions).
- Lock-step assertion confirmed BOOL-NEG-001 allow-list ⊂ canonical inverses; future drift fails CI loudly.

### Unblocks
- **#05** (wire codegen into CI with `git diff --exit-code` after regen) — round-trip stability now proven, so determinism check is safe.

---

## v4.13.0 — Go-Aware BOOL-NEG-001 (Task #02)

**Scope:** Add a Go scanner for BOOL-NEG-001 so embedded migrations and ORM struct definitions are covered alongside `.sql` files.

### Done
- **#02**: Added `linters-cicd/checks/boolean-column-negative/go.py` with two complementary scanners:
  - **Struct-tag scanner** — walks `type X struct { ... }` blocks, inspects `bool`/`*bool` fields. Priority: `gorm:"column:..."` → `db:"..."` → field name. Handles snake_case ↔ PascalCase normalization.
  - **Embedded-SQL scanner** — finds back-tick raw strings containing `CREATE TABLE` and runs the same regex/allow-list as `sql.py`.
- Allow-list (10 names) and `NEG_PREFIX_RE` kept in lock-step with `sql.py`.
- Registered `"go": "checks/boolean-column-negative/go.py"` in `checks/registry.json`.
- Added `boolean_column_negative_go_shim.py` (importlib loader for hyphenated folder).
- Added `tests/test_boolean_column_negative_go.py` — 18 stdlib unittest cases across 8 suites covering snake/pascal conversion, struct field name, db-tag, gorm-tag priority, allow-list lock-step, embedded SQL, mixed sources, and v1 boundary.

### Verification
- 31/31 unit tests pass (13 SQL + 18 Go).
- E2E pipeline smoke test (`run-all.sh --languages go --rules BOOL-NEG-001`) on a realistic Go fixture detected exactly 5 findings across all 4 detection paths (struct-field, db-tag, gorm-tag, embedded-sql).
- Allow-list respected; clean Go file produced 0 findings.
- v1 boundary holds: Cannot/Disabled prefixes correctly out-of-scope.
- All 3 installer harnesses still green (153 assertions).

---

## v3.98.0 — Lock README Install Order to UI

**Scope:** Root README install experience only. Keep install commands as single-line copy/paste commands and mirror the on-site install UI order exactly.

**Scope:** Root README install experience only. Keep install commands as single-line copy/paste commands and mirror the on-site install UI order exactly.

### Problem

The root `readme.md` drifted from the actual install UI:

- the top install block did not clearly include the full named-bundle split the user expects,
- bundle installers lived too far down the document,
- prior README renderings mixed comments and multiple commands in one visible code block,
- the CI check only enforced install-section-first and one-line fences, but not the required top-level order of `Install in One Line` → `Bundle Installers` → `Table of Contents`.

### Fix

- Move `Bundle Installers` directly under `Install in One Line` at the top of `readme.md`.
- Keep every install fence to exactly one command line with platform headers outside the fence.
- Mirror the UI bundle order exactly: `error-manage`, `splitdb`, `slides`, `linters`, `cli`, `wp`, `consolidated`.
- Remove the duplicate lower README bundle section to prevent drift and confusion.

### Enforcement

Strengthen `linter-scripts/check-readme-install-section.py` so CI now also fails when:

1. `Bundle Installers` is missing,
2. `Bundle Installers` is not immediately after `Install in One Line`,
3. `Bundle Installers` appears after the Table of Contents.

### Memory

Reinforce `mem://constraints/install-command-formatting` and add the reminder to `.lovable/memory/index.md` so future README edits preserve the top install layout.

### Files Touched

- `readme.md` — move bundle installers to top and remove duplicate lower block
- `linter-scripts/check-readme-install-section.py` — validate bundle section order too
- `.lovable/memory/constraints/install-command-formatting.md` — clarify top-of-README ordering rule
- `.lovable/memory/index.md` — add reminder entry
- `.lovable/plan.md` — this entry
- `package.json` — bump 4.2.0 → 4.3.0
- Run `npm run sync`

---

## Active Work (carried over)



## Active Work

| # | Task | Status | Priority |
|---|------|--------|----------|
| 01 | Smoke-test BOOL-NEG-001 in `run-all.sh` end-to-end | ⏳ Pending | Medium |
| 02 | Add Go-aware `checks/boolean-column-negative/go.py` (parse `db:""` in `embed.FS`) | ⏳ Pending | Medium |
| 03 | Unit tests for BOOL-NEG-001 (`checks/_tests/boolean_column_negative_test.py`) | ⏳ Pending | Medium |
| 04 | Round-trip tests for codegen inversion table (`linters-cicd/codegen/_tests/`) | ⏳ Pending | Medium |
| 05 | Wire codegen into CI (`run-all.sh` → `git diff --exit-code`) | ⏳ Pending | Medium |
| 06 | Linter for missing `Description` / `Notes` / `Comments` columns (Rules 10–12) | ⏳ Pending | Medium |
| 07 | Strengthen BOOL-NEG-001 with replacement hints (`HasNoAccess` → `IsUnauthorized`, etc.) | ⏳ Pending | Low |
| 08 | Cross-link link-checker over `spec/` (Rule 9 / BOOL-NEG-001 / codegen-README anchors) | ⏳ Pending | Low |
| 09 | End-to-end test: `./run.sh slides` on a clean checkout (verify build + browser open) | ⏳ Pending | Medium |
| 10 | End-to-end test: `install.sh` on a clean dest dir pulls all 4 folders incl. `linters-cicd/` | ⏳ Pending | Medium |
| 11 | Implement `release-install.ps1` per spec `14-update/25-release-pinned-installer.md` (v1.0.0) | ✅ Done (4.6.0) | High |
| 12 | Implement `release-install.sh` per spec `14-update/25-release-pinned-installer.md` (v1.0.0) | ✅ Done (4.6.0) | High |
| 13 | Wire release-install.* into `release.sh` / `release.ps1` (sed VERSION/REPO, ship as release assets) | ✅ Done (4.7.0) | High |
| 14 | Add release-pinned one-liner block to GitHub Release body template | ✅ Done (4.7.0) | Medium |
| 15 | Test harness asserting NO call to `api.github.com/.../releases/latest` from release-install.* | ✅ Done (4.5.0) | Medium |

---

## Completed Plans (Historical)

| # | Task | Date |
|---|------|------|
| 01 | Coding guidelines consolidation (5 sources → 1, 6 phases, 85 files) | 2026-04-02 |
| 02 | Phase 2 content overlap audit | 2026-04-03 |
| 03 | Phase 3 consolidated structure design | 2026-04-03 |
| 04 | Spec viewer UI — syntax highlighting | 2026-04-05 |
| 05 | Light/dark syntax theme toggle | 2026-04-05 |
| 06 | Persistent syntax theme preference | 2026-04-05 |
| 07 | Discriminated union + enum pattern for toast | 2026-04-05 |
| 08 | TypeScript standards spec update | 2026-04-05 |
| 09 | Validate-guidelines — zero violations (95 files) | 2026-04-05 |
| 10 | Spec cross-reference validation | 2026-04-05 |
| 11 | specTree.json regeneration (371 files) | 2026-04-05 |
| 12 | Sidebar folder structure restoration | 2026-04-05 |
| 13 | Download folder as ZIP | 2026-04-05 |
| 14 | Dashboard data regeneration | 2026-04-16 |
| 15 | Consistency report update | 2026-04-16 |
| 16 | Folder structure doc update | 2026-04-16 |
| 17 | Version bump — all 319 spec files + UI to v3.1.0 | 2026-04-16 |
| 18 | Placeholder consolidated guidelines 11/12/13 filled | 2026-04-16 |
| 19 | Expanded `01-spec-authoring.md` 90% → 95% | 2026-04-16 |
| 20 | Expanded `16-app-design-system-and-ui.md` 88% → 93% | 2026-04-16 |
| 21 | Created `22-app-database.md` | 2026-04-16 |
| 22 | Updated AI onboarding prompt | 2026-04-16 |
| 23 | Created write-memory prompt v3.3 | 2026-04-16 |
| 24 | FAQ features in code (suppression parsing, baseline flags, TOML) | 2026-04-19 |
| 25 | STYLE-099 SuppressionWithoutReason synthetic finding | 2026-04-19 |
| 26 | Created `99-troubleshooting.md` (CICD) | 2026-04-19 |
| 27 | Performance impl: middle-out walker, `--jobs`, `--check-timeout`, TOOL-TIMEOUT (linters-cicd v3.12.0) | 2026-04-19 |
| 28 | `--version` flag on every check script (v3.13.0) | 2026-04-19 |
| 29 | `01-naming-conventions.md` v3.3.0 — Rule 2 clarification + Rule 9 | 2026-04-19 |
| 30 | `02-schema-design.md` v3.3.0 — §6 Mandatory Descriptive Columns | 2026-04-19 |
| 31 | BOOL-NEG-001 linter (v3.14.0) | 2026-04-19 |
| 32 | Inverted-field codegen tool (Go + PHP + TS) | 2026-04-19 |
| 33 | Cross-linked Rule 9 from boolean-principles + no-negatives (v2.2.0) | 2026-04-19 |
| 34 | `01-naming-conventions.md` v3.4.0 — Rule 8 three-bucket table | 2026-04-19 |
| 35 | `01-naming-conventions.md` v3.5.0 — Rules 10/11/12 (Description/Notes/Comments) | 2026-04-19 |
| 36 | Restructured `.lovable/` to single-file convention; saved write-memory prompt v1.0.0 | 2026-04-19 |
| 37 | Aligned `02-schema-design.md` §6 wording with naming v3.5.0 (v3.4.0) | 2026-04-19 |
| 38 | Removed `.gitmap/` and `src/.gitmap/` directories | 2026-04-19 |
| 39 | Created `spec/15-distribution-and-runner/` (00–04, v1.0.0) — install/runner/release/config contracts | 2026-04-19 |
| 40 | Added `linters-cicd` to `install-config.json` default folders | 2026-04-19 |
| 41 | Extended root `run.ps1` / `run.sh` with `slides`/`lint`/`help` sub-commands | 2026-04-19 |
| 42 | Removed `spec/19-ai-reliability/` and all dependent artifacts (per user request); CHANGELOG `[3.23.0]` rewritten | 2026-04-21 |
| 43 | Created `QUICKSTART.md` (root) — local + GitHub Actions copy-paste recipes | 2026-04-23 |
| 44 | Other-repo CI/CD templates: GitLab CI, Azure Pipelines, Jenkins (SARIF upload + required files) | 2026-04-23 |
| 45 | Decomposed `InstallSection.tsx` (337 → < 100 lines) into `install/{HighlightedCommand,CopyButton,BundleCard}` | 2026-04-23 |
| 46 | Refactored `fuzzyMatch.ts` + `useSearchKeyboard.ts` (CODE-RED-004/012/023) | 2026-04-23 |
| 47 | Refactored `readme.md` + `02-coding-guidelines.md` example for Boolean Principles compliance | 2026-04-23 |
| 48 | Validator clean run — 0 violations across 612 files (v3.81.0) | 2026-04-23 |
| 49 | Created `.lovable/cicd-issues/` + `cicd-index.md` and `solved-issues/` | 2026-04-23 |
| 50 | README CODE-RED Validation Walkthrough (riseup-asia-uploader) — one rule per snippet | 2026-04-23 |
| 51 | README CODE-RED Rules summary table (CODE-RED-001..023) + ToC entry | 2026-04-23 |
| 52 | README markdown hierarchy fix (h4 → h3 promotion, balanced fences verified) | 2026-04-23 |
| 53 | README Spec References index (9-row navigation table, all paths verified) | 2026-04-23 |
| 54 | Folded `.lovable/plans/installer-behavior-rollout.md` back into `plan.md` (single-file convention) | 2026-04-23 |
| 55 | README install section is first after badges; CI validator + memory rule (4.2.0–4.3.0) | 2026-04-24 |
| 56 | Standalone-script standards memory + payment-banner-hider RCA + reference rewrite (4.4.0) | 2026-04-24 |
| 57 | `tests/installer/check-no-latest-api.sh` + CI step + `npm run test:installer:no-latest` (4.5.0) | 2026-04-24 |

---

## Installer Behavior Rollout (formerly `.lovable/plans/installer-behavior-rollout.md`)

> **Spec source of truth:** `spec/14-update/27-generic-installer-behavior.md` v1.0.0

### Phase 1 — Spec + memory ✅ Done
- [x] Write `spec/14-update/27-generic-installer-behavior.md`
- [x] Add memory file `mem://standards/installer-behavior`
- [x] Update `mem://index.md` Core + Memories

### Phase 2 — Generator template ✅ Done (4.8.0)
- [x] Update `scripts/generate-bundle-installers.mjs` to ship §3 mode dispatch, §7 banner, §8 exit codes
- [x] Add `--version` / `-Version` and `--no-discovery` / `-NoDiscovery` flags
- [x] Add `-Help` / `-?` switch to PS1 template (spec §B.1.c.i bridge to comment-based help)
- [ ] Bump `LOOKAHEAD` constant from 5 → 20 in discovery probe (deferred — discovery not yet inlined; current behavior is forward-compatible)

### Phase 3 — Regenerate + verify ✅ Done (4.8.0)
- [x] Regenerate all 14 bundle installers
- [x] Run `bash -n` syntax checks on every regenerated file (7/7 pass)
- [x] Run no-latest-api guard on every file (14/14 pass)
- [x] New `tests/installer/check-bundle-installers.sh` — 126 structural assertions, wired into CI + `npm run test:installer:bundles`
- [x] Bump minor version, run `sync-version.mjs`

### Phase 4 — Hand-rolled installers ⏳ Pending
- [ ] `install.sh` / `install.ps1`: hand-edit to match template
- [ ] `release-install.sh` / `release-install.ps1`: audit against §4 MUST-NOT list
- [ ] `linters-cicd/install.sh`: same audit

### Phase 5 — Docs + downstream ⏳ Pending
- [ ] Add section to `readme.md` linking to spec §12
- [ ] Add section to `docs/slides-installer.md` referencing the generic spec
- [ ] Note in `mem://features/release-pinned-installer` that the generic spec is umbrella

### Acceptance gates
1. Every installer prints the §7 banner
2. Every installer accepts `--version` / `-Version`
3. PINNED MODE refuses `main` fallback and V→V+N discovery
4. IMPLICIT MODE probes V+1..V+20 in parallel
5. Exit codes `0/1/2/3/4/5` consistent across all installers
6. Spec path appears in `readme.md`

---

## Pending (Backlog)

| # | Task | Priority |
|---|------|----------|
| 01 | Publish the app for external access | Medium |
| 02 | End-to-end testing of docs viewer | Medium |
| 03 | Cross-reference link check across all specs | Low |
| 04 | Mobile responsiveness testing | Low |
| 05 | Expand remaining gap analysis items below 90% | Medium |
| 06 | Update `99-consistency-report.md` for recent expansions | Medium |
| 07 | Bootstrap PHP plugins for CODE-RED-001..004 (Phase 1 roadmap) | Medium |
| 08 | `--total-timeout` in `run-all.sh` + per-file 2s parse timeouts | Low |
| 09 | `exclude-paths` glob support in `.codeguidelines.toml` + `walker.py` | Medium |
| 10 | `--strict` flag in `scripts/load-config.py` (AC-CI-014) | Low |
| 11 | `--split-by severity` flag in `run-all.sh` (AC-CI-013) | Low |

---

*Plan — v3.13.0 — 2026-04-23*

*Plan — v3.14.0 — 2026-04-23*
