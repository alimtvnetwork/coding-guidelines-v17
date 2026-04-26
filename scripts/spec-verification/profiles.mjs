/**
 * profiles.mjs — Folder profiles for the verification injector.
 *
 * Each profile defines:
 *   - tag:     short prefix used in AC IDs (e.g. AC-DB-002)
 *   - title:   (slug) => H3 title text
 *   - given:   (slug) => Given clause
 *   - when:    static When clause (action verb)
 *   - then:    (slug) => Then clause (machine-checkable assertion)
 *   - commandKeys: list of keys into ``COMMAND_TEMPLATES``. Composed with
 *                  `&&` to produce the final shell command. This keeps the
 *                  command surface centralised — one edit in the registry
 *                  propagates to every profile that uses the template.
 *
 * Adding a folder profile is the only change needed to onboard a new spec
 * top-level folder. Keep bodies short — one Given/When/Then triple per
 * file is the design budget.
 */
import { composeCommands } from "./command-templates.mjs";

const slugTitle = (slug) => slug.replace(/\b\w/g, (c) => c.toUpperCase());

/**
 * Resolve a profile's `commandKeys` into the final shell string.
 * Centralised here so both the injector and any future tooling (docs
 * table, dashboards) get identical resolution.
 */
export function resolveCommand(profile) {
  return composeCommands(profile.commandKeys);
}

export const FOLDER_PROFILES = {
  "01-spec-authoring-guide": {
    tag: "AC-SAG",
    title: (s) => `Conformance check for spec authoring rule: ${slugTitle(s)}`,
    given: () => "Run the spec-structure linter against `spec/`.",
    when: "Run the verification command shown below.",
    then: () => "Every folder MUST contain a valid `00-overview.md`, follow kebab-case numeric prefixes, and resolve all internal links.",
    commandKeys: ["meta:spec-health"],
  },
  "02-coding-guidelines": {
    tag: "AC-CG",
    title: (s) => `Coding guideline conformance: ${slugTitle(s)}`,
    given: () => "Run the cross-language coding-guidelines validator against `src/` and language-specific source roots.",
    when: "Run the verification command shown below.",
    then: () => "Zero CODE-RED violations are reported (functions ≤ 15 lines, files ≤ 300 lines, no nested ifs, max 2 boolean operands).",
    commandKeys: ["lint:guidelines-go", "lint:guidelines-py"],
  },
  "03-error-manage": {
    tag: "AC-ERR",
    title: (s) => `Error-management conformance: ${slugTitle(s)}`,
    given: () => "Audit error-handling sites for use of the `apperror` package, error codes, and explicit file/path logging.",
    when: "Run the verification command shown below.",
    then: () => "Every error site uses `apperror.Wrap`/`apperror.New` with a registered code; no bare `errors.New` or swallowed errors remain.",
    commandKeys: ["lint:forbidden-strings", "lint:guidelines-go"],
  },
  "04-database-conventions": {
    tag: "AC-DB",
    title: (s) => `Database convention conformance: ${slugTitle(s)}`,
    given: () => "Run the SQL schema linter against your DDL files.",
    when: "Run the verification command shown below.",
    then: () => "Every table is PascalCase singular; PK is `<TableName>Id INTEGER PRIMARY KEY AUTOINCREMENT`; columns are `NOT NULL` unless waived; no `createdAt`, `created_at`, `UUID` tokens.",
    commandKeys: ["schema:db"],
  },
  "05-split-db-architecture": {
    tag: "AC-SDB",
    title: (s) => `Split-DB architecture conformance: ${slugTitle(s)}`,
    given: () => "Inspect Root/App/Session DB lifecycle wiring and Casbin RBAC enforcement points.",
    when: "Run the verification command shown below.",
    then: () => "Each tier opens its own SQLite handle (WAL mode), policy reload happens on Casbin policy change, and user-scope isolation is enforced by row filters.",
    commandKeys: ["lint:spec-links"],
  },
  "06-seedable-config-architecture": {
    tag: "AC-CFG",
    title: (s) => `Seedable-config conformance: ${slugTitle(s)}`,
    given: () => "Diff the running config tree against `config.seed.json` after a SemVer-aware GORM merge.",
    when: "Run the verification command shown below.",
    then: () => "Merged keys preserve user overrides; new seed keys are added; removed seed keys are pruned; merge is idempotent on a second pass.",
    commandKeys: ["lint:spec-links"],
  },
  "07-design-system": {
    tag: "AC-DS",
    title: (s) => `Design-system conformance: ${slugTitle(s)}`,
    given: () => "Scan `src/` for raw color literals, hard-coded spacing, and untokenized typography.",
    when: "Run the verification command shown below.",
    then: () => "All visual properties resolve to semantic tokens declared in `index.css` / `tailwind.config.ts`; no `text-white`, `bg-#fff`, or hex literals appear in components.",
    commandKeys: ["lint:eslint"],
  },
  "08-docs-viewer-ui": {
    tag: "AC-UI",
    title: (s) => `Docs viewer UI conformance: ${slugTitle(s)}`,
    given: () => "Render the docs viewer against the spec tree fixture.",
    when: "Run the verification command shown below.",
    then: () => "Keyboard navigation, syntax highlighting, fullscreen toggle, and copy-markdown all function without console errors.",
    commandKeys: ["test:unit"],
  },
  "09-code-block-system": {
    tag: "AC-CB",
    title: (s) => `Code-block system conformance: ${slugTitle(s)}`,
    given: () => "Render fenced code blocks (incl. nested 4-backtick fences) and checklist blocks from the spec tree.",
    when: "Run the verification command shown below.",
    then: () => "Nested fences preserve backtick counts; clipboard copy returns exact source; tree rendering matches the constants map.",
    commandKeys: ["test:unit"],
  },
  "10-research": {
    tag: "AC-RES",
    title: (s) => `Research-folder conformance: ${slugTitle(s)}`,
    given: () => "Validate research note structure (front-matter, dated filenames, source links).",
    when: "Run the verification command shown below.",
    then: () => "Every research note has a date prefix, a `Source:` line, and a `Decision:` or `Outcome:` section.",
    commandKeys: ["lint:spec-folders"],
  },
  "11-powershell-integration": {
    tag: "AC-PS",
    title: (s) => `PowerShell integration conformance: ${slugTitle(s)}`,
    given: () => "Lint PowerShell scripts and modules in `scripts/` for naming, parameter binding, and error propagation.",
    when: "Run the verification command shown below.",
    then: () => "Filenames are lowercase-kebab-case; functions are `Verb-Noun` PascalCase; `$ErrorActionPreference = 'Stop'` is set; no `Write-Host` for control flow.",
    commandKeys: ["lint:powershell"],
  },
  "12-cicd-pipeline-workflows": {
    tag: "AC-CI",
    title: (s) => `CI/CD pipeline conformance: ${slugTitle(s)}`,
    given: () => "Validate `.github/workflows/*.yml` against the documented job matrix.",
    when: "Run the verification command shown below.",
    then: () => "Required jobs (`lint`, `cross-links`, `sync-drift`) are present; concurrency groups follow the `<workflow>-<ref>` pattern; `permissions:` is least-privilege.",
    commandKeys: ["meta:full-ci"],
  },
  "13-generic-cli": {
    tag: "AC-CLI",
    title: (s) => `Generic CLI conformance: ${slugTitle(s)}`,
    given: () => "Run the CLI smoke harness against the documented subcommand surface.",
    when: "Run the verification command shown below.",
    then: () => "`--help` exits 0 for every subcommand; flags follow kebab-case; structured output is valid JSON when `--json` is set.",
    commandKeys: ["lint:guidelines-go"],
  },
  "14-update": {
    tag: "AC-UPD",
    title: (s) => `Self-update conformance: ${slugTitle(s)}`,
    given: () => "Exercise the rename-first deploy path against a fixture release directory.",
    when: "Run the verification command shown below.",
    then: () => "`latest.json` is written atomically; the old binary is renamed (not deleted) before the new one is moved into place; rollback restores the previous version.",
    commandKeys: ["lint:spec-links"],
  },
  "15-distribution-and-runner": {
    tag: "AC-DIST",
    title: (s) => `Distribution & runner conformance: ${slugTitle(s)}`,
    given: () => "Validate the install contract and runner contract against a clean machine fixture.",
    when: "Run the verification command shown below.",
    then: () => "Install script is idempotent; runner detects missing deps and exits with a stable error code; PATH entries are deduped.",
    commandKeys: ["lint:spec-links"],
  },
  "16-generic-release": {
    tag: "AC-REL",
    title: (s) => `Generic-release conformance: ${slugTitle(s)}`,
    given: () => "Inspect a release artifact bundle for required assets and checksums.",
    when: "Run the verification command shown below.",
    then: () => "SHA-256 checksums verify; `release-metadata.json` matches the package version; install scripts pin the exact release tag.",
    commandKeys: ["lint:spec-links"],
  },
  "17-consolidated-guidelines": {
    tag: "AC-CON",
    title: (s) => `Consolidated guideline conformance: ${slugTitle(s)}`,
    given: () => "Cross-check this consolidated digest against its source spec folder.",
    when: "Run the verification command shown below.",
    then: () => "Every rule cited here resolves to a section in the source folder via the cross-link checker; no orphan rules.",
    commandKeys: ["lint:spec-links"],
  },
  "18-wp-plugin-how-to": {
    tag: "AC-WP",
    title: (s) => `WordPress plugin conformance: ${slugTitle(s)}`,
    given: () => "Static-analyze the plugin source against the documented enum, trait, and REST conventions.",
    when: "Run the verification command shown below.",
    then: () => "Enums are `enum X: string` with metadata methods; REST routes use the `/wp-json/<plugin>/v1/` namespace; nonces are verified on every mutating request.",
    commandKeys: ["lint:spec-links"],
  },
  "21-app": {
    tag: "AC-APP",
    title: (s) => `App-level conformance: ${slugTitle(s)}`,
    given: () => "Run the application's integration smoke suite.",
    when: "Run the verification command shown below.",
    then: () => "Boot sequence completes; health endpoint returns 200; no unhandled promise rejections appear in the log.",
    commandKeys: ["test:unit"],
  },
  "22-app-issues": {
    tag: "AC-AI",
    title: (s) => `App issues triage conformance: ${slugTitle(s)}`,
    given: () => "Audit issue write-ups for the required Reproduction / Cause / Fix / Prevention sections.",
    when: "Run the verification command shown below.",
    then: () => "Every issue file contains all four sections and references at least one commit or PR.",
    commandKeys: ["lint:spec-links"],
  },
  "23-app-db": {
    tag: "AC-ADB",
    title: (s) => `App-database conformance: ${slugTitle(s)}`,
    given: () => "Validate app database migrations against the schema-design rules.",
    when: "Run the verification command shown below.",
    then: () => "Migrations are forward-only; PascalCase naming is preserved; new columns are nullable with no DEFAULT (Rule 12).",
    commandKeys: ["schema:db"],
  },
  "24-app-ui-design-system": {
    tag: "AC-ADS",
    title: (s) => `App design-system conformance: ${slugTitle(s)}`,
    given: () => "Scan app UI for raw colors and untokenized spacing; render Storybook (or equivalent) snapshot suite.",
    when: "Run the verification command shown below.",
    then: () => "All components consume semantic tokens; snapshot diff is empty in light and dark themes.",
    commandKeys: ["lint:eslint", "test:unit"],
  },
};

export const DEFAULT_PROFILE = {
  tag: "AC-GEN",
  title: (s) => `General conformance check: ${slugTitle(s)}`,
  given: () => "Run the spec health-check against this folder.",
  when: "Run the verification command shown below.",
  then: () => "Cross-references resolve and the folder contains the required `00-overview.md`, `97-acceptance-criteria.md`, and `99-consistency-report.md`.",
  commandKeys: ["lint:spec-links"],
};