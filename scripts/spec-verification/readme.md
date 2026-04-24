# Spec Verification Injector

Batch generator that inserts (or refreshes) a topic-appropriate
`## Verification` section into every prose markdown file under `spec/`.

## Why

Each spec file should end with a deterministic, machine-checkable
acceptance test. Hand-writing one per file produces boilerplate; this
generator keeps content minimal and topic-aware by sourcing each
section from a **folder profile**.

## Files

| File | Purpose |
|------|---------|
| `inject-verification-sections.mjs` | The injector. Walks `spec/`, replaces or appends `## Verification`. |
| `profiles.mjs` | One profile per top-level spec folder (tag, Given/When/Then templates, command). |

## Usage

```bash
# Plan only — no writes
npm run spec:verify:inject:dry

# Apply
npm run spec:verify:inject

# Restrict to a single folder
node scripts/spec-verification/inject-verification-sections.mjs --only 04-database

# Machine-readable report
node scripts/spec-verification/inject-verification-sections.mjs --json
```

## Behaviour

- **Idempotent**: replaces any existing `## Verification` block (from the
  preceding `---` separator down to EOF). Running twice writes nothing.
- **Skipped basenames**: `00-overview.md`, `97-acceptance-criteria.md`,
  `99-consistency-report.md`, `readme.md`, `changelog.md`, plus all
  spec-root files at depth 1.
- **AC tag derivation**: `<profile.tag>-<file-prefix>[a|b|c…]`, where the
  letter suffix marks subfolder depth so siblings under nested folders
  don't collide.

## Adding a new folder profile

Append an entry to `FOLDER_PROFILES` in `profiles.mjs`:

```js
"25-new-folder": {
  tag: "AC-NEW",
  title: (s) => `New conformance: ${s}`,
  given: () => "Run the new linter against …",
  when: "Run the verification command shown below.",
  then: () => "Concrete, machine-checkable assertion.",
  command: "python3 linter-scripts/check-new-thing.py",
},
```

Files in folders without an explicit profile fall back to
`DEFAULT_PROFILE` (a generic spec-health-check section).