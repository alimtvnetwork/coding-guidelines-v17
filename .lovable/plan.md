# Current Plan

**Version:** 3.98.0
**Updated:** 2026-04-24

---

## Latest Session — Lock README Install Order to UI

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

### Phase 2 — Generator template ⏳ Pending
- [ ] Update `scripts/generate-bundle-installers.mjs` to ship §3 mode dispatch, §7 banner, §8 exit codes
- [ ] Add `--version` / `-Version` and `--no-discovery` / `-NoDiscovery` flags
- [ ] Bump `LOOKAHEAD` constant from 5 → 20 in discovery probe

### Phase 3 — Regenerate + verify ⏳ Pending
- [ ] Regenerate all 14 bundle installers
- [ ] Run `bash -n` / `pwsh` syntax checks on every regenerated file
- [ ] Run linters (`check-forbidden-strings.py`, `check-readme-canonicals.py`, `check-root-readme.py`)
- [ ] Bump minor version, run `sync-version.mjs`

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
