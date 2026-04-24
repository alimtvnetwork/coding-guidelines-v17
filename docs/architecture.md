# Architecture, Folder Structure & Decisions

> **Version:** <!-- STAMP:VERSION -->4.15.0<!-- /STAMP:VERSION -->
> **Updated:** <!-- STAMP:UPDATED -->2026-04-24<!-- /STAMP:UPDATED -->
> **Stats:** <!-- STAMP:FILES -->612<!-- /STAMP:FILES --> spec files across <!-- STAMP:FOLDERS -->22<!-- /STAMP:FOLDERS --> top-level folders (<!-- STAMP:LINES -->131,969<!-- /STAMP:LINES --> lines).

---

## Spec Authoring Conventions

Every spec folder follows strict conventions defined in [`spec/01-spec-authoring-guide/`](../spec/01-spec-authoring-guide/00-overview.md).

### Folder Rules

| Rule | Convention |
|------|-----------|
| **Naming** | `{NN}-{kebab-case-name}/` — numeric prefix + lowercase kebab-case |
| **Entry point** | Every folder MUST have `00-overview.md` |
| **Health check** | Every folder MUST have `99-consistency-report.md` |
| **File limit** | Target 300 lines per file (soft limit 400) |
| **Numbering gaps** | Intentional — allows future insertions without renaming |

### Required Metadata (every `00-overview.md`)

```markdown
# Module Name

**Version:** X.Y.Z
**Updated:** YYYY-MM-DD
**AI Confidence:** Low | Medium | High | Production-Ready
**Ambiguity:** None | Low | Medium | High | Critical

## Keywords
`keyword-1` · `keyword-2` · `keyword-3`

## Scoring
| Criterion | Status |
|-----------|--------|
| `00-overview.md` present | ✅ |
| AI Confidence assigned   | ✅ |
| Ambiguity assigned       | ✅ |
| Keywords present         | ✅ |
| Scoring table present    | ✅ |
```

### Cross-References

- **Always** use file-relative paths (`../03-golang/00-overview.md`)
- **Never** use root-relative paths
- **Always** include `.md` extension
- **Always** use lowercase kebab-case in paths

### File Naming

| Type | Pattern | Example |
|------|---------|---------|
| Overview | `00-overview.md` | Every folder |
| Spec content | `{NN}-{kebab-case}.md` | `02-boolean-principles.md` |
| Acceptance criteria | `97-acceptance-criteria.md` | Testable requirements |
| Changelog | `98-changelog.md` | Version history |
| Consistency report | `99-consistency-report.md` | Health self-assessment |

---

## Folder Structure (top-level)

The full tree is regenerated into [`src/data/specTree.json`](../src/data/specTree.json) by `scripts/sync-spec-tree.mjs`. Top-level layout:

```
spec/
├── 01-spec-authoring-guide/        # How to write specs (meta-guide)
├── 02-coding-guidelines/           # Cross-language + per-language coding rules
├── 03-error-manage/                # Error management architecture (apperror, envelope, registry)
├── 04-database-conventions/        # PascalCase schema, FK patterns, view conventions
├── 05-split-db-architecture/       # Root / App / Session SQLite hierarchy
├── 06-seedable-config-architecture/# config.seed.json + GORM merge strategy
├── 07-design-system/               # AI-adaptable design tokens
├── 08-docs-viewer-ui/              # Spec viewer React app
├── 09-code-block-system/           # Markdown code-fence rendering
├── 10-research/                    # Open research notes
├── 11-powershell-integration/      # Cross-platform PowerShell runner
├── 12-cicd-pipeline-workflows/     # GitHub Actions / CI patterns
├── 13-generic-cli/                 # Reusable CLI scaffolding spec
├── 14-update/                      # Self-update with rename-first deploy
├── 15-distribution-and-runner/     # Bundle + runner separation (Phase 6B module)
├── 16-generic-release/             # Versioned release pipeline
├── 17-consolidated-guidelines/     # Master consolidated reference
├── 18-wp-plugin-how-to/            # WordPress plugin Gold Standard
├── 21-app/ … 24-app-design-system-and-ui/   # App-local specs (never synced from gitmap)
└── health-dashboard.md             # Global self-assessment
```

Numeric prefix gaps (e.g. 19, 20, 25–) are intentional and reserved for future insertions.

---

## Architecture Decisions

### Why This Structure Exists

| Decision | Rationale |
|----------|-----------|
| **Specs as product, not afterthought** | Documentation debt compounds faster than code debt. Investing upfront prevents drift. |
| **300-line file limit** | Matches AI context window constraints. Forces decomposition. Easier to review. |
| **Numeric prefixes** | Enforces reading order. Allows insertions without renaming. Mirrors Go package patterns. |
| **Cross-language first** | 70%+ of rules are language-agnostic. DRY principle applied to specs themselves. |
| **Consistency reports** | Self-validating specs. Each folder knows if it's healthy without external tooling. |
| **Archive, don't delete** | `_archive/` folders preserve history. Merged content has audit trail. |
| **Enum deduplication** | One canonical source per pattern. Other files link to it. Prevents drift when updating. |

### Consolidation History

The system was consolidated from 5 separate legacy sources into one canonical structure:

| Legacy Source | Status | Merged Into |
|---------------|--------|-------------|
| Pre-code review guides | ✅ Archived | Cross-language guidelines |
| WPOnboard format guidelines | ✅ Archived | Language-specific files |
| WorkFlowy master guidelines | ✅ Archived | Master + AI optimization |
| Standalone Go enum spec | ✅ Archived | Go enum specification |
| Scattered per-file rules | ✅ Archived | Centralized cross-language rules |

---

## Error Management Summary

The error management system is built around three pillars, battle-tested in the **[Riseup Asia](https://riseup-asia.com/) WordPress onboarding platform** (`riseup-asia-uploader` plugin):

1. **Error Resolution** (`01-error-resolution/`) — retrospectives, verification patterns, debugging guides for Go and TypeScript.
2. **Error Architecture** (`02-error-architecture/`) — `apperror` package, response envelope, error modal, structured logging.
3. **Error Code Registry** (`03-error-code-registry/`) — centralized catalog, JSON Schemas, collision detection, templates.

Full reference: [`spec/03-error-manage/00-overview.md`](../spec/03-error-manage/00-overview.md). Complete `apperror` constructor catalogue and Response Envelope JSON examples live under [`02-error-architecture/06-apperror-package/`](../spec/03-error-manage/02-error-architecture/06-apperror-package/00-overview.md) and [`02-error-architecture/05-response-envelope/`](../spec/03-error-manage/02-error-architecture/05-response-envelope/00-overview.md).

---

## Health Dashboard & Spec Index

- [Health Dashboard](../spec/health-dashboard.md) — global self-assessment across all spec folders.
- [`src/data/specTree.json`](../src/data/specTree.json) — machine-readable tree (auto-generated).
- [`version.json`](../version.json) — single source of truth for live counts and per-folder metadata.

Every folder scores itself on 4 criteria (25 points each): `00-overview.md` present with required metadata, AI Confidence assigned, Ambiguity assessed, Keywords + scoring table included.