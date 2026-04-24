# Memory: index.md
Updated: 2026-04-24

# Project Memory

## Core
- 🔴 CODE RED: Never swallow errors. Zero-nesting (no nested if). Max 2 operands. Positively named guard functions.
- 🔴 CODE RED: Strict metrics: functions 8-15 lines, files < 300 lines, React components < 100 lines.
- 🔴 CODE RED: Standalone scripts — NO `!important`, NO `as unknown` / `as any`, NO error-swallowing `return null` in catch, NO magic strings (use enums in `types.ts`), NO bare top-level functions (class-based, DI). Hide via class toggle + CSS transition — never nested `requestAnimationFrame`. Always blank line before `return`.
- 🔴 PRE-WRITE: Before producing any standalone-script code, read the target repo's coding-guideline spec AND the sibling `standalone-scripts/*/src/` files first. See mem://issues/payment-banner-hider-rca.
- 🔴 README install commands: ONE line per command, NEVER `#` comments inside install code fences. Platform shown by header above the block. Install section comes FIRST after badges, before TOC. Match on-site `InstallSection.tsx` order (4 full-repo + 7 named bundles).
- 🔴 Release & Migration UI: exactly TWO cards (Windows PowerShell + macOS/Linux Bash), one-liner each. NEVER add "skip latest probe" variants. User locked this 2026-04-24.
- 🔴 Canonical repo slug: `alimtvnetwork/coding-guidelines-v17`. Any v14/v15 reference is a bug — run repo-wide `grep -rn` after every rebrand.
- 🔴 NEVER sync 01-app, 02-app-issues, 03-general, 03-tasks, or 12-consolidated-guidelines from gitmap-v3. All maintained locally.
- Naming: PascalCase for all internal IDs, DB, JSON, Types. Exceptions: Rust uses snake_case identifiers.
- DB Schema: PascalCase naming. PKs are `{TableName}Id` (INTEGER PRIMARY KEY AUTOINCREMENT). No UUIDs.
- DB Schema Rules 10/11/12: Entity/ref tables need `Description TEXT NULL`; transactional need `Notes`+`Comments TEXT NULL`; all must be nullable, no DEFAULT. Join tables exempt.
- Workflow: Spec-First (`spec/`) and Issue-First (`03-issues/`).
- Global Namespace: Always use `github.com/mahin/movie-cli-v2`. Any v1 reference is a bug.
- Version sync: bump package.json → `node scripts/sync-version.mjs` → `node scripts/sync-spec-tree.mjs`.
- Execution: Break complex requests into discrete tasks. Wait for "next" prompt to continue.

## Memories
- [Install Command Formatting](mem://constraints/install-command-formatting) — One-line installs, no inline comments, per-platform headers, mirror InstallSection.tsx order.
- [2026-04-24 Batch Cleanup + Rebrand](mem://sessions/2026-04-24-batch-cleanup-and-rebrand) — Slug rebrand to v16, Release & Migration UI lock, 11 plan items closed (B5/B6/B7/B8/B10/B11/09/10/12/B2 + UI).
- [Blank Line Between If Guards](mem://constraints/blank-line-between-if-guards) — Rule 5 applied to all markdown snippets and source code.
- [SQL Linter Rules](mem://sessions/2026-04-sql-linter-rules) — DB-FREETEXT-001 (presence) + MISSING-DESC-001 (presence+Rule 12+waivers), shared _lib, waiver syntax.
- [Axios Pinning](mem://constraints/axios-version-pinning) — Exact pinned versions only (1.14.0/0.30.3). Blocked versions: 1.14.1, 0.30.4.
- [Database Architecture](mem://architecture/database-schema) — PascalCase naming, no UUIDs, Vw prefixes for views.
- [Error Handling](mem://architecture/error-handling) — 'apperror' package, explicit file/path logging required.
- [PowerShell Style](mem://style/powershell-naming) — lowercase-kebab-case files, PascalCase Verb-Noun functions.
- [Development Workflow](mem://processes/development-workflow) — Spec-first workflow, linter enforcement, clean docs.
- [React ForwardRef Warning](mem://constraints/react-app-forwardref-warning) — Ignore lovable.js App.tsx ref console warning.
- [Code Red Guidelines](mem://standards/code-red-guidelines) — Full rules for zero-nesting, booleans, metrics.
- [Standards Enforcement](mem://processes/automated-standards-enforcement) — linter-scripts validation requirements.
- [Naming Conventions](mem://style/naming-conventions) — Zero-Underscore policy, full uppercase acronyms.
- [Caching Policy](mem://architecture/caching-policy) — Explicit TTL, deterministic keys, invalidate on mutation.
- [Nested Code Fences](mem://issues/nested-code-fence-data-corruption) — 4-backtick fences required for nested markdown blocks.
- [TypeScript Patterns](mem://standards/typescript-patterns) — Named interfaces for unions, TypedAction, explicit types.
- [Enum Standards](mem://standards/enum-standards) — Cross-language PascalCase enums, strict parsing methods.
- [Split Database](mem://architecture/split-database) — Root, App, Session hierarchical SQLite with WAL and Casbin.
- [Seedable Config](mem://architecture/seedable-configuration) — SemVer GORM merge of config.seed.json.
- [Self Update Arch](mem://features/self-update-architecture) — Rename-first deployment, atomicity with latest.json.
- [Doc Standards](mem://project/documentation-standards) — Mandatory numeric folders (01-20 Core, 21+ App), JSON tree syncing.
- [Author Attribution](mem://project/author-attribution) — Md. Alim Ul Karim, Riseup Asia LLC, SEO/footer requirements.
- [Avoid Gitmap Sync](mem://constraints/avoid-app-sync) — NEVER sync app, app-issues, general, tasks, or consolidated-guidelines from gitmap-v3.
- [Install Command Formatting](mem://constraints/install-command-formatting) — README top install area must mirror UI order; one-line commands only; bundles before ToC.
- [Standalone Script Standards](mem://constraints/standalone-script-standards) — Hard rules for browser/userscript files: no !important, no as-unknown, no error swallowing, class+DI, enums in types.ts, styles.ts, hide via class+transition.
- [Payment Banner Hider RCA](mem://issues/payment-banner-hider-rca) — Root cause for the macro-ahk-v23 regression and the mandatory pre-write checklist that prevents repeats.
