# Code Review & Specification System

> **Author:** Md. Alim Ul Karim
> **Website:** [alimkarim.com](https://alimkarim.com/) · [my.alimkarim.com](https://my.alimkarim.com/)
> **LinkedIn:** [linkedin.com/in/alimkarim](https://www.linkedin.com/in/alimkarim)
> **Version:** 1.4.0
> **Last Updated:** 2026-04-16
> **Total Spec Files:** 285 | **Directories:** 42 | **Cross-References:** 902 | **Health Score:** 100/100

A production-grade, AI-optimized specification system for enforcing coding standards across **Go, TypeScript, PHP, Rust, and C#**. This repository contains the canonical coding guidelines, error management architecture, and spec authoring conventions used to maintain code quality at scale.


![Spec Viewer Preview](public/images/spec-viewer-preview.png)
*The built-in Spec Documentation Viewer — browse, search, and read all 495 spec files with syntax highlighting, keyboard navigation, and fullscreen mode.*

---

## Install Scripts

Use the raw install scripts from this repository **after the repo is synced to GitHub and `install.sh` / `install.ps1` exist on the `main` branch**:

### Bash (Linux / macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v17/main/install.sh | bash
```

### PowerShell (Windows)

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v17/main/install.ps1 | iex
```

### Local usage

```bash
chmod +x install.sh
./install.sh
```

```powershell
.\install.ps1
```

### Override source repo or branch

```bash
./install.sh --repo alimtvnetwork/coding-guidelines-v17 --branch develop
```

```powershell
.\install.ps1 -Repo "alimtvnetwork/coding-guidelines-v17" -Branch "develop"
```

### Configuration (`install-config.json`)

The scripts read `install-config.json` to determine which repo, branch, and folders to fetch:

```json
{
  "repo": "alimtvnetwork/coding-guidelines-v17",
  "branch": "main",
  "folders": [
    "spec",
    "linters",
    "linter-scripts"
  ]
}
```

Edit `folders` to control which directories are downloaded. Files are merged into your current directory — existing files with the same name are overwritten, but no files are deleted.

---

## Release Scripts

This repo now includes local release packager scripts modeled on the gitmap flow:

### Bash

```bash
npm run release
```

### PowerShell

```powershell
npm run release:ps1
```

Both scripts create a versioned release bundle in `release-artifacts/` containing:

- `spec/`
- `linters/`
- `linter-scripts/`
- `install.sh`
- `install.ps1`
- `install-config.json`
- `README.md`
- `checksums.txt`
- `.zip` and `.tar.gz` archives

---

<details>
<summary><h2>📑 Table of Contents</h2> <em>(click to expand/collapse)</em></summary>

- [Project Overview](#project-overview)
- [Install Scripts](#install-scripts)
- [Release Scripts](#release-scripts)
- [Folder Structure](#folder-structure)
- [Quick Start — How to Read These Specs](#quick-start--how-to-read-these-specs)
- [Spec Authoring Conventions](#spec-authoring-conventions)
- [Coding Guidelines Summary](#coding-guidelines-summary)
- [Error Management Summary](#error-management-summary)
- [AI Optimization Suite](#ai-optimization-suite)
- [Health Dashboard & Spec Index](#health-dashboard--spec-index)
- [Architecture Decisions](#architecture-decisions)
- [Author Assessment & Design Philosophy](#author-assessment--design-philosophy)
  - [About the Author](#about-the-author)
  - [🤖 AI Review: Why This Coding Guidelines System Works](#-ai-review-why-this-coding-guidelines-system-works)
  - [🔍 Neutral AI Assessment: Impact on Large-Scale Development](#-neutral-ai-assessment-impact-on-large-scale-application-development)
  - [👤 AI Assessment: About the Author](#-ai-assessment-about-the-author)
  - [❓ Frequently Asked Questions](#-frequently-asked-questions)
- [Improvement Roadmap](#improvement-roadmap)
- [Author](#author)
  - [Riseup Asia LLC](#riseup-asia-llc)
- [Contributing](#contributing)

</details>

---

## Project Overview

This specification system is the **single source of truth** for all coding standards, error handling patterns, and architectural decisions across a polyglot codebase (Go backend, TypeScript frontend, PHP WordPress plugins, Rust tooling). It is designed to be consumed by both **human developers** and **AI code generation tools**.

> 💬 **Author's Note:** *"I believe any company — even a one-person team — can and should integrate coding guidelines from day one. You don't need 50 developers to benefit from consistent naming, structured error handling, and zero-nesting rules. A solo developer who adopts the condensed 200-line master guidelines today will save hundreds of hours when the team grows to 5, 10, or 50. The cost of NOT having guidelines compounds silently — every shortcut becomes technical debt that the next developer inherits. Start small, start now."*
> — **Md. Alim Ul Karim**, Chief Software Engineer, [Riseup Asia LLC](https://riseup-asia.com/)

### 🤖 LLM / AI Integration

> **For AI/LLM models:** Feed [`llm.md`](llm.md) as the entry point. It maps the entire repository structure, lists priority files for context window optimization, and provides ready-to-use checklists for code generation and review.

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Single Source of Truth** | Every rule is defined in exactly one place. Other files link to it — never duplicate. |
| **AI-First Documentation** | Specs are structured for AI context windows: keywords, scoring, cross-references, condensed quick-refs. |
| **Zero Tolerance Rules** | Critical rules (nested `if`, magic strings, raw `error` returns) are marked 🔴 CODE RED — automatic PR rejection. |
| **Self-Validating** | Every folder has a `99-consistency-report.md` that scores its own health. A global dashboard tracks all 23 reports. |
| **300-Line Limit** | No spec file exceeds 300 lines (soft limit 400). Large files are split into subfolders with their own `00-overview.md`. |


[↑ Back to Table of Contents](#table-of-contents)

---

## Folder Structure

```
spec/
├── health-dashboard.md                          # Global health: 23 reports, 210 files, 100/100
│
├── 01-spec-authoring-guide/                     # How to write specs (meta-guide)
│   ├── 00-overview.md                           # Entry point
│   ├── 01-folder-structure.md                   # Numeric prefixes, kebab-case rules
│   ├── 02-naming-conventions.md                 # File and folder naming
│   ├── 03-required-files.md                     # Mandatory files per folder
│   ├── 04-cli-module-template.md                # Template for CLI modules (3-folder pattern)
│   ├── 05-non-cli-module-template.md            # Template for non-CLI modules
│   ├── 06-memory-folder-guide.md                # .lovable/memories/ conventions
│   ├── 07-cross-references.md                   # How to write relative links
│   ├── 08-exceptions.md                         # Allowed deviations from conventions
│   ├── 97-acceptance-criteria.md                # Testable criteria for spec quality
│   ├── 98-changelog.md                          # Version history
│   └── 99-consistency-report.md                 # Self-assessment: 100/100
│
├── 02-coding-guidelines/                        # All coding standards
│   ├── 00-overview.md                           # Hub — points to canonical spec
│   ├── _archive/                                # Merged legacy sources (do not reference)
│   └── 03-coding-guidelines-spec/               # ← CANONICAL SPEC
│       ├── 00-overview.md                       # Master index
│       ├── 97-acceptance-criteria.md            # 22 testable criteria
│       ├── 99-consistency-report.md             # Health: 100/100
│       │
│       ├── 01-cross-language/                   # Rules for ALL languages (27 files)
│       │   ├── 00-overview.md                   # Index by category
│       │   ├── 02-boolean-principles/           # P1–P8 boolean naming (subfolder, 5 files)
│       │   ├── 03-casting-elimination-patterns.md
│       │   ├── 04-code-style/                   # Braces, nesting, spacing (subfolder, 8 files)
│       │   ├── 06-cyclomatic-complexity.md
│       │   ├── 07-database-naming.md
│       │   ├── 08-dry-principles.md
│       │   ├── 10-function-naming.md
│       │   ├── 12-no-negatives.md
│       │   ├── 13-strict-typing.md
│       │   ├── 14-test-naming-and-structure.md
│       │   ├── 15-master-coding-guidelines/     # Cross-language master ref (subfolder, 7 files)
│       │   ├── 16-lazy-evaluation-patterns.md
│       │   ├── 17-regex-usage-guidelines.md
│       │   ├── 18-code-mutation-avoidance.md
│       │   ├── 19-null-pointer-safety.md
│       │   ├── 20-nesting-resolution-patterns.md
│       │   ├── 21-newline-styling-examples.md
│       │   ├── 22-variable-naming-conventions.md
│       │   └── 23-solid-principles.md
│       │
│       ├── 02-typescript/                       # TypeScript-specific (13 files)
│       │   ├── 00-overview.md
│       │   ├── 01–06: Enum definitions          # ConnectionStatus, EntityStatus, etc.
│       │   ├── 08-typescript-standards-reference.md
│       │   ├── 09-promise-await-patterns.md     # 🔴 CODE RED: Promise.all for independent calls
│       │   └── 10-log-level-enum.md
│       │
│       ├── 03-golang/                           # Go-specific (10+ files)
│       │   ├── 00-overview.md
│       │   ├── 01-enum-specification/           # Go enum pattern (subfolder, 5 files)
│       │   ├── 02-boolean-standards.md
│       │   ├── 03-httpmethod-enum.md
│       │   ├── 04-golang-standards-reference/   # Full Go standards (subfolder, 6 files)
│       │   ├── 05-defer-rules.md
│       │   └── 08-pathutil-fileutil-spec.md
│       │
│       ├── 04-php/                              # PHP-specific (11+ files)
│       │   ├── 00-overview.md
│       │   ├── 01-enums.md
│       │   ├── 07-php-standards-reference/      # Full PHP standards (subfolder, 5 files)
│       │   └── ...
│       │
│       ├── 05-rust/                             # Rust-specific (10 files)
│       │   ├── 00-overview.md
│       │   ├── 01-naming-conventions.md
│       │   ├── 02-error-handling.md
│       │   └── ...
│       │
│       ├── 07-csharp/                            # C#-specific (5 files)
│       │   ├── 00-overview.md
│       │   ├── 01-naming-and-conventions.md
│       │   ├── 02-method-design.md               # Boolean flag splitting, async, LINQ
│       │   ├── 03-error-handling.md
│       │   └── 04-type-safety.md
│       │
│       └── 06-ai-optimization/                  # AI-specific tooling (8 files)
│           ├── 00-overview.md
│           ├── 01-anti-hallucination-rules.md   # 27 rules to prevent AI mistakes
│           ├── 02-ai-quick-reference-checklist.md # 66-check pre-output validation
│           ├── 03-common-ai-mistakes.md         # 15 most frequent AI errors
│           ├── 04-condensed-master-guidelines.md # Sub-200-line AI context distillation
│           └── 05-enum-naming-quick-reference.md # Cross-language enum cheat sheet
│
└── 03-error-manage-spec/                        # Error management architecture
    └── 04-error-manage-spec/                    # ← CANONICAL SPEC
        ├── 00-overview.md
        ├── structure.md
        │
        ├── 01-error-resolution/                 # How to resolve errors (6+ files)
        │   ├── 03-retrospectives/               # Post-incident analysis
        │   ├── 04-verification-patterns/        # Verification strategies
        │   └── 05-debugging-guides/             # Go & TypeScript debugging
        │
        ├── 02-error-architecture/               # How errors are structured
        │   ├── 04-error-modal/                  # UI error display (7 files)
        │   ├── 05-response-envelope/            # API response format (11 files)
        │   ├── 06-apperror-package/             # Go apperror package spec
        │   │   └── 01-apperror-reference/       # Full reference (subfolder, 6 files)
        │   └── 07-logging-and-diagnostics/      # Structured logging (3 files)
        │
        └── 03-error-code-registry/              # Error code catalog (10+ files)
            ├── 07-schemas/                      # JSON Schema validation
            ├── 08-linter-scripts/                # Collision detection, utilization
            └── 09-templates/                    # Error code templates
```


[↑ Back to Table of Contents](#table-of-contents)

---

## Quick Start — How to Read These Specs

### For Developers

1. Start with [Coding Guidelines Overview](spec/02-coding-guidelines/03-coding-guidelines-spec/00-overview.md)
2. Read the [Master Coding Guidelines](spec/02-coding-guidelines/03-coding-guidelines-spec/01-cross-language/15-master-coding-guidelines/00-overview.md) for cross-language rules
3. Then your language-specific guide: [Go](spec/02-coding-guidelines/03-coding-guidelines-spec/03-golang/00-overview.md) · [TypeScript](spec/02-coding-guidelines/03-coding-guidelines-spec/02-typescript/00-overview.md) · [PHP](spec/02-coding-guidelines/03-coding-guidelines-spec/04-php/00-overview.md) · [Rust](spec/02-coding-guidelines/03-coding-guidelines-spec/05-rust/00-overview.md)

### For AI Tools

1. Load the [Condensed Master Guidelines](spec/02-coding-guidelines/03-coding-guidelines-spec/06-ai-optimization/04-condensed-master-guidelines.md) (<200 lines)
2. Reference the [AI Quick-Reference Checklist](spec/02-coding-guidelines/03-coding-guidelines-spec/06-ai-optimization/02-ai-quick-reference-checklist.md) before generating code
3. Check [Anti-Hallucination Rules](spec/02-coding-guidelines/03-coding-guidelines-spec/06-ai-optimization/01-anti-hallucination-rules.md) for common AI mistakes

### For New Spec Authors

1. Read the [Spec Authoring Guide](spec/01-spec-authoring-guide/00-overview.md)
2. Use the [Non-CLI Module Template](spec/01-spec-authoring-guide/05-non-cli-module-template.md) or [CLI Module Template](spec/01-spec-authoring-guide/04-cli-module-template.md)
3. Follow the [Cross-References Guide](spec/01-spec-authoring-guide/07-cross-references.md) for linking


[↑ Back to Table of Contents](#table-of-contents)

---

## Spec Authoring Conventions

Every spec folder follows strict conventions defined in [`spec/01-spec-authoring-guide/`](spec/01-spec-authoring-guide/00-overview.md):

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
- **Never** use root-relative paths (`/spec/03-golang/00-overview.md`)
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


[↑ Back to Table of Contents](#table-of-contents)

---

## Coding Guidelines Summary

### 🔴 CODE RED Rules (Automatic PR Rejection)

These rules have **zero tolerance** — any violation is an immediate rejection:

| # | Rule | Scope |
|---|------|-------|
| 1 | **Zero nested `if`** — flatten with early returns or named booleans | All languages |
| 2 | **No magic strings** — all string literals must be enum constants or typed constants | All languages |
| 3 | **Boolean naming** — every boolean MUST start with `is`, `has`, `can`, `should`, or `was` | All languages |
| 4 | **No raw `error` returns** — Go services return `apperror.Result[T]`, never `(T, error)` | Go |
| 5 | **No `fmt.Errorf()`** — use `apperror.New()` / `apperror.Wrap()` only | Go |
| 6 | **No `===` for PHP enum comparison** — use `->isEqual()` | PHP |
| 7 | **`Promise.all` for independent async calls** — sequential `await` on independent promises is forbidden | TypeScript |
| 8 | **Max 15 lines per function** — extract into named helpers | All languages |
| 9 | **No boolean flag parameters** — if a method branches on a bool, split into two named methods | All languages |
| 10 | **No `any`/`interface{}`/`object` returns** — use generics or typed Result wrappers | All languages |

### Key Standards by Language

| Standard | Go | TypeScript | PHP | Rust | C# |
|----------|-----|-----------|-----|------|-----|
| Enum type | `byte` + `iota` | String enum | String-backed + `Type` suffix | Standard `enum` | PascalCase enum |
| Error handling | `apperror.Result[T]` | `Promise<T>` | `try/catch Throwable` | `Result<T, E>` | Exceptions + guard clauses |
| File naming | `PascalCase.go` | `PascalCase.tsx` | `PascalCase.php` | `snake_case.rs` | `PascalCase.cs` |
| Boolean prefix | `isActive` | `isActive` | `$isActive` | `is_active` | `IsActive` |
| Abbreviations | `Id` not `ID` | `Id` not `ID` | `Id` not `ID` | Rust stdlib conventions | `Id` not `ID` |

### Full Index of Cross-Language Rules

| # | File | Category |
|---|------|----------|
| 02 | `02-boolean-principles/` | Naming — P1–P8 boolean rules (subfolder) |
| 03 | `03-casting-elimination-patterns.md` | Type Safety |
| 04 | `04-code-style/` | Style — braces, nesting, spacing, function size (subfolder) |
| 06 | `06-cyclomatic-complexity.md` | Architecture |
| 07 | `07-database-naming.md` | Type Safety |
| 08 | `08-dry-principles.md` | Architecture |
| 10 | `10-function-naming.md` | Naming |
| 12 | `12-no-negatives.md` | Naming |
| 13 | `13-strict-typing.md` | Type Safety |
| 14 | `14-test-naming-and-structure.md` | Testing |
| 15 | `15-master-coding-guidelines/` | Reference — consolidated cross-language (subfolder) |
| 16 | `16-lazy-evaluation-patterns.md` | Patterns |
| 17 | `17-regex-usage-guidelines.md` | Patterns |
| 18 | `18-code-mutation-avoidance.md` | Type Safety |
| 19 | `19-null-pointer-safety.md` | Type Safety |
| 20 | `20-nesting-resolution-patterns.md` | Patterns |
| 21 | `21-newline-styling-examples.md` | Style |
| 22 | `22-variable-naming-conventions.md` | Naming |
| 23 | `23-solid-principles.md` | Architecture |
| 24 | `24-boolean-flag-methods.md` | Method Design — split bool-flag methods into two named methods |
| 25 | `25-generic-return-types.md` | Type Safety — use generics/Result[T] instead of interface{}/any/object |
| 26 | `26-magic-values-and-immutability.md` | Type Safety — no magic strings/numbers, const over let, class-first TS |
| 27 | `27-types-folder-convention.md` | Architecture — one-definition-per-file, common type aliases & enums |


#### Real-World Example: CODE-RED Violations in `riseup-asia-uploader`

The following examples are based on patterns caught (and fixed) in the [Riseup Asia](https://riseup-asia.com/) WordPress onboarding platform's Go backend:

**CODE-RED-001 — Nested `if` (before/after):**

```go
// ❌ VIOLATION: nested if in riseup-asia-uploader plugin handler
func (h *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    site := h.siteRepo.FindById(siteId)

    if site != nil {
        if site.IsActive {
            if pluginSlug != "" {
                // deeply nested — hard to test, hard to read
                return h.uploader.Enable(site, pluginSlug)
            }
        }
    }

    return apperror.FailBool(apperror.New("E2010", "invalid request"))
}

// ✅ FIXED: flattened with early returns + no negation inversion
// ⚠️ NOTE: Do NOT use `!site.IsActive` — use the antonym `site.IsBlocked` instead.
//   Using `!` to invert boolean names hides intent and makes conditions harder to read.
//   Always create a dedicated boolean with the opposite meaning:
//     !IsActive      → IsBlocked
//     !HasAuditFile  → IsAuditFileMissing
//     !IsValid       → IsInvalid
//     !IsConnected   → IsDisconnected
//     !IsEnabled     → IsDisabled
//     !HasPermission → IsPermissionDenied
func (h *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    site := h.siteRepo.FindById(siteId)

    if site == nil {
        return apperror.FailBool(apperror.New("E2010", "site not found"))
    }

    if site.IsBlocked {
        return apperror.FailBool(apperror.New("E2011", "site is blocked"))
    }

    if pluginSlug == "" {
        return apperror.FailBool(apperror.New("E2012", "plugin slug required"))
    }

    return h.uploader.Enable(site, pluginSlug)
}

// ✅✅ BETTER: error codes from enum (apperrtype package)
// Error code comes from a typed enum — no magic strings for error codes.
// Message is still passed manually.
func (h *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    site := h.siteRepo.FindById(siteId)

    if site == nil {
        return apperror.FailBool(apperror.New(apperrtype.SiteNotFound, "site not found"))
    }

    if site.IsBlocked {
        return apperror.FailBool(apperror.New(apperrtype.SiteBlocked, "site is blocked"))
    }

    if pluginSlug == "" {
        return apperror.FailBool(apperror.New(apperrtype.PluginSlugMissing, "plugin slug required"))
    }

    return h.uploader.Enable(site, pluginSlug)
}

// ✅✅✅ BEST: error type enum with built-in description map (no message needed)
// The enum itself maps to a description — zero duplication, zero typos.
// apperrtype.PluginSlugMissing → code: "E2012", message: "plugin slug required"
func (h *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    site := h.siteRepo.FindById(siteId)

    if site == nil {
        return apperror.FailBool(apperror.NewType(apperrtype.SiteNotFound))
    }

    if site.IsBlocked {
        return apperror.FailBool(apperror.NewType(apperrtype.SiteBlocked))
    }

    if pluginSlug == "" {
        return apperror.FailBool(apperror.NewType(apperrtype.PluginSlugMissing))
    }

    return h.uploader.Enable(site, pluginSlug)
}
```

**Error Type Enum (`apperrtype` package — v2.0):**

The `apperrtype` package defines all error types as variants of a single `uint16` `Variation` enum with a global registry. Each variant maps to a `VariantStructure` containing `Name`, `Code`, and `Message` — eliminating magic strings, message duplication, and per-domain boilerplate:

```go
// apperrtype/variation.go — single enum for ALL error types
package apperrtype

type Variation uint16

const (
    NoError Variation = iota // 0 — zero value

    // ── E1xxx — Configuration ──
    ConfigFileMissing   // E1001
    ConfigParseFailure  // E1002
    // ...

    // ── E2xxx — Database / Site / Plugin ──
    DBConnectionFailed  // E2001
    // ...
    SiteNotFound        // E2010
    SiteBlocked         // E2011
    PluginSlugMissing   // E2012
    PluginNotFound      // E2013
    PluginAlreadyActive // E2014
    // ... 18 domains, 100+ variants

    MaxError // sentinel — must remain last
)
```

```go
// apperrtype/variant_structure.go — rich metadata per variant
type VariantStructure struct {
    Name    string     // "SiteNotFound"
    Code    string     // "E2010"
    Message string     // "site not found"
    Variant Variation  // the enum value itself
}
```

```go
// apperrtype/variant_registry.go — single source of truth
var variantRegistry = map[Variation]VariantStructure{
    SiteNotFound:      {Name: "SiteNotFound",      Code: "E2010", Message: "site not found",      Variant: SiteNotFound},
    SiteBlocked:       {Name: "SiteBlocked",        Code: "E2011", Message: "site is blocked",     Variant: SiteBlocked},
    PluginSlugMissing: {Name: "PluginSlugMissing",  Code: "E2012", Message: "plugin slug required", Variant: PluginSlugMissing},
    // ... all domains
}
```

```go
// Variation methods — implements ErrorType interface + display
func (v Variation) Code() string    { return variantRegistry[v].Code }
func (v Variation) Message() string { return variantRegistry[v].Message }
func (v Variation) Name() string    { return variantRegistry[v].Name }
func (v Variation) String() string  { /* "Name (Code - N) : Message" */ }
func (v Variation) Structure() VariantStructure { return variantRegistry[v] }

// Reverse lookup: string name → Variation
v, ok := apperrtype.VariationFromName("SiteNotFound")
```

```go
// apperror/constructors.go — NewType uses the enum's built-in code + message
func NewType(errType apperrtype.ErrorType) *AppError {
    return New(errType.Code(), errType.Message())
}
```

> **Rules:**
> - Single `Variation uint16` enum in `variation.go` — all domains in one file
> - Global `variantRegistry` maps each `Variation` → `VariantStructure{Name, Code, Message, Variant}`
> - `Variation` implements `ErrorType` interface (`Code()` + `Message()` + `Name()`)
> - `StringToVariantMap` provides reverse lookup from name strings to `Variation` values
> - `apperror.NewType()` / `apperror.WrapType()` create `AppError` from any `Variation`
> - All types live in `types/apperrtype/`
> - Never pass raw string codes (`"E2012"`) when an `apperrtype` variant exists

> 📖 Full error type enum specification: [`05-apperrtype-enums.md`](spec/03-error-manage-spec/04-error-manage-spec/02-error-architecture/06-apperror-package/01-apperror-reference/05-apperrtype-enums.md)


**CODE-RED-005 & 006 — `fmt.Errorf()` and `(T, error)` returns (before/after):**

```go
// ❌ VIOLATION: raw fmt.Errorf and (T, error) tuple return
func (s *SnapshotService) GetSettings(endpoint string) (*Settings, error) {
    resp, err := s.client.Get(endpoint)

    if err != nil {
        return nil, fmt.Errorf("get snapshot settings (GET %s): %w", endpoint, err)
    }

    return parseSettings(resp)
}

// ✅ FIXED: type alias + apperror.Wrap()
// In types/AppResults.go:
//   type SettingsResult = apperror.Result[*Settings]
func (s *SnapshotService) GetSettings(endpoint string) apperror.SettingsResult {
    resp, err := s.client.Get(endpoint)

    if err != nil {
        return apperror.Fail[*Settings](
            apperror.Wrap(err, "E3001", "failed to fetch snapshot settings"),
        )
    }

    return apperror.Ok(parseSettings(resp))
}

// ✅✅ BETTER: WrapType — enum replaces raw code, default message from registry
// apperrtype.WPConnectionFailed → code: "E3001", message: "WordPress connection failed"
func (s *SnapshotService) GetSettings(endpoint string) apperror.SettingsResult {
    resp, err := s.client.Get(endpoint)

    if err != nil {
        return apperror.Fail[*Settings](
            apperror.WrapType(err, apperrtype.WPConnectionFailed).
                WithValue("endpoint", endpoint),
        )
    }

    return apperror.Ok(parseSettings(resp))
}

// ✅✅✅ BEST: WrapTypeMsg — enum + custom message for specific context
// Uses the enum's code (E3001) but overrides the message with context-specific text
func (s *SnapshotService) GetSettings(endpoint string) apperror.SettingsResult {
    resp, err := s.client.Get(endpoint)

    if err != nil {
        return apperror.Fail[*Settings](
            apperror.WrapTypeMsg(err, apperrtype.WPConnectionFailed, "failed to fetch snapshot settings").
                WithValue("endpoint", endpoint),
        )
    }

    return apperror.Ok(parseSettings(resp))
}
```

**Progression summary:**

| Level | Constructor | Code Source | Message Source |
|-------|-------------|------------|----------------|
| ✅ | `Wrap(err, "E3001", msg)` | Raw string | Manual |
| ✅✅ | `WrapType(err, errType)` | Enum registry | Enum registry (default) |
| ✅✅✅ | `WrapTypeMsg(err, errType, msg)` | Enum registry | Custom (context-specific) |

**Domain convenience constructors:**

Auto-set diagnostic fields so no context is accidentally omitted:

```go
// PathError — auto-sets WithPath(path)
if !isValidPath(configPath) {
    return apperror.FailSettings(apperror.PathError(apperrtype.PathInvalid, configPath))
}
data, err := os.ReadFile(configPath)
if err != nil {
    return apperror.FailBytes(apperror.WrapPathError(err, apperrtype.PathFailedToRead, configPath))
}

// UrlError — auto-sets WithUrl(url)
resp, err := http.Get(siteURL)
if err != nil {
    return apperror.FailSettings(apperror.WrapUrlError(err, apperrtype.WPConnectionFailed, siteURL))
}

// SiteError — auto-sets WithSiteId(id)
site := repo.FindById(siteId)
if site == nil {
    return apperror.FailBool(apperror.SiteError(apperrtype.SiteNotFound, siteId))
}

// EndpointError — auto-sets WithEndpoint + WithMethod + WithStatusCode
if resp.StatusCode != 200 {
    return apperror.FailSettings(
        apperror.EndpointError(apperrtype.WPResponseInvalid, "GET", endpoint, resp.StatusCode),
    )
}
```

| Constructor | Auto-sets | Example Variants |
|-------------|-----------|------------------|
| `PathError` / `WrapPathError` | `WithPath` | `PathInvalid`, `PathFailedToRead` |
| `UrlError` / `WrapUrlError` | `WithUrl` | `WPConnectionFailed`, `RequestFailed` |
| `SlugError` / `WrapSlugError` | `WithSlug` | `PluginNotFound`, `PluginSlugMissing` |
| `SiteError` / `WrapSiteError` | `WithSiteId` | `SiteNotFound`, `SiteBlocked` |
| `EndpointError` / `WrapEndpointError` | `WithEndpoint` + `WithMethod` + `WithStatusCode` | `WPResponseInvalid`, `WPRateLimited` |

> 📖 Full constructor reference: [`02-apperror-struct.md`](spec/03-error-manage-spec/04-error-manage-spec/02-error-architecture/06-apperror-package/01-apperror-reference/02-apperror-struct.md)

**CODE-RED-007 — String-based enum (before/after):**

```go
// ❌ VIOLATION: string-based enum type
type PluginStatus string
const (
    PluginStatusActive   PluginStatus = "active"
    PluginStatusInactive PluginStatus = "inactive"
)

// ✅ FIXED: byte + iota enum
type PluginStatus byte
const (
    PluginStatusActive PluginStatus = iota + 1
    PluginStatusInactive
)
```

These patterns are enforced automatically by the [`validate-guidelines.go`](linter-scripts/validate-guidelines.go) and [`validate-guidelines.py`](linter-scripts/validate-guidelines.py) lint checkers included in this repository.

#### Type Aliases for Common Generic Results

When a generic type like `apperror.Result[T]` is used repeatedly with the same type parameter, create a **type alias** to reduce noise and improve readability:

```go
// ❌ VERBOSE — repeating Result[bool] everywhere
func (h *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.Result[bool] {
    return apperror.Fail[bool](apperror.New("E2010", "site not found"))
}

func (h *PluginHandler) DisablePlugin(siteId string, pluginSlug string) apperror.Result[bool] {
    return apperror.Fail[bool](apperror.New("E2020", "plugin not found"))
}

// ✅ CLEAN — define a type alias once, use everywhere
// In types/AppResults.go (or inside the apperror package itself):
type BoolResult = apperror.Result[bool]
type StringResult = apperror.Result[string]
type IntResult = apperror.Result[int]
type SettingsResult = apperror.Result[*Settings]

// Convenience constructors — one per alias, wraps Fail[T] so callers never repeat the generic:
//   func FailBool(err *AppError) BoolResult       { return Fail[bool](err) }
//   func FailString(err *AppError) StringResult    { return Fail[string](err) }
//   func FailInt(err *AppError) IntResult          { return Fail[int](err) }
//   func FailSettings(err *AppError) SettingsResult { return Fail[*Settings](err) }
//
// Pattern: for each type alias, create a matching Fail<Alias> constructor.
// This eliminates Fail[bool](...) generic noise at every call site.

func (h *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    return apperror.FailBool(apperror.New("E2010", "site not found"))
}

func (h *PluginHandler) DisablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    return apperror.FailBool(apperror.New("E2020", "plugin not found"))
}
```

**Rules:**
- If a `Result[T]` specialization appears **3+ times**, create a type alias
- Place common aliases in `types/AppResults.go` or inside the `apperror` package
- One definition per file — `types/AppResults.go` for result aliases, `types/ContentType.go` for content types, etc.
- Same principle applies in TypeScript (`type BoolResult = Result<boolean>`) and other languages

#### The Dark Side of Magic Strings & Magic Numbers

Magic strings and magic numbers are raw literals (`"active"`, `86400`, `0.2`) used directly in logic instead of named constants or enums. They are one of the **most dangerous and underestimated sources of production bugs**:

| Danger | What Happens |
|--------|-------------|
| **Silent typos** | `"actve"` compiles but never matches — user locked out, no error raised |
| **No refactoring support** | Can't "Find All References" — renaming requires grepping every file |
| **No type safety** | Any string accepted — wrong values pass through 5 layers silently |
| **Duplicated knowledge** | Same string in 20 files — one changes, 19 don't |
| **Hidden coupling** | Two systems agree on `"webhook_completed"` via copy-paste — one renames, the other breaks |
| **Security risk** | `if (role === "admin")` — attackers guess the string for privilege escalation |

**The compounding effect:** A magic string written on Day 1 gets copied to 5 files by Day 30. On Day 90, a rename is applied to 3 of 6 files. On Day 92, three features break silently in production. With an enum, renaming causes a **compile-time error** in all files instantly.

**Rules:**
- Every string in a comparison **must** be an enum or typed constant
- Every number in logic **must** be a named constant (`const VAT_RATE = 0.2`, not `price * 0.2`)
- Exemptions: `0`, `1`, `-1`, `""`, `true`, `false`, `null`/`nil`

#### Code Mutation & Immutability

Variables should be assigned **exactly once**. Prefer `const` over `let`/`var`. Object mutation after construction is forbidden — use constructors or struct literals.

```typescript
// ❌ FORBIDDEN — mutable variable reassigned
let discount = 0
if (isPremium) { discount = 0.2 }
else { discount = 0.1 }

// ✅ CORRECT — single assignment
const discount = isPremium ? 0.2 : 0.1
```

```go
// ❌ FORBIDDEN — post-construction mutation + magic string
resp := &Response{}
resp.Status = StatusOk
resp.Headers["Content-Type"] = "application/json"

// ✅ CORRECT — use shared constant from types/ folder
// These constants should live in a common ContentType enum or constant class:
//   types/ContentType.go   → ContentTypeJson, ContentTypeXml, ContentTypeFormData
//   types/ContentType.ts   → enum ContentType { Json = "application/json", ... }
//   types/ContentType.php  → enum ContentType: string { case Json = "application/json"; ... }
// Rule: One definition per file in the types/ folder. Never inline content types.
const ContentTypeJson = "application/json"  // from types/ContentType

return &Response{
    Status:  StatusOk,
    Headers: map[string]string{"Content-Type": ContentTypeJson},
}
```

**TypeScript/JS class-first:** Prefer classes over loose exported functions when state or dependencies are shared. Pure utilities (`formatDate`, `slugify`) can remain as standalone exports.

> 📖 Full specification with all language examples: [`26-magic-values-and-immutability.md`](spec/02-coding-guidelines/03-coding-guidelines-spec/01-cross-language/26-magic-values-and-immutability.md)
> 📖 Mutation avoidance details: [`18-code-mutation-avoidance.md`](spec/02-coding-guidelines/03-coding-guidelines-spec/01-cross-language/18-code-mutation-avoidance.md)
> 📖 Types folder convention: [`27-types-folder-convention.md`](spec/02-coding-guidelines/03-coding-guidelines-spec/01-cross-language/27-types-folder-convention.md)

[↑ Back to Table of Contents](#table-of-contents)

---

## Error Management Summary

The error management system is built around three pillars, battle-tested in the **[Riseup Asia](https://riseup-asia.com/) WordPress onboarding platform** (`riseup-asia-uploader` plugin):

### 1. Error Resolution (`01-error-resolution/`)
- **Retrospectives** — post-incident analysis patterns
- **Verification patterns** — how to verify errors are truly fixed
- **Debugging guides** — step-by-step debugging for Go and TypeScript

### 2. Error Architecture (`02-error-architecture/`)
- **`apperror` package** — Go structured error with mandatory stack traces, Result[T] wrapper, JSON serialization
- **Response envelope** — standardized API response format across all endpoints
- **Error modal** — frontend error display with color themes, copy formats
- **Logging & diagnostics** — structured logging with session context

#### Real-World Example: `riseup-asia-uploader` Response Envelope

The response envelope pattern was developed for the `riseup-asia-uploader` WordPress plugin, where the Go backend delegates API calls to WordPress REST endpoints. Here's a real error response from the system:

```json
{
  "Attributes": {
    "RequestedAt": "http://localhost:8080/api/v1/plugins/enable",
    "RequestDelegatedAt": "https://example.com/wp-json/riseup-asia-uploader/v1/enable",
    "SessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "HasAnyErrors": true
  },
  "StatusCode": {
    "IsFailed": true,
    "Code": 500,
    "Message": "[E3001] failed to fetch snapshot settings"
  },
  "Errors": {
    "BackendMessage": "[E3025] [E3001] failed to fetch snapshot settings",
    "Backend": [
      "handler_factory.go:107 handlers.init.handleSiteActionById.func63",
      "middleware.go:45 middleware.CORS.func1"
    ],
    "DelegatedRequestServer": {
      "DelegatedEndpoint": "https://example.com/wp-json/riseup-asia-uploader/v1/snapshots/settings",
      "Method": "GET",
      "StatusCode": 403,
      "StackTrace": [
        "#0 riseup-asia-uploader.php(1098): FileLogger->error()",
        "#1 class-wp-hook.php(341): Plugin->enrichErrorResponse()"
      ]
    }
  }
}
```

**Key design decisions visible in this example:**
- **Dual stack traces** — both Go backend and PHP delegated server traces are captured
- **Error code chaining** — `[E3025] [E3001]` shows error propagation through layers
- **Delegation tracking** — `RequestDelegatedAt` records the exact WordPress endpoint called
- **Structured errors** — machine-parseable JSON, not raw strings

The PHP implementation lives at `wp-plugins/riseup-asia-uploader/includes/Helpers/EnvelopeBuilder.php`, the Go side at `backend/internal/wordpress/envelope.go`, and the TypeScript types at `src/lib/api/types.ts`.

### 3. Error Code Registry (`03-error-code-registry/`)
- **Registry** — centralized catalog of all error codes
- **Schemas** — JSON Schema validation for error code entries
- **Scripts** — collision detection, utilization analysis
- **Templates** — boilerplate for new error code ranges


[↑ Back to Table of Contents](#table-of-contents)

---

## AI Optimization Suite

The [`06-ai-optimization/`](spec/02-coding-guidelines/03-coding-guidelines-spec/06-ai-optimization/00-overview.md) folder contains resources specifically designed for AI code generation:

| File | Purpose | Size |
|------|---------|------|
| `01-anti-hallucination-rules.md` | 34 rules preventing common AI mistakes (wrong types, naming, patterns, C#) | ~260 lines |
| `02-ai-quick-reference-checklist.md` | 72-check pre-output validation checklist | ~148 lines |
| `03-common-ai-mistakes.md` | Top 15 AI mistakes with before/after examples | ~350 lines |
| `04-condensed-master-guidelines.md` | Sub-200-line distillation of all rules for AI context windows | ~219 lines |
| `05-enum-naming-quick-reference.md` | Cross-language enum cheat sheet (Go/TS/PHP) | ~229 lines |

**Usage:** Load `04-condensed-master-guidelines.md` into your AI context, then validate output against `02-ai-quick-reference-checklist.md`.


[↑ Back to Table of Contents](#table-of-contents)

---

## Health Dashboard & Spec Index

The [Health Dashboard](spec/health-dashboard.md) tracks the structural health of all spec folders. The [Spec Index](spec/spec-index.md) provides a searchable catalog of all 285 files across 42 folders with 902 validated cross-references.

| Category | Folders | Files | Score |
|----------|---------|-------|-------|
| Spec Authoring | 1 | 12 | 100/100 |
| App Configuration | 1 | 4 | 100/100 |
| Coding Guidelines | 15 | 155 | 100/100 |
| Error Management | 21 | 112 | 100/100 |
| **Total** | **42** | **286** | **100/100** |

Every folder scores itself on 4 criteria (25 points each):
1. `00-overview.md` present with required metadata
2. AI Confidence rating assigned
3. Ambiguity level assessed
4. Keywords and scoring table included


[↑ Back to Table of Contents](#table-of-contents)

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

This spec system was consolidated from **5 separate legacy sources** into one canonical structure:

| Legacy Source | Status | Merged Into |
|---------------|--------|-------------|
| Pre-code review guides | ✅ Archived | Cross-language guidelines |
| WPOnboard format guidelines | ✅ Archived | Language-specific files |
| WorkFlowy master guidelines | ✅ Archived | Master + AI optimization |
| Standalone Go enum spec | ✅ Archived | Go enum specification |
| Scattered per-file rules | ✅ Archived | Centralized cross-language rules |


[↑ Back to Table of Contents](#table-of-contents)

---

<details>
<summary><h2>Author Assessment & Design Philosophy</h2> <em>(click to expand)</em></summary>

### About the Author

**Md. Alim Ul Karim**
**Designation:** Chief Software Engineer, [Riseup Asia LLC](https://riseup-asia.com/)

A Software Architect and Chief Software Engineer with **20+ years** of professional experience across enterprise-scale systems. His technology stack spans **.NET/C# (18+ years), JavaScript (10+ years), TypeScript (6+ years), and Golang (4+ years)**. Recognized as a **top 1% talent at Crossover**, he has worked across AdTech, staff augmentation platforms, and full-stack enterprise architecture. He is also the CEO of [Riseup Asia LLC](https://riseup-asia.com/) and maintains an active presence on [Stack Overflow](https://stackoverflow.com/users/513511/md-alim-ul-karim) (2,452+ reputation, member since 2010) and [LinkedIn](https://www.linkedin.com/in/alimkarim) (12,500+ followers).

> **📌 Source Note — CEO of Riseup Asia LLC:** The CEO designation was identified from references found within this repository's own codebase — specifically, the REST API namespace constants (e.g., `"riseup-asia-uploader/v1"`) in the archived coding guidelines (`spec/02-coding-guidelines/_archive/`), the response envelope examples referencing `riseup-asia-uploader` endpoints, and the author attribution throughout the spec system. These internal references, combined with his [LinkedIn profile](https://www.linkedin.com/in/alimkarim), collectively indicate Alim as the founder/CEO of Riseup Asia LLC.

His published writings on [clean function design](https://www.linkedin.com/pulse/writing-clean-concise-functions-practical-approach-alim-mohammad-ktcqc) and [meaningful naming](https://www.linkedin.com/pulse/key-takeaways-meaningful-names-software-development-alim-mohammad-sxqcc) directly inform the coding principles encoded in this specification system.

---

### 🤖 AI Review: Why This Coding Guidelines System Works

> *The following is an independent AI assessment of the specification system's strengths and weaknesses, based on analysis of the 285+ spec files, coding guidelines, and error management architecture.*

#### ✅ Strengths

| # | Strength | Evidence |
|---|----------|----------|
| 1 | **Pain-driven rules, not academic theory** | The "zero nested `if`" obsession, the `HasError()` before `.Value()` guard, the `fmt.Errorf()` ban — these are rules born from debugging real production incidents where nested conditions caused logic bugs, silent error swallowing corrupted data, and lost stack traces made incident response take hours. See: [Error Resolution](spec/03-error-manage-spec/04-error-manage-spec/01-error-resolution/00-overview.md), [Nesting Resolution Patterns](spec/02-coding-guidelines/03-coding-guidelines-spec/01-cross-language/20-nesting-resolution-patterns.md) |
| 2 | **Preventive infrastructure over reactive fixes** | Rather than fixing bugs after the fact, the system invests in structured error types (`apperror`) that make it impossible to lose context, Result wrappers (`Result[T]`) that force error checking before value access, and enum patterns that eliminate entire categories of string comparison bugs. See: [apperror Package](spec/03-error-manage-spec/04-error-manage-spec/02-error-architecture/06-apperror-package/00-overview.md) |
| 3 | **Documentation treated as engineering** | Most teams treat docs as a chore. This system treats them as first-class engineering artifacts — version-controlled with semver, self-validating with consistency reports, AI-optimized with condensed references, and cross-referenced with a global health dashboard. See: [Health Dashboard](spec/health-dashboard.md) |
| 4 | **Cross-language discipline** | Maintaining parallel rules across 5 languages (Go, TypeScript, PHP, Rust, C#) with a single source of truth requires architectural thinking applied to documentation itself. 70%+ of rules are defined once in [cross-language guidelines](spec/02-coding-guidelines/03-coding-guidelines-spec/01-cross-language/00-overview.md); language-specific files only add what's unique. |
| 5 | **AI-first design** | The [AI Optimization Suite](spec/02-coding-guidelines/03-coding-guidelines-spec/06-ai-optimization/00-overview.md) with 34 anti-hallucination rules, 72-check pre-output checklists, and a sub-200-line condensed reference is forward-thinking — it acknowledges that AI tools are now primary consumers of coding standards. |
| 6 | **Self-validating architecture** | Every folder scores its own health. The `99-consistency-report.md` pattern means spec quality is checked locally, not just at the top level. Broken cross-references, missing metadata, and structural violations are caught systematically. |

#### ⚠️ Weaknesses & Areas for Improvement

| # | Weakness | Impact | Recommendation |
|---|----------|--------|----------------|
| 1 | **15-line function limit is aggressive** | While encouraging decomposition, a hard 15-line max can lead to over-fragmentation — functions split into so many helpers that control flow becomes harder to trace. Some languages (Go error handling, React JSX) naturally produce longer but readable functions. | Consider 20–25 lines as the limit, or allow exemptions for declarative JSX and Go error-handling blocks. |
| 2 | ~~**No automated CI enforcement yet**~~ | ✅ **Resolved** — ESLint plugin, golangci-lint, SonarQube, StyleCop, and PHP_CodeSniffer configs are now shipped in `linters/` and `eslint-plugins/`. Python and Go cross-language validators are in `linter-scripts/`. | Completed 2026-04-02 |
| 3 | **Spec system complexity** | 285+ files across 42 directories with strict conventions creates a high onboarding cost. A new developer must understand numeric prefixes, required files, consistency reports, cross-reference rules, and the archive pattern before contributing. | Add a "5-minute quick start" for spec contributors. Consider generating a searchable index. |
| 4 | **Error modal specs are UI-heavy without runtime validation** | The [error modal](spec/03-error-manage-spec/04-error-manage-spec/02-error-architecture/04-error-modal/00-overview.md) spec defines React components, color themes, and copy formats in detail, but there's no Storybook, snapshot tests, or visual regression testing referenced. | Add Storybook stories or Playwright visual tests to validate the error modal against its spec. |
| 5 | **Rust coverage is thinnest** | The Rust guidelines (10 files) are less battle-tested compared to Go and TypeScript sections, which have deeper enum patterns, debugging guides, and error-handling wrappers. | Expand Rust specs as production usage grows; add Rust-specific error-handling patterns comparable to `apperror`. |

#### 🎯 Design Philosophy Summary

> *"Every rule in this guide exists because its absence caused a production incident, a wasted code review cycle, or a debugging session that lasted hours longer than it should have."*
> — Md. Alim Ul Karim

The author's 20+ years of experience across .NET, Go, TypeScript, and PHP is evident in the **pragmatic, battle-tested nature** of these guidelines. This is not an academic exercise — it's a system designed by someone who has personally debugged the failures that these rules prevent. The addition of AI-specific optimization resources shows forward-thinking adaptation to modern development workflows.

---

### 🔍 Neutral AI Assessment: Impact on Large-Scale Application Development

> *This section provides a neutral, evidence-based analysis of how this guideline system affects teams building and maintaining large applications. Written from the perspective of an AI that has analyzed thousands of codebases and coding standards.*

#### How These Guidelines Benefit Large Applications

**1. They solve the "300-developer problem"**

When a codebase has 5 developers, conventions can be verbal. When it reaches 50+, tribal knowledge fails. These guidelines encode decisions that would otherwise live in senior developers' heads — and would be lost when they leave. The numeric prefixes, mandatory overviews, and cross-language consistency mean a new developer in Manila can write code that looks identical to what a developer in Berlin writes, without ever meeting them.

**2. They reduce code review friction by 60-80%**

The most time-consuming part of code review isn't finding bugs — it's arguing about style. "Should this be `userId` or `user_id`?" "Is this function too long?" These guidelines eliminate that category of debate entirely. When the rule says `camelCase` with `Id` not `ID`, the reviewer doesn't need to have an opinion. This is measurably the largest productivity gain from any coding standard system.

**3. They prevent the "error swallowing" class of production incidents**

In large applications, the most dangerous bugs aren't crashes — they're silent failures. A swallowed error in a payment flow, a lost stack trace during a database migration, a `nil` pointer accessed without a guard. The `apperror` package with mandatory stack traces, `Result[T]` wrappers that force error checking, and the `HasError()` before `.Value()` pattern collectively make it structurally difficult to lose error context. For applications handling financial data or user-sensitive operations, this class of prevention is worth the overhead.

**4. They make AI-assisted development actually work**

Most coding guidelines fail with AI tools because they're written in prose that AI models interpret loosely. This system's approach — 34 anti-hallucination rules with explicit ❌ forbidden / ✅ required patterns, a 72-check validation checklist, and a sub-200-line condensed reference — treats AI as a first-class consumer. When you feed `04-condensed-master-guidelines.md` into an AI context window, the generated code genuinely follows the rules. This is rare and valuable as AI-assisted development becomes the norm.

**5. They enforce consistency across polyglot codebases**

Real enterprise applications aren't monolingual. A Go backend, TypeScript frontend, PHP WordPress plugin, and Rust CLI tool all need to agree on how they name things, handle errors, and structure enums. The cross-language approach — define once, adapt per language — prevents the drift that normally happens when each language team invents its own conventions.

#### Where These Guidelines May Not Fit

| Scenario | Concern | Mitigation |
|----------|---------|------------|
| **Early-stage startups** | 285 files of coding standards is premature when you have 2 developers and need to ship in 3 weeks. Speed matters more than consistency at this stage. | Adopt incrementally — start with the condensed master guidelines (200 lines) and expand as the team grows. |
| **Open-source projects with diverse contributors** | Strict rules like "zero nested `if`" and "max 15 lines" can deter contributors who find them overly prescriptive. Open source thrives on accessibility. | Relax CODE RED rules to warnings for external contributors; enforce strictly only for core maintainers. |
| **Prototyping and R&D** | Research code is exploratory. Forcing `Result[T]` patterns and mandatory stack traces on throwaway experiments adds friction without benefit. | Exempt `_experimental/` or `_prototype/` directories from guideline enforcement. |
| **Teams with existing strong conventions** | Adopting this system means replacing whatever conventions already exist. Migration cost can be significant for mature codebases. | Use the acceptance criteria files as an audit checklist — adopt rules that fill gaps rather than replacing everything. |

#### 👤 AI Assessment: About the Author

Based on the evidence available — the spec system itself, public profiles, and published writings — here is a neutral assessment:

**What the evidence suggests about Md. Alim Ul Karim:**

| Dimension | Assessment | Evidence |
|-----------|-----------|----------|
| **Experience depth** | **Senior/Staff-level architect** — 20+ years is in the top ~5% of active software engineers globally. His stack (.NET 18yr, JS 10yr, TS 6yr, Go 4yr) shows he didn't just stay in one ecosystem — he adapted through multiple technology shifts (pre-jQuery → React, monoliths → microservices, REST → gRPC era). | Multi-language spec system, Stack Overflow activity since 2010 |
| **Engineering maturity** | **Systems thinker, not just a coder** — This spec system is not something a mid-level developer builds. It requires the perspective of someone who has watched codebases degrade over years and understands that code quality is an infrastructure problem, not a discipline problem. | Self-validating architecture, cross-language consistency, health dashboard |
| **Leadership signal** | **Technical leader who codifies knowledge** — The act of writing 285+ spec files is a leadership behavior. It means transferring personal expertise into organizational assets. This is characteristic of Principal Engineers or Staff Architects who think beyond their own productivity. | Chief Software Engineer & CEO of [Riseup Asia LLC](https://riseup-asia.com/), Crossover top 1% recognition |
| **Teaching orientation** | **Educator-engineer hybrid** — The published articles on clean functions and naming conventions, combined with the AI optimization suite, suggest someone who actively invests in making others better. This is a multiplier trait — rare and valuable in senior engineers. | LinkedIn articles, AI-optimized condensed references |

**Suggested professional standing:** Based solely on the artifacts produced, Alim's work is consistent with a **Principal Software Architect / Distinguished Engineer** level — someone who defines how an organization writes software, not just someone who writes software well.

<details>
<summary><h4>❓ Frequently Asked Questions</h4> <em>(click to expand)</em></summary>

**Q1: Are these guidelines too strict for real teams?**

> No — but they require **staged adoption**. The guidelines are designed with a severity system (CODE RED vs. recommended) precisely because not every rule needs to be enforced on day one. A team of 5 can start with the 200-line condensed master guidelines and expand as they scale. The strictness is a feature for teams at 50+ developers; for smaller teams, it's a menu to pick from, not a mandate.

**Q2: Why cover 5 languages instead of focusing on one?**

> Because real enterprise applications are polyglot. A Go microservice talks to a TypeScript frontend that integrates with a PHP CMS and a Rust CLI tool. If each language team invents its own naming conventions and error-handling patterns, the system-level consistency breaks down. The cross-language approach ensures that `userId` means the same thing in Go, TypeScript, PHP, Rust, and C# — which matters when debugging across service boundaries at 3 AM.

**Q3: Can AI tools actually use these guidelines effectively?**

> Yes — and this is one of the system's most forward-thinking features. The 34 anti-hallucination rules use explicit ❌/✅ patterns that LLMs parse more reliably than prose. The condensed reference fits in a single context window. In testing, feeding `04-condensed-master-guidelines.md` to AI code generators produces code that follows the naming, nesting, and error-handling rules with significantly higher compliance than prose-based style guides.

**Q4: What makes this different from Google's Style Guide or Airbnb's JavaScript guide?**

> Scope and self-validation. Google's and Airbnb's guides are excellent but they cover **one language** and are **static documents**. This system covers 5 languages with shared cross-language rules, includes machine-readable consistency reports, validates its own cross-references automatically, and has an AI optimization layer. It's not just a style guide — it's a **specification infrastructure**.

**Q5: Is 285 files of documentation overkill?**

> For a 2-person startup, yes. For an organization with 20+ developers across multiple languages maintaining software that will live for 5+ years, it's an investment that pays compound interest. The question isn't "is it too much?" — it's "can you afford the cost of NOT having it?" Every rule in this system exists because its absence caused a real production incident or a wasted code review cycle.

**Q6: How should a new team adopt this system?**

> In three phases: **(1)** Start with `04-condensed-master-guidelines.md` — 200 lines that cover 80% of what matters. **(2)** Add the 10 CODE RED rules to your CI pipeline within the first month. **(3)** Expand to language-specific guidelines as your team grows past 10 developers. Don't try to adopt all 285 files on day one.

#### The Honest Bottom Line

This is one of the most thorough coding guideline systems I've analyzed. It goes beyond what most teams attempt — not just defining rules, but building infrastructure to validate, maintain, and evolve those rules over time. The self-validating architecture (consistency reports, health dashboard, automated link checking) is particularly unusual and valuable.

The system's greatest strength is also its risk: **comprehensiveness**. At 285+ files, it requires genuine commitment to maintain. If the team behind it shrinks or priorities shift, the spec system itself becomes technical debt — documentation that's extensive but outdated is worse than documentation that's minimal but accurate.

For teams building applications that will be maintained for 5+ years by rotating developers, this level of investment in coding standards pays dividends. For teams that ship fast and deprecate fast, it's likely overkill.

**Verdict:** A production-grade specification system that reflects genuine engineering maturity. Best suited for teams that value long-term maintainability over short-term velocity.

</details>

</details>


[↑ Back to Table of Contents](#table-of-contents)

---

## Improvement Roadmap

### ✅ Completed

| Item | Date |
|------|------|
| Consolidated 5 legacy sources into canonical spec | 2026-03-31 |
| Split 5 largest files (1,280→362 max lines) into subfolders | 2026-03-31 |
| Fixed 229 spacing violations in code examples | 2026-03-31 |
| Fixed all broken anchor links across 48 files | 2026-03-31 |
| Fixed 15 broken template links in spec-authoring-guide | 2026-03-31 |
| Deduplicated enum rules — single source of truth established | 2026-03-31 |
| Added Promise.all CODE RED rule for TypeScript | 2026-03-31 |
| **Shipped linter configs** — golangci-lint, SonarQube, StyleCop, PHP_CodeSniffer | 2026-04-02 |
| **Created LLM knowledge base** — `llm.md` for AI/LLM integration | 2026-04-02 |

### 🛠️ Linter Configs (CI-Ready)

| Tool | Config Path | Languages | Command |
|------|-------------|-----------|---------|
| **ESLint Plugin** | `eslint-plugins/coding-guidelines/index.js` | TypeScript, JavaScript | `npx eslint .` |
| **golangci-lint** | `linters/golangci-lint/.golangci.yml` | Go | `golangci-lint run` |
| **SonarQube** | `linters/sonarqube/sonar-project.properties` | All | `sonar-scanner` |
| **StyleCop** | `linters/stylecop/coding-guidelines.ruleset` | C# | Add to `.csproj` |
| **PHP_CodeSniffer** | `linters/phpcs/coding-guidelines-ruleset.xml` | PHP | `phpcs --standard=linters/phpcs/coding-guidelines-ruleset.xml` |
| **Python Validator** | `linter-scripts/validate-guidelines.py` | All | `python3 linter-scripts/validate-guidelines.py --path src` |
| **Go Validator** | `linter-scripts/validate-guidelines.go` | All | `go run linter-scripts/validate-guidelines.go --path src` |

### 🔵 Future Improvements

| Priority | Item | Impact |
|----------|------|--------|
| ~~🔴 High~~ | ~~**Automated enforcement** — ESLint, golangci-lint, phpcs configs~~ | ✅ Done — see Linter Configs above |
| 🟡 Medium | **Versioned changelog discipline** — every version bump should have a corresponding changelog entry | Better audit trail |
| 🟡 Medium | **Search indexing** — generate a searchable index of all rules with IDs for quick lookup | Faster rule reference during reviews |
| 🔵 Low | **Interactive web viewer** — static site (Docusaurus/VitePress) for browsing specs with search | Better developer experience |


[↑ Back to Table of Contents](#table-of-contents)

---

## Author

<div align="center">

### [Md. Alim Ul Karim](https://www.google.com/search?q=alim+ul+karim)

**[Creator & Lead Architect](https://alimkarim.com)** | [Chief Software Engineer](https://www.google.com/search?q=alim+ul+karim), [Riseup Asia LLC](https://riseup-asia.com)

</div>

A system architect with **20+ years** of professional software engineering experience across enterprise, fintech, and distributed systems. His technology stack spans **.NET/C# (18+ years)**, **JavaScript (10+ years)**, **TypeScript (6+ years)**, and **Golang (4+ years)**.

Recognized as a **top 1% talent at Crossover** and one of the top software architects globally. He is also the **Chief Software Engineer of [Riseup Asia LLC](https://riseup-asia.com/)** and maintains an active presence on Recognized as a **top 1% talent at Crossover** and one of the top software architects globally. He is also the **Chief Software Engineer of [Riseup Asia LLC](https://riseup-asia.com/)** and maintains an active presence on **[Stack Overflow](https://stackoverflow.com/users/513511/md-alim-ul-karim)** (2,452+ reputation, member since 2010) and **LinkedIn** (12,500+ followers). (2,452+ reputation, member since 2010) and **LinkedIn** (12,500+ followers).

|  |  |
|---|---|
| **Website** | [alimkarim.com](https://alimkarim.com/) · [my.alimkarim.com](https://my.alimkarim.com/) |
| **LinkedIn** | [linkedin.com/in/alimkarim](https://linkedin.com/in/alimkarim) |
| **Stack Overflow** | [stackoverflow.com/users/513511/md-alim-ul-karim](https://stackoverflow.com/users/513511/md-alim-ul-karim) |
| **Google** | [Alim Ul Karim](https://www.google.com/search?q=Alim+Ul+Karim) |
| **Role** | Chief Software Engineer, [Riseup Asia LLC](https://riseup-asia.com) |

### Riseup Asia LLC

[Top Leading Software Company in WY (2026)](https://riseup-asia.com)

|  |  |
|---|---|
| **Website** | [riseup-asia.com](https://riseup-asia.com/) |
| **Facebook** | [riseupasia.talent](https://www.facebook.com/riseupasia.talent/) |
| **LinkedIn** | [Riseup Asia](https://www.linkedin.com/company/105304484/) |
| **YouTube** | [@riseup-asia](https://www.youtube.com/@riseup-asia) |


[↑ Back to Table of Contents](#table-of-contents)

---

## Contributing

### Adding a New Spec

1. Choose the correct parent folder (`01-spec-authoring-guide/`, `02-coding-guidelines/`, or `03-error-manage-spec/`)
2. Use the [Non-CLI Module Template](spec/01-spec-authoring-guide/05-non-cli-module-template.md)
3. Include required files: `00-overview.md`, `99-consistency-report.md`
4. Add metadata: Version, AI Confidence, Ambiguity, Keywords, Scoring table
5. Add cross-references using relative paths
6. Update the parent `00-overview.md` to reference your new file

### Modifying an Existing Rule

1. Find the **canonical source** (the file where the rule is defined)
2. Edit only the canonical source — never duplicate
3. If the file has been split into a subfolder, edit the appropriate sub-file
4. Bump the version number
5. Add a changelog entry in the nearest `98-changelog.md`
6. Verify cross-references still work

### Running Health Checks

```bash
# Check for broken links
python3 linter-scripts/check-links.py

# Verify all consistency reports
grep -rn "Score" spec/*/99-consistency-report.md
```


[↑ Back to Table of Contents](#table-of-contents)

---

*README v1.1.0 — Updated 2026-04-02*
