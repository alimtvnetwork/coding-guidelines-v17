# Verification Command Templates

**Generated:** 2026-04-21

Single source of truth for the shell commands used in every
`## Verification` block injected by
`scripts/spec-verification/inject-verification-sections.mjs`. Edit the
registry in `command-templates.mjs`, then run
`npm run spec:verify:docs` to refresh this file.

---

## 1. Verification needs → templates

The recommended template for each common verification need:

| Verification need | Template key | Command |
|-------------------|--------------|---------|
| Internal links resolve | `lint:spec-links` | `python3 linter-scripts/check-spec-cross-links.py --root spec --repo-root .` |
| Spec folder structure valid | `lint:spec-folders` | `python3 linter-scripts/check-spec-folder-refs.py` |
| No forbidden tokens / paths | `lint:forbidden-strings` | `python3 linter-scripts/check-forbidden-strings.py` |
| DB schema conforms | `schema:db` | `python3 linter-scripts/check-forbidden-strings.py` |
| Code-style guidelines (Go/Py) | `lint:guidelines-go` | `go run linter-scripts/validate-guidelines.go --path spec --max-lines 15` |
| TypeScript/ESLint clean | `lint:eslint` | `npm run lint` |
| PowerShell scripts clean | `lint:powershell` | `pwsh -NoProfile -Command "Invoke-ScriptAnalyzer -Path scripts -Recurse -Severity Warning"` |
| Axios pinned safely | `lint:axios-version` | `bash linter-scripts/check-axios-version.sh` |
| Unit tests pass | `test:unit` | `npm run test` |
| Production build succeeds | `test:build` | `npm run build` |
| specTree.json in sync | `schema:spec-tree` | `node scripts/sync-spec-tree.mjs && git diff --exit-code -- src/data/specTree.json` |
| version.json in sync | `schema:version` | `node scripts/sync-version.mjs` |
| Spec health (structure + links) | `meta:spec-health` | `python3 linter-scripts/check-spec-folder-refs.py && python3 linter-scripts/check-spec-cross-links.py --root spec --repo-root .` |
| Full CI gate | `meta:full-ci` | `npm run sync && npm run lint && npm run test` |

---

## 2. Template registry

### 🧹 Lint

| Key | Asserts | Command |
|-----|---------|---------|
| `lint:axios-version` | Axios is pinned to an exact safe version (1.14.0 or 0.30.3); blocked versions are rejected. | `bash linter-scripts/check-axios-version.sh` |
| `lint:eslint` | ESLint passes with zero errors against the project's TypeScript and React surface. | `npm run lint` |
| `lint:forbidden-paths` | No re-split or merge-proposal placeholder paths leak into spec/. | `bash linter-scripts/check-forbidden-spec-paths.sh` |
| `lint:forbidden-strings` | No forbidden tokens (createdAt, UUID, snake_case columns, legacy paths) appear anywhere in the repo. | `python3 linter-scripts/check-forbidden-strings.py` |
| `lint:guidelines-go` | Zero CODE-RED violations: functions ≤ 15 lines, files ≤ 300 lines, no nested ifs, max 2 boolean operands. | `go run linter-scripts/validate-guidelines.go --path spec --max-lines 15` |
| `lint:guidelines-py` | Python-side guideline validator agrees with the Go validator on every rule. | `python3 linter-scripts/validate-guidelines.py spec` |
| `lint:powershell` | PowerShell scripts pass PSScriptAnalyzer at Warning severity or higher. | `pwsh -NoProfile -Command "Invoke-ScriptAnalyzer -Path scripts -Recurse -Severity Warning"` |
| `lint:spec-folders` | Every spec folder has the required 00-overview.md and follows kebab-case numeric prefixes. | `python3 linter-scripts/check-spec-folder-refs.py` |
| `lint:spec-links` | Every internal markdown link in spec/ resolves to an existing file and heading anchor. | `python3 linter-scripts/check-spec-cross-links.py --root spec --repo-root .` |

### 🧪 Test

| Key | Asserts | Command |
|-----|---------|---------|
| `test:build` | Production Vite build completes without errors or type failures. | `npm run build` |
| `test:unit` | Vitest unit suite passes with zero failures. | `npm run test` |

### 🗄️ Schema

| Key | Asserts | Command |
|-----|---------|---------|
| `schema:db` | DDL conforms to PascalCase singular table names, integer PKs, no forbidden tokens (createdAt/UUID/snake_case). | `python3 linter-scripts/check-forbidden-strings.py` |
| `schema:spec-tree` | src/data/specTree.json is in sync with the on-disk spec/ tree. | `node scripts/sync-spec-tree.mjs && git diff --exit-code -- src/data/specTree.json` |
| `schema:version` | version.json structural content matches package.json (volatile git/updated fields ignored). | `node scripts/sync-version.mjs` |

### 🧭 Meta (composites)

| Key | Asserts | Command |
|-----|---------|---------|
| `meta:full-ci` | Sync drift, lint, and unit tests all pass — equivalent to the merge-blocking CI gate. | `npm run sync && npm run lint && npm run test` |
| `meta:spec-health` | Spec tree is structurally valid AND every internal cross-reference resolves. | `python3 linter-scripts/check-spec-folder-refs.py && python3 linter-scripts/check-spec-cross-links.py --root spec --repo-root .` |


---

## 3. Where each template is used

Folder profiles (in `profiles.mjs`) reference template keys via the
`commandKeys` field. The injector composes them with `&&`:

| Folder | AC tag | Templates used |
|--------|--------|----------------|
| `01-spec-authoring-guide` | `AC-SAG` | `meta:spec-health` |
| `02-coding-guidelines` | `AC-CG` | `lint:guidelines-go`, `lint:guidelines-py` |
| `03-error-manage` | `AC-ERR` | `lint:forbidden-strings`, `lint:guidelines-go` |
| `04-database-conventions` | `AC-DB` | `schema:db` |
| `05-split-db-architecture` | `AC-SDB` | `lint:spec-links` |
| `06-seedable-config-architecture` | `AC-CFG` | `lint:spec-links` |
| `07-design-system` | `AC-DS` | `lint:eslint` |
| `08-docs-viewer-ui` | `AC-UI` | `test:unit` |
| `09-code-block-system` | `AC-CB` | `test:unit` |
| `10-research` | `AC-RES` | `lint:spec-folders` |
| `11-powershell-integration` | `AC-PS` | `lint:powershell` |
| `12-cicd-pipeline-workflows` | `AC-CI` | `meta:full-ci` |
| `13-generic-cli` | `AC-CLI` | `lint:guidelines-go` |
| `14-update` | `AC-UPD` | `lint:spec-links` |
| `15-distribution-and-runner` | `AC-DIST` | `lint:spec-links` |
| `16-generic-release` | `AC-REL` | `lint:spec-links` |
| `17-consolidated-guidelines` | `AC-CON` | `lint:spec-links` |
| `18-wp-plugin-how-to` | `AC-WP` | `lint:spec-links` |
| `21-app` | `AC-APP` | `test:unit` |
| `22-app-issues` | `AC-AI` | `lint:spec-links` |
| `23-app-db` | `AC-ADB` | `schema:db` |
| `24-app-ui-design-system` | `AC-ADS` | `lint:eslint`, `test:unit` |

---

## 4. Adding a template

1. Add an entry to `COMMAND_TEMPLATES` in `command-templates.mjs` with a
   stable kebab-case key (e.g. `lint:new-thing`).
2. If it answers a recurring need, register it in `VERIFICATION_NEED_MAP`.
3. Reference it from any folder profile via `commandKeys: ["lint:new-thing"]`.
4. Run `npm run spec:verify:docs && npm run spec:verify:inject`.

_Generated by `scripts/spec-verification/generate-templates-doc.mjs`._
