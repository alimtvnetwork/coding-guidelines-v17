# WP Plugin Spec — AI-Blind Implementation Readiness

**Date:** 2026-04-26
**Subject:** `spec/18-wp-plugin-how-to/`
**Audited by:** Lovable AI gap-analysis pass

---

## TL;DR

| Dimension | Score | Verdict |
|-----------|------:|---------|
| Coding-principle adherence (boolean naming, guard clauses, magic strings, function size, error handling, structured responses) | **9.2 / 10** | Production-grade |
| AI-blind buildability (a competent AI building the plugin from this spec alone, no human Q&A) | **8.4 / 10** | Mostly yes — gaps below |
| SQL-injection resistance of the recommended micro-ORM + validation patterns | **8.7 / 10** | Safe by default; one escape-hatch caveat |
| Overall confidence | **8.8 / 10** | Ship-ready with the gaps below addressed |

The 18-phase spec is one of the strongest authored modules in the repo. It is internally consistent, uses copy-paste-ready code, and routes every behaviour through a single named pattern (`safeExecute`, `EnvelopeBuilder`, `validationError`, `Orm::forTable`, `TypeCheckerTrait`, `FileLogger`). An AI agent can build a working plugin from this spec without asking a single clarifying question for ~85% of features.

---

## 1. Where the spec is genuinely AI-blind ready

| Strength | Evidence |
|----------|----------|
| **No magic strings** — backed PHP enums everywhere | Phase 2 + `StatusType::tryFrom()` validation (Phase 6 §6.4) |
| **Single error-handling path** | Every REST handler must use `safeExecute()` (Phase 3 §3.4). No exceptions can leak. |
| **Single response shape** | `EnvelopeBuilder` with PascalCase `Status / Attributes / Results` keys (Phase 5). |
| **Two-tier logging contract** | `ErrorLogHelper` (bootstrap) → `FileLogger` (runtime), Phase 4. |
| **Validation-then-sanitise rule** | Phase 6 §6.7 explicitly forbids `sanitize_text_field` before type-check. |
| **Hard ceilings** | 200-line file limit; 8–15-line function limit; Orchestrator pattern when exceeded (Phase 11). |
| **Copy-paste reference implementations** | Phase 7 contains the 5 starter files verbatim — autoloader, bootstrap, singleton, etc. |
| **End-to-end walkthrough** | Phase 20 wires every previous phase into one buildable example. |
| **SQL parameterisation by default** | `Orm::forTable()` + `OrmWhereTrait` use `:param` PDO bindings, with column names sanitised by `generateParamName()` regex `[^a-zA-Z0-9_]` (Phase 19 §19.2). |
| **Destructive-query guard** | `delete()` and `update()` refuse to execute without a WHERE clause (Phase 19 §19.4). |

---

## 2. SQL-Injection Risk Assessment

### Safe paths (no injection vector if used as documented)

- `where()`, `whereEqual()`, `whereGt()`, `whereLike()`, `whereIn()`, etc. → all values flow into PDO `:param` bindings.
- Column names in those methods are stripped to `[a-zA-Z0-9_]+` before being interpolated, neutering quoting attacks.
- `findOne($id)` and `count()` route through the same parameterised pipeline.
- Phase 6 mandates server-side type checks (`isInteger`, `isString`, enum `tryFrom`) **before** any value reaches the ORM, so an attacker can't smuggle non-string types in a JSON body.

### ⚠️ Residual injection risks (must be hardened before AI-blind use)

| # | Surface | Risk | Recommended fix |
|---|---------|------|-----------------|
| 1 | `Orm::rawExecute($sql)` (Phase 19 §19.5 "Raw SQL escape hatch") | Free-form SQL string. An AI seeing this method name may pass user input directly. | Add a **MUST** rule: `rawExecute()` accepts only static SQL literals; user-controlled values go through a 2nd `array $params` arg bound as PDO parameters. Add a linter rule `WP-ORM-001` that flags `rawExecute(` followed by string concatenation. |
| 2 | `whereRaw($clause, $params)` | Caller writes the clause verbatim. | Already accepts `$params`, but the spec doesn't *require* their use. Add a **MUST** that `$clause` contains no `$` PHP variables and no concatenation. |
| 3 | `orderBy($col, $dir)`, `groupBy($col)`, `selectColumn($col)` | If `$col` originates from user input (e.g. a sortable table header) it is interpolated into SQL. | Document an allow-list pattern: `$sortableColumns = ['CreatedAt', 'Status'];` then `if (!in_array($col, $sortableColumns, true)) { return validationError(...); }`. Add Phase 6 §6.5.1 "Sortable / filter parameter validation". |
| 4 | Table name in `Orm::forTable($table)` | Currently has no documented sanitiser. If table name ever comes from a request param (rare but possible for multi-tenant plugins), it's interpolated raw. | Either constrain `forTable()` to `[A-Za-z0-9_]+` server-side (defence in depth) or document that table names must always be enum-bound (`TableName::Transactions->value`). |
| 5 | WordPress core `$wpdb` usage | Phase 18 spec is silent on when to drop to `$wpdb` directly. An AI might use `$wpdb->query("SELECT ... WHERE id=" . $id)` because it's idiomatic WP. | Add a **MUST**: outside the micro-ORM, all `$wpdb` access uses `$wpdb->prepare()`. Provide a one-line example. |

---

## 3. Coding-Principle Adherence

| Principle (CODE RED) | Spec coverage | Score |
|----------------------|---------------|------:|
| Boolean naming (`is`/`has`, positive only) | Phase 6 §6.4 + every example uses `$hasName`, `$isPriorityValid` | 10 |
| Guard clauses, no nested `if` | Phase 6 §6.2 "Standard validation flow" is a textbook example | 10 |
| Magic strings forbidden | Phase 2 enums + `StatusType::tryFrom` enforcement | 10 |
| Function 8–15 lines / file ≤ 200 | Stated in Quick Start §0.4 + Phase 11 Orchestrator pattern | 9 — examples slightly exceed 15 lines but stay under 25 |
| Error handling first | Phase 3 §3.4 `safeExecute` — mandatory wrapper | 10 |
| Database PascalCase singular | Phase 19 examples (`Transactions` table → singular violation: should be `Transaction`) | 7 — **fix needed** |
| Structured response envelope | Phase 5 `EnvelopeBuilder` | 10 |
| Logging | Phase 4 two-tier | 10 |

**Detected inconsistency:** Phase 19 examples use plural table name `Transactions`. The repo's `04-database-conventions/` mandates **singular** table names (`Transaction`, not `Transactions`). All Phase 19 code blocks should be updated. Memory: `mem://architecture/database-schema`.

---

## 4. Things an AI Will Still Have to Guess

These are the items where an AI building a plugin from this spec alone will either hallucinate or stop and ask:

1. **Plugin namespace and slug.** Quick Start uses `PluginName` placeholder but never tells the AI the substitution rule. → Add §0.2.1 "Substitute `PluginName` with the PascalCase form of your slug; substitute `plugin-slug` with the kebab-case form."
2. **WordPress capability for REST routes.** `register_rest_route` permission callbacks are shown as `__return_true` in some examples. AI will use that in prod. → Add a **MUST**: write endpoints declare `current_user_can('manage_options')` (or a documented capability map) — never `__return_true`.
3. **Nonce verification for admin POSTs.** Not covered in Phase 8. → Add §8.x "Admin form nonces — `wp_verify_nonce` is mandatory for any non-GET admin endpoint".
4. **Database migration ordering / version table.** Phase 19 §19.6 calls `createTables()` but never defines a migration registry. AI will invent its own. → Document a single `Migration` table with `Version`, `AppliedAt`, `Checksum`.
5. **Asset enqueue rules.** Phase 11 mentions templates but not `wp_enqueue_script` discipline (versioning, dependencies, footer-vs-head). → 1-page addendum.
6. **Uninstall hook.** No mention of `uninstall.php` or `register_uninstall_hook`. → 1-page addendum.
7. **i18n.** Text-domain registration and `__() / _e()` rules are absent. Required by WordPress.org plugin directory. → 1-page addendum.
8. **CRON / WP-Cron jobs.** Not covered. → 1-page addendum.

---

## 5. Recommended Spec Patches (priority order)

| # | Phase | Patch | Severity |
|---|-------|-------|----------|
| 1 | 19 | Rename `Transactions` → `Transaction` in every code block; add note about singular-table mandate | High (silent rule violation) |
| 2 | 6 | Add §6.5.1 "Sortable / filter parameter allow-listing" | High (SQL injection vector) |
| 3 | 19 | Add **MUST** rules around `rawExecute()` and `whereRaw()` requiring `$params` array | High (SQL injection vector) |
| 4 | 8 | Add §8.x "REST permission callbacks — `__return_true` is forbidden in production" | High (auth bypass) |
| 5 | 8 | Add §8.y "Nonce verification for admin POSTs" | High |
| 6 | 0 | Add §0.2.1 explicit slug/namespace substitution rule | Medium |
| 7 | 19 | Document migration registry table | Medium |
| 8 | new phase | i18n, uninstall, asset enqueue, WP-Cron addenda | Medium |
| 9 | 19 | Constrain `Orm::forTable($table)` to `[A-Za-z0-9_]+` server-side | Low (defence in depth) |

---

## 6. Summary for Decision-Makers

- **Can you hand this spec to a competent AI today and get a runnable WP plugin?** Yes — for 85% of features, with a code-review pass to catch the gaps in §4.
- **Will the AI accidentally introduce SQL injection?** Only if it reaches for `rawExecute()` / `whereRaw()` / unvalidated `orderBy` — patches #2 and #3 close that.
- **Will the AI follow your CODE RED rules?** Yes — the spec actively enforces them through the response/error/validation pipelines.
- **Bottom line:** apply the 4 high-severity patches in §5 and the spec moves from **8.4 → 9.5 / 10** AI-blind ready.