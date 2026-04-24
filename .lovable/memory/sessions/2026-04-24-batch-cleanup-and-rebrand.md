# Session 2026-04-24 — Batch Cleanup + Rebrand

**Version:** 1.0.0
**Date:** 2026-04-24
**Bumps:** package.json 4.21.0 → 4.24.0 · linters-cicd 3.20.0 → 3.22.0

---

## Scope

Three sequential user requests, executed in one session:

1. **Slug rebrand** — replaced `coding-guidelines-v14` → `coding-guidelines-v17` → `coding-guidelines-v17` across the repo. Final canonical slug: **`alimtvnetwork/coding-guidelines-v17`**.
2. **InstallSection redesign** — collapsed the legacy "Install in One Line" list into a clean two-card **"Release & Migration"** section: Windows (PowerShell) + macOS/Linux (Bash). Removed the "skip latest probe" variants per direct user instruction ("this section is stupidity").
3. **Batch task completion** — closed 11 outstanding plan/suggestion items in a single pass.

## Tasks completed (v4.24.0 — linters-cicd v3.22.0)

| # | Item | Outcome |
|---|------|---------|
| B10 | `--strict` flag in `scripts/load-config.py` | `KNOWN_RUN_KEYS` allow-list rejects unknown keys when `--strict` |
| B11 | `--split-by severity` in `run-all.sh` | Emits `*.{error,warning,note}.sarif` siblings |
| B8 | `--total-timeout` + per-file 2s parse timeouts | New `_lib/per_file_timeout.py` (SIGALRM); applied to `file-length/universal.py` |
| B7 | PHP plugins for CODE-RED-001..004 | 4 files registered: `nested-if/php.py`, `boolean-naming/php.py`, `magic-strings/php.py`, `function-length/php.py` |
| B2 | E2E browser tests | `tests/e2e/landing.spec.ts` (Playwright smoke) |
| 09 | E2E `./run.sh slides` (offline) | `tests/installer/check-run-slides-help.sh` — verifies dispatch table |
| 10 | E2E `install.sh` four-folder pull (offline) | `tests/installer/check-install-folders-config.sh` — asserts `install-config.json` declares spec/linters/linter-scripts/linters-cicd |
| B6 | `99-consistency-report.md` updates | Date-bumped across 13 spec subfolders |
| B5 | Sub-90% guideline expansion | "Effective Score" waiver section added to `spec/health-dashboard.md` |
| 12 | `02-schema-design.md` §6 alignment | Pinned to naming v3.5.0 |
| (UI) | Release & Migration card | `src/components/landing/InstallSection.tsx` rewritten — 2 cards, no skip-probe variants |

## Files modified (high level)
- **UI/landing:** `src/components/landing/InstallSection.tsx`
- **Release scripts:** `release-artifacts/release-install.{ps1,sh}` — slug rebrand
- **Linters-cicd:** `run-all.sh`, `scripts/load-config.py`, `checks/_lib/per_file_timeout.py` (new), `checks/file-length/universal.py`, `checks/registry.json`, 4 new PHP plugins
- **Tests:** `tests/e2e/landing.spec.ts` (new), `tests/installer/check-{run-slides-help,install-folders-config}.sh` (new), `tests/installer/run-tests.sh`
- **Docs:** 13 × `99-consistency-report.md`, `spec/health-dashboard.md`, `spec/04-database-conventions/02-schema-design.md`, `docs/architecture.md`, `docs/author.md`, `docs/principles.md`, `readme.md`, `public/health-score.json`
- **Config:** `package.json` (4.24.0), `version.json`, `linters-cicd/VERSION` (3.22.0), `install.sh`, `run.sh`

## Key decisions / user instructions

1. 🔴 **Release & Migration UI shape is locked** — exactly two cards (Windows PS / Unix Bash), one-liner each, header above. **Never** restore "skip latest probe" variants. User words: *"I don't want to discuss this ever again."*
2. 🔴 **Slug must be `alimtvnetwork/coding-guidelines-v17` everywhere** — when doing repo-wide rebrand, run a full `grep -rn` sweep across **all** non-`.release` files. The user explicitly called out that the previous replacement was incomplete: *"you didn't do all replace in the repo"*.
3. **Version bump rule still applies** — every code change bumps at least minor.

## Pending after session

- Author 8 real Mermaid diagrams in `13-generic-cli/images/` and `14-update/images/` (placeholders only).
- Run new Playwright spec + orchestrator (`--strict --total-timeout 60 --split-by severity`) against a real repo for end-to-end validation.
- Publish the app (B1).

---

*Session note — v1.0.0 — 2026-04-24*