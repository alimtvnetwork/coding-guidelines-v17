# Changelog

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

---

## [3.23.0] - 2026-04-21

### Removed
- **`spec/19-ai-reliability/`** — folder removed at user request along
  with all dependent artifacts: `scripts/replay-repro.sh`,
  `linters-cicd/scripts/check-context-hygiene.py`,
  `tests/release-install/`, the `--gctx-log` flag in
  `linters-cicd/run-all.sh`, and the matching memory file
  `.lovable/memory/architecture/ai-reliability-spec.md`. Production
  install/release scripts (`release-install.{sh,ps1}` from spec 14)
  remain — they predate spec 19.

---

## [3.22.0] - 2026-04-21

### Changed
- **Release pipeline bakes and uploads versioned `release-install.*`
  scripts.** New `.github/workflows/release.yml` step
  *"Bake version into release-install scripts"* (runs after the
  `linters-cicd` verify, before `softprops/action-gh-release`).
  - Copies `release-install.sh` and `release-install.ps1` into
    `release-artifacts/` and `sed`-substitutes the literal
    `__VERSION_PLACEHOLDER__` token with the resolved tag
    (`${{ steps.version.outputs.version }}`). Originals in the repo
    keep the placeholder verbatim so subsequent releases re-bake
    cleanly from a known-good source.
  - Fail-fast guards: missing source file → `::error::… missing`;
    any leftover `__VERSION_PLACEHOLDER__` after substitution →
    `::error::… still present`; explicit `grep` assertions confirm
    `BAKED_VERSION="vX.Y.Z"` (bash) and `$BakedVersion = "vX.Y.Z"`
    (PowerShell) are present in the staged copies.
  - `chmod +x` applied to the bash variant; SHA-256 sums for both
    files appended to `release-artifacts/checksums.txt`.
  - Both files added to the `softprops/action-gh-release` `files:`
    list, so each GitHub Release page now ships
    `release-install.sh` and `release-install.ps1` as first-class
    assets pinned to that exact tag. Implements the deferred wiring
    step from `spec/14-update/25-release-pinned-installer.md` §6.

## [3.21.0] - 2026-04-21

### Added
- **`release-install.sh` and `release-install.ps1`** — pinned-version
  installers for GitHub Release pages. Implementation of
  `spec/14-update/25-release-pinned-installer.md`.
  - Version source priority: `--version` / `-Version` argument →
    baked-in `__VERSION_PLACEHOLDER__` (substituted at release time) →
    fatal exit 1.
  - Strict semver validation (`^v?\d+\.\d+\.\d+(-[A-Za-z0-9.]+)?$`);
    invalid input exits 2 before any network call.
  - Hybrid download: tries `releases/download/<tag>/source-code.{tar.gz,zip}`
    first, falls back to `codeload.github.com/.../refs/tags/<tag>`.
    Both 404 → exit 3 with both probed URLs and HTTP codes.
  - Hands off to inner installer with `--pinned-by-release-install <tag>`
    handshake; auto-update / version-probe is disabled for the run.
  - `--no-update` / `-NoUpdate` accepted as no-ops (pinning is always on).
  - Checksum verification deferred — matches existing `install.*`
    behavior. Tracked as a follow-up.
- **`install.sh` and `install.ps1` pinning handshake.** Both now accept
  `--pinned-by-release-install <tag>` / `-PinnedByReleaseInstall <tag>`.
  When set:
  - Version-probe / auto-update is skipped unconditionally.
  - If `--version` is also passed, it must equal the handshake value;
    mismatch exits 2 (handshake-skew detection per spec §Failure Modes).
  - Implements AMB-1 from the spec: generic installers also enforce
    strict pinning when an explicit version is requested.

### Removed
- **Stale `LEGACY-CDN-DOMAIN` allowlist entries.** Removed
  `spec/15-domain-migration/` and `docs/legacy-domains.md` from the
  rule's allowlist in `linter-scripts/forbidden-strings.toml` — neither
  path exists in the repository, so they could only mask future
  legitimate findings. Allowlist is now empty for this rule. Added
  `CHANGELOG.md` to `exclude_files` so changelog prose can describe
  legacy patterns without false positives.

## [3.20.0] - 2026-04-21

### Changed
- **`check-spec-folder-refs.py` — section-aware allowlist + clearer errors.**
  The linter now distinguishes documentation-only references from real
  external (sibling-repo) folder references.
  - `spec-folder-refs.allowlist` is now divided into `[external]` and
    `[doc-only]` sections. Entries before any header default to
    `[external]` for backward compatibility.
  - Stale-reference output now includes a fuzzy "Did you mean …?" hint
    using the nearest existing spec folder, plus a 3-option decision
    tree (typo / sibling-repo / doc-only) so authors know exactly how
    to resolve each finding.
  - The previously-allowlisted `15-domain-migration` was removed — the
    only consumer (CHANGELOG.md) was fixed in 3.19.x cleanup, so
    `[doc-only]` starts empty.

## [3.19.0] - 2026-04-20

### Added
- **`LEGACY-CDN-DOMAIN` forbidden-strings rule.** Guards against legacy CDN domain
  references (`cdn.riseup-asia.com`) that should be `cdn.riseup.asia` per the
  current infrastructure standard.
  - Pattern: `cdn\.riseup-asia\.com`
  - Allowlist: `docs/legacy-domains.md` (legitimate historical migration documentation).
  - Added to `linter-scripts/forbidden-strings.toml` as the third `[[rule]]`
    demonstrating the TOML-driven scanner's extensibility.

## [3.18.0] - 2026-04-20

### Added
- **`STALE-MODULE-PATH` forbidden-strings rule.** Guards against legacy module
  path references (`movie-cli-v1`) that should be `movie-cli-v2` per the
  global namespace standard.
  - Pattern: `movie-cli-v1\\b`
  - Allowlist: `spec/14-update/23-install-script-version-probe.md` (legitimate
    historical migration docs).
  - Added to `linter-scripts/forbidden-strings.toml` as the second `[[rule]]`
    demonstrating the TOML-driven scanner's extensibility.

## [3.17.0] - 2026-04-20

### Refactored
- **`forbidden-strings` TOML-driven linter.** Generalized the single-purpose
  `check-stale-repo-slug.sh` into a reusable, configuration-driven scanner.
  - New `linter-scripts/forbidden-strings.toml` — each `[[rule]]` defines a
    regex `pattern`, human-readable `description`, `fix_hint`, `allowlist` paths,
    and exclusion lists.
  - New `linter-scripts/check-forbidden-strings.py` — parses the TOML config
    and validates all rules in a single pass with unified reporting.
- **CI migration** — removed `check-stale-repo-slug.sh` and
  `stale-repo-slug.allowlist`; the generic checker now runs via Python in the
  lint job.

### Benefits
- Adding new rename guards no longer requires new scripts — just append a
  `[[rule]]` block to the TOML.
- Allowlists live next to their rules, making intent explicit and reviews easier.

## [3.16.0] - 2026-04-20

### Added
- **`check-stale-repo-slug.sh` linter safeguard.** Scans repository for pre-renumber
  repo slug references (`coding-guidelines-v1` through `v14`). The current canonical
  slug is `coding-guidelines-v17`; any older slug is a bug from incomplete bulk rename.
- **Allowlist-driven filtering** via `linter-scripts/stale-repo-slug.allowlist` --
  permits legitimate historical references in changelogs, migration docs, and
  install-script version-probe specs (v5→v15 is the canonical worked example).
- **CI wiring** -- added to `.github/workflows/ci.yml` lint job; fails build if
  stale references are found outside allowlisted paths.

## [3.12.0] — 2026-04-19

### Refactored
- **Free-text-column rule family — extracted shared logic** into
  `linters-cicd/checks/_lib/free_text_columns.py`. Both rules are now
  thin shims over the shared module:
  - `DB-FREETEXT-001` → v1.1.0 — **presence only**, no waivers (preserves
    v1.0 behaviour for existing CI configs).
  - `MISSING-DESC-001` → v1.2.0 — **presence + Rule 12 nullability +
    waiver mechanism**. Recommended for new pipelines.
- Both rules share classifier, column detection, join-table heuristic,
  and scope rules — they cannot drift apart.
- Added a guidance note to
  `spec/02-coding-guidelines/06-cicd-integration/06-rules-mapping.md`:
  enable **only one** of the two rules in CI to avoid duplicate findings.

### Why this approach
The user requested "extend DB-FREETEXT-001 with Rule 12 too." Mirroring
the logic would have created two rules emitting identical findings on
the same code (noisy CI output, ambiguous suppressions). The refactor
keeps both rule IDs alive for back-compat while making MISSING-DESC-001
the canonical superset.

---

## [3.11.0] — 2026-04-19

### Added
- **`MISSING-DESC-001` v1.1 — waiver mechanism.** Per-block waiver
  `-- linter-waive: MISSING-DESC-001 reason="..."` (5-line lookback,
  comments-only chain) and per-file waiver
  `-- linter-waive-file: MISSING-DESC-001 reason="..."`. The
  `reason="..."` clause is **mandatory** — bare waivers are ignored so
  silent suppressions can't pass review. Documented in
  `spec/04-database-conventions/02-schema-design.md` §6.6 and
  `linters-cicd/checks/missing-desc/README.md`.

### Audited & cleaned
- **Spec tree audit (115 violations → 0 unwaived).** Every `CREATE TABLE`
  inside ` ```sql ` markdown fences across `spec/` was audited against
  Rules 10/11/12.
  - **Fixed in place:** `spec/17-consolidated-guidelines/22-app-database.md`
    — entity / lookup / transactional / migration templates now
    demonstrate `Description` and `Notes`+`Comments` correctly, and a
    new §4.4 *Transactional Table Template* was added.
  - **Waived (98 blocks across 15 files):** pedagogical mini-examples
    (PK choice, normalization, FK syntax, junction tables, split-DB
    isolation, seedable-config, naming-only examples) where adding the
    free-text columns would obscure the lesson being taught. Each
    waiver carries a path-appropriate `reason="..."`.
  - The three intentional ❌-WRONG anti-examples in
    `02-schema-design.md` §6.4 carry the reason
    `"Intentional anti-example for Rule {N} — teaches the violation"`.

---

## [3.10.0] — 2026-04-19

### Added
- **`DB-FREETEXT-001`** SQL linter (`linters-cicd/checks/free-text-columns/sql.py`)
  — flags `CREATE TABLE` statements missing the required nullable free-text
  columns per `spec/04-database-conventions/02-schema-design.md` §6 and Naming
  Rules 10/11/12 (v3.5.0):
  - Entity / reference / lookup / master-data tables must declare
    `Description TEXT NULL`.
  - Transactional tables (`*Transaction`, `*Invoice`, `*Order`, `*Payment`,
    `*Bill`, `*Charge`, `*Refund`, `*Settlement`) must declare both
    `Notes TEXT NULL` AND `Comments TEXT NULL`.
  - Audit/log tables (`*Log`, `*History`, `*Event`, `*AuditLog`) must declare
    `Notes TEXT NULL`.
  - Pure join/pivot tables (no `{TableName}Id` PK) are exempt.
- Registered in `linters-cicd/checks/registry.json` and documented in
  `spec/02-coding-guidelines/06-cicd-integration/06-rules-mapping.md` under a
  new **Database rules** section. Verified against good/bad fixtures (4
  expected findings on bad, 0 on good).

---

## [3.9.0] — 2026-04-19

### Added
- **`linters-cicd/` CI/CD linter pack** — portable, language-agnostic CODE RED
  enforcement that any pipeline can integrate with one line.
  - 7 checks (Phase 1, Go + TypeScript): nested-if, boolean-naming,
    magic-strings, function-length, file-length (universal), positive-conditions,
    no-else-after-return.
  - **SARIF 2.1.0** output by default — surfaces inline on GitHub PRs (Code
    Scanning), GitLab MRs, and Azure DevOps.
  - `run-all.sh` orchestrator with text + SARIF formats and proper exit codes
    (0 clean / 1 findings / 2 tool error).
  - **GitHub composite Action** at `linters-cicd/action.yml`:
    `uses: alimtvnetwork/coding-guidelines-v17/linters-cicd@v3.9.0`.
  - **`install.sh` one-liner** with SHA-256 verification and `-d`/`-v`/`-n` flags.
  - Ready-to-paste CI templates for GitHub Actions, GitLab CI, Azure DevOps,
    Bitbucket Pipelines, Jenkins, plus a pre-commit hook.
- **`spec/02-coding-guidelines/06-cicd-integration/`** — full spec for the
  linter pack: SARIF contract, plugin model, language roadmap (Phase 2 = PHP,
  Phase 3 = Python + Rust, Phase 4+ on request), CI templates inventory,
  distribution model, rules mapping, and acceptance criteria.

### Release pipeline
- `.github/workflows/release.yml` now also packages
  `coding-guidelines-linters-vX.Y.Z.zip` on every `v*` tag, computes its
  SHA-256, appends to `checksums.txt`, and attaches both the ZIP and
  `linters-install.sh` to the GitHub Release.

### Smoke test
- Orchestrator self-tested against this repo's `src/`: all 7 checks ran,
  SARIF validated against the 2.1.0 schema, exit codes correct.

---

## [3.8.0] — 2026-04-19

### Added
- **`-n` / `--no-latest` skip-probe flag** on both installers. Pass `-n` to bypass
  the latest-version auto-probe and run the current installer as-is — useful on
  flaky networks, in CI pipelines, or when you want a fully reproducible install
  pinned to the URL you ran.
  - PowerShell: `-n`, `-NoLatest`, `-NoProbe` (all aliases of the same switch).
  - Bash: `-n`, `--no-latest`, `--no-probe` (all aliases).
- New "skip latest probe" one-liner variants surfaced in both the landing-page
  install section and the root `readme.md` so users can copy them in one click.

### Changed
- **Windows PowerShell command is now listed first** in the UI install section
  and the README's Option 1 — matching the dominant audience for this repo.
  Bash (macOS / Linux) follows immediately below.
- **Middle-out probe ordering** in `install.ps1` and `install.sh`. The 20 candidate
  versions (`current+1 .. current+20`) are now dispatched starting from the middle
  of the window and expanding outward (`mid, mid+1, mid-1, mid+2, mid-2, …`).
  The result-scan loop iterates highest → lowest so the first hit accepted is
  already the winner — no second pass, no per-iteration sort.
  - Documented as a portable trick in
    [`spec/14-update/23-install-script-version-probe.md`](spec/14-update/23-install-script-version-probe.md)
    so any other CLI's installer can adopt it.
- **Indented PowerShell output** — every `Write-Step / OK / Warn / Err / Dim / Plain`
  call (and the banner / summary blocks) now share a 4-space left gutter for a
  clean, professional column. Matches the visual rhythm of the bash output.

### Performance
- The PowerShell probe was rewritten to use in-process `System.Net.Http.HttpClient`
  async HEAD requests instead of `Start-Job` (which spawns one PowerShell process
  per candidate, ~20 s of overhead). The `Timeout = 2s` setting is now genuinely
  honoured and the probe finishes in ~2–3 s end-to-end.

### Documentation
- README's flag table updated with the full alias list:
  `--no-probe`, `--no-latest`, `-n` ↔ `-NoProbe`, `-NoLatest`, `-n`.
- New section in `spec/14-update/23-install-script-version-probe.md`:
  *"Probe ordering optimization (middle-out + descending result scan)"* —
  explains why ordering still matters under degraded parallelism (corporate
  proxies, throttled CI runners, low-fd shells) and provides reference
  pseudocode any installer can copy.

### Files touched
- `install.ps1` — `-NoLatest` / `-n` aliases, middle-out candidate array,
  descending result scan.
- `install.sh` — `--no-latest` / `-n` aliases, middle-out candidate array,
  descending `sort -n | tail -1` winner pick.
- `src/components/landing/InstallSection.tsx` — Windows-first ordering, added
  two "skip latest probe" command cards.
- `readme.md` — Reordered Option 1 (PowerShell first), added `-n` variants,
  expanded flag table.
- `spec/14-update/23-install-script-version-probe.md` — middle-out ordering spec.
- `package.json`, `version.json` — bumped to `3.8.0`.

---
