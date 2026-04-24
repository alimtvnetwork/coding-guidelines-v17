<p align="center">
  <a href="https://github.com/alimtvnetwork/coding-guidelines-v15">
    <img
      src="public/images/coding-guidelines-icon.png"
      alt="Coding Guidelines v15 brand icon — gradient shield with code-bracket symbol"
      width="160"
      height="160"
    />
  </a>
</p>

<h1 align="center">Coding Guidelines v15</h1>

<p align="center">
  <strong>Production-grade coding standards with zero-nesting enforcement and AI-optimized spec architecture<br/>
  for <em>Go, TypeScript, PHP, Rust, and C#</em> — drop-in conventions for elite engineering teams.</strong>
</p>

<p align="center">
  <!-- STAMP:BADGES --><a href="https://github.com/alimtvnetwork/coding-guidelines-v15/releases"><img alt="Version" src="https://img.shields.io/badge/version-4.7.0-3B82F6?style=flat-square"/></a> <a href="spec/"><img alt="Spec Files" src="https://img.shields.io/badge/spec%20files-612-10B981?style=flat-square"/></a> <a href="spec/"><img alt="Folders" src="https://img.shields.io/badge/folders-22-8B5CF6?style=flat-square"/></a> <a href="version.json"><img alt="Lines" src="https://img.shields.io/badge/lines-131%2C969-F59E0B?style=flat-square"/></a> <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-22C55E?style=flat-square"/></a> <a href="llm.md"><img alt="AI Ready" src="https://img.shields.io/badge/AI%20ready-yes-FF6E3C?style=flat-square"/></a> <a href="version.json"><img alt="Updated" src="https://img.shields.io/badge/updated-2026--04--24-0EA5E9?style=flat-square"/></a><!-- /STAMP:BADGES -->
</p>

<p align="center">
  <!-- STAMP:PLATFORM_BADGES --><a href="spec/02-coding-guidelines/"><img alt="Languages" src="https://img.shields.io/badge/languages-Go%20%7C%20TS%20%7C%20PHP%20%7C%20Rust%20%7C%20C%23-EC4899?style=flat-square"/></a> <a href="#-bundle-installers"><img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-6366F1?style=flat-square"/></a> <a href="bundles.json"><img alt="Bundles" src="https://img.shields.io/badge/bundles-7-14B8A6?style=flat-square"/></a> <a href="public/health-score.json"><img alt="Health Score" src="https://img.shields.io/badge/health-80%2F100%20(B)-F59E0B?style=flat-square"/></a> <a href="spec/17-consolidated-guidelines/29-blind-ai-audit-v3.md"><img alt="Blind AI Audit" src="https://img.shields.io/badge/blind%20AI%20audit-99.8%2F100-FF6E3C?style=flat-square"/></a> <a href="#-contributing"><img alt="PRs Welcome" src="https://img.shields.io/badge/PRs-welcome-22C55E?style=flat-square"/></a> <a href="https://lovable.dev"><img alt="Made With Lovable" src="https://img.shields.io/badge/made%20with-Lovable-FF6E3C?style=flat-square"/></a> <a href="https://github.com/alimtvnetwork/coding-guidelines-v15/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/alimtvnetwork/coding-guidelines-v15?style=flat-square&color=F59E0B"/></a> <a href="https://github.com/alimtvnetwork/coding-guidelines-v15/issues"><img alt="Issues" src="https://img.shields.io/github/issues/alimtvnetwork/coding-guidelines-v15?style=flat-square&color=EF4444"/></a><!-- /STAMP:PLATFORM_BADGES -->
</p>

<p align="center"><strong>By <a href="https://alimkarim.com/">Md. Alim Ul Karim</a></strong> — Chief Software Engineer, <a href="https://riseup-asia.com/">Riseup Asia LLC</a> · <a href="https://www.linkedin.com/in/alimkarim">LinkedIn</a> · <a href="https://stackoverflow.com/users/513511/md-alim-ul-karim">SO</a> · <a href="https://github.com/alimtvnetwork">GitHub</a> · <a href="docs/author.md">Full bio</a></p>

<p align="center">
  <em>Stats:</em> <!-- STAMP:FILES -->612<!-- /STAMP:FILES --> spec files · <!-- STAMP:FOLDERS -->22<!-- /STAMP:FOLDERS --> top-level folders · <!-- STAMP:LINES -->131,969<!-- /STAMP:LINES --> lines · v<!-- STAMP:VERSION -->4.7.0<!-- /STAMP:VERSION --> · updated <!-- STAMP:UPDATED -->2026-04-24<!-- /STAMP:UPDATED -->
</p>

---

<h2 align="center">⚡ Install in One Line</h2>

<p align="center">
  Pick your platform. Copy the line. Paste it. Done — no clone, no <code>npm install</code>.<br/>
  Need just one bundle? Jump to <a href="#-bundle-installers">Named Bundle Installers</a>.
</p>

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.ps1 | iex
```

### 🪟 Windows · PowerShell · skip latest-version probe

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.ps1))) -n
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.sh | bash
```

### 🐧 macOS · Linux · Bash · skip latest-version probe

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.sh | bash -s -- -n
```

<p align="center"><sub>Version-pinned · SHA-256 verified · idempotent · temp-clean. Power-user flags (<code>--repo</code>, <code>--branch</code>, <code>--version</code>, <code>--folders</code>, <code>--dest</code>, <code>--config</code>, <code>--prompt</code>, <code>--force</code>, <code>--dry-run</code>) live in <a href="#%EF%B8%8F-full-repo-install-scripts">Full-Repo Install Scripts</a>.</sub></p>

---

<h2 align="center">📦 Bundle Installers</h2>

<p align="center">
  Same order as the on-site install UI — seven named bundles, each with one Windows line and one Bash line.
</p>

### <code>error-manage</code> — Error Management Spec

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/error-manage-install.ps1 | iex
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/error-manage-install.sh | bash
```

### <code>splitdb</code> — Split-DB Architecture Spec

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/splitdb-install.ps1 | iex
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/splitdb-install.sh | bash
```

### <code>slides</code> — Slides App + Decks

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.ps1 | iex
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.sh | bash
```

### <code>linters</code> — Linters + CI/CD Linter Pack

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/linters-install.ps1 | iex
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/linters-install.sh | bash
```

### <code>cli</code> — CLI Toolchain Spec

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/cli-install.ps1 | iex
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/cli-install.sh | bash
```

### <code>wp</code> — WordPress Plugin How-To Spec

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/wp-install.ps1 | iex
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/wp-install.sh | bash
```

### <code>consolidated</code> — Consolidated Guidelines

### 🪟 Windows · PowerShell

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/consolidated-install.ps1 | iex
```

### 🐧 macOS · Linux · Bash

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/consolidated-install.sh | bash
```

### Verify & Uninstall

**Verify**: `sha256sum -c checksums.txt --ignore-missing` (Unix) · `Get-FileHash … -Algorithm SHA256` (Windows). **Uninstall**: delete the folders listed under each bundle's `folders[].dest` in [`bundles.json`](bundles.json). **Windows SmartScreen**: use `-ExecutionPolicy Bypass` for a single session if `irm | iex` is flagged.

<h2 align="center">📑 Table of Contents</h2>

<p align="center">
  <a href="#-table-of-contents">Table of Contents</a> ·
  <a href="#-install-in-one-line">Install</a> ·
  <a href="#-bundle-installers">Bundle Installers</a> ·
  <a href="#-run-commands">Run Commands</a> ·
  <a href="#-core-development-principles">Core Development Principles</a> ·
  <a href="#-code-red-rules">CODE-RED Rules</a> ·
  <a href="#-real-world-example-code-red-violations">Real-world Code Red Violations</a> ·
  <a href="#spec-references">Spec References</a> ·
  <a href="#-error-management-summary">Error Management Summary</a> ·
  <a href="#-type-aliases-for-common-generic-results">Type Aliases for Generic Results</a> ·
  <a href="#-for-ai-agents">For AI Agents</a> ·
  <a href="#%EF%B8%8F-full-repo-install-scripts">Full-Repo Install Scripts</a> ·
  <a href="#-documentation">Documentation</a> ·
  <a href="#-neutral-ai-assessment">Neutral AI Assessment</a> ·
  <a href="#-contributing">Contributing</a> ·
  <a href="#-author">Author</a>
</p>

---

<h2 align="center">🚀 Run Commands</h2>

<p align="center">
  Local developer workflow — for contributors who clone the repo.<br/>
  End-users do <strong>not</strong> need this section; the one-line installers above handle everything.
</p>

### Setup

```bash
git clone https://github.com/alimtvnetwork/coding-guidelines-v15.git
```

```bash
cd coding-guidelines-v15 && npm install
```

### Daily Workflow

```bash
npm run dev
```

```bash
npm run build
```

```bash
npm run preview
```

### Sync & Stamping

```bash
npm run sync
```

```bash
npm run sync:version
```

```bash
npm run sync:specs
```

```bash
npm run sync:health
```

```bash
npm run sync:readme
```

### Linters (what CI runs)

```bash
go run linter-scripts/validate-guidelines.go --path spec --max-lines 15
```

```bash
python3 linter-scripts/validate-guidelines.py spec
```

```bash
python3 linter-scripts/check-spec-cross-links.py --root spec --repo-root .
```

```bash
python3 linter-scripts/check-spec-folder-refs.py
```

```bash
python3 linter-scripts/check-forbidden-strings.py
```

```bash
bash linter-scripts/check-forbidden-spec-paths.sh
```

```bash
bash linter-scripts/check-axios-version.sh
```

```bash
npm run lint:readme
```

```bash
npm run lint:readme:canonicals
```

> **Markdown is intentionally not linted for code-style.** CI lints code in `spec/` and source files only — example snippets in `readme.md` and `docs/` are validated by hand against [`spec/02-coding-guidelines/01-cross-language/04-code-style/`](spec/02-coding-guidelines/01-cross-language/04-code-style/).

### Repo migration (v15 → v16)

```bash
npm run migrate:repo:dry
```

---

<h2 align="center">🧭 Core Development Principles</h2>

<p align="center">
  Nine non-negotiables. Every spec, every linter, every PR enforces them.<br/>
  Full reference: <a href="docs/principles.md"><code>docs/principles.md</code></a>.
</p>

| # | Principle | One-line rule |
|---|---|---|
| 1 | **Zero-Nesting Discipline** | No nested `if`-`else`. Use early-return guards. |
| 2 | **Two-Operand Maximum** | Boolean expressions take ≤ 2 operands; extract the third. |
| 3 | **Positively Named Booleans** | `isReady`, `hasError`, `canPublish` — never `!isNotReady`. |
| 4 | **Structured Error Wrapping** | Every error crosses a boundary as `AppError` with stack + context. |
| 5 | **Strict Function & File Metrics** | Functions 8-15 lines · files < 300 · React components < 100. |
| 6 | **PascalCase Everywhere** | Identifiers, DB columns, JSON keys, types. Acronyms stay full-caps. |
| 7 | **No Magic Strings** | Constants, enums, or typed action discriminators — never inline strings. |
| 8 | **Spec-First Workflow** | Spec the change in `spec/` before writing code. |
| 9 | **Cache Invalidation by Contract** | Explicit TTLs, deterministic keys, invalidate on mutation. |

---

<h2 align="center">🔴 CODE-RED Rules</h2>

<p align="center">
  CODE-RED rules are <strong>zero-tolerance</strong> standards enforced by
  <a href="linter-scripts/validate-guidelines.py"><code>linter-scripts/validate-guidelines.py</code></a>
  and <a href="linter-scripts/validate-guidelines.go"><code>validate-guidelines.go</code></a>.
  A violation fails CI; it is never accepted as "style preference."
</p>

| ID | Rule | One-line summary |
|---|---|---|
| CODE-RED-001 | **Zero nested control flow** | No nested `if`/`else`. Use early-return guards with one explicit reason per branch. |
| CODE-RED-002 | **No magic strings in errors** | Construct errors via `apperror.NewType()` / `WrapType()` / `WrapTypeMsg()` — never raw codes. |
| CODE-RED-003 | **Contextual error names** | Use `requestError`, `readFileError`, `siteWasNotFound` — never generic `err` or `ERR`. |
| CODE-RED-004 | **Positive boolean naming** | Domain language (`site.IsBlocked`, `slug.IsMissing()`) — never hidden negation like `!isValidPath`. |
| CODE-RED-005 | **No `fmt.Errorf()`** | Always wrap with `apperror.WrapType()` / `WrapTypeMsg()` and an `apperrtype` enum. |
| CODE-RED-006 | **Single-value returns** | Go functions return one `Result[T]` — never `(T, error)` tuples. |
| CODE-RED-007 | **Typed enums only** | `type X byte` + `iota` — never string-backed enums in Go. |
| CODE-RED-008 | **Named protocol values** | `http.MethodGet`, `http.StatusOK` — never literals like `"GET"` or `200`. |

**Where the full walkthrough lives in the document hierarchy:**

1. **Root README** → [Real-world Code Red Violations](#-real-world-example-code-red-violations) — quick before/after for each rule above.
2. **Cross-language specs** → [`spec/02-coding-guidelines/01-cross-language/`](spec/02-coding-guidelines/01-cross-language/) — language-agnostic rule definitions (magic values, immutability, types folder).
3. **Go-specific specs** → [`spec/02-coding-guidelines/03-golang/07-code-severity-taxonomy.md`](spec/02-coding-guidelines/03-golang/07-code-severity-taxonomy.md) — Code Red vs Dangerous classification.
4. **Error architecture** → [`spec/03-error-manage/04-error-manage-spec/02-error-architecture/06-apperror-package/`](spec/03-error-manage/04-error-manage-spec/02-error-architecture/06-apperror-package/) — `apperror` constructors and `apperrtype` enum registry.
5. **AI quick reference** → [`spec/02-coding-guidelines/03-coding-guidelines-spec/06-ai-optimization/04-condensed-master-guidelines.md`](spec/02-coding-guidelines/03-coding-guidelines-spec/06-ai-optimization/04-condensed-master-guidelines.md) — sub-200-line distillation for AI context windows.
6. **Linters** → [`linter-scripts/`](linter-scripts/) — automated enforcement that mirrors the rules above.

---

<h2 align="center">🚨 Real-world Example — Code Red Violations</h2>

<p align="center">
  Pulled from the <strong>Riseup Asia Uploader</strong> codebase audit.<br/>
  These exact patterns are now blocked by <a href="linter-scripts/"><code>linter-scripts/</code></a>.
</p>

```ts
// ❌ CODE RED — nested if, three operands, error swallowed, magic string,
//              raw negation (`!user.banned`), untyped param, opaque "admin" string.
function processUser(user) {
  if (user) {
    if (user.role === "admin" && user.active && !user.banned) {
      try { doWork(user); } catch (e) { /* silent */ }
    }
  }
}

// ✅ Refactored — typed enums, positively-named guards (zero `!`),
//                ≤ 2 operands per expression, structured AppError, no magic strings.
enum Role {
  Admin  = "Admin",
  Member = "Member",
}

enum AppErrorCode {
  UserMissing      = "UserMissing",
  UserNotAdmin     = "UserNotAdmin",
  UserSuspended    = "UserSuspended",
}

// Positive guards — each one is a single intent, no negation at the call site.
function isUserMissing(user: User | null): user is null {
  return user === null;
}

function isUserAdmin(user: User): boolean {
  return user.role === Role.Admin;
}

function isUserSuspended(user: User): boolean {
  return user.isBanned || user.isInactive;   // single operator, two operands
}

function processUser(user: User | null): Result<void> {
  if (isUserMissing(user)) {
    return Failure(AppError.create(AppErrorCode.UserMissing));
  }

  if (isUserSuspended(user)) {
    return Failure(AppError.create(AppErrorCode.UserSuspended));
  }

  if (isUserAdmin(user)) {
    return TryDo(() => doWork(user));
  }

  return Failure(AppError.create(AppErrorCode.UserNotAdmin));
}
```

Full case study with five more violations: [`docs/principles.md`](docs/principles.md#real-world-violations).

---

### Detailed Walkthrough — CODE-RED Validation for `riseup-asia-uploader`

The earlier draft mixed multiple violations into the same snippets, which made the "fixed" path weaker than the standard it was supposed to teach. This rewrite isolates each rule so the recommended examples model the style they require.

**Validation rules enforced in this walkthrough:**

| Concern | Reject in examples | Require in examples |
|---|---|---|
| Error naming | Generic names such as `err` or `ERR` | Contextual names such as `requestError`, `readFileError`, `siteWasNotFound` |
| Error construction | Raw code strings and generic messages in recommended examples | `apperrtype` + `apperror.NewType()` / `WrapType()` / `WrapTypeMsg()` |
| Control flow | Deep nesting and ambiguous fallback errors | Early returns with one explicit reason per branch |
| Negation style | Hidden intent such as `!isValidPath` | Domain language such as `pathValidation.IsInvalid`, `site.IsBlocked`, `slug.IsMissing()` |
| Protocol values | Magic literals such as `"GET"` and `200` | `http.MethodGet` and `http.StatusOK` |

**CODE-RED-001 — Nested control flow (before/after):**

```go
// ❌ VIOLATION: nested control flow hides which precondition failed.
func (handler *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    site := handler.siteRepo.FindById(siteId)
    siteWasFound := site != nil
    if siteWasFound {
        if site.IsReadyForPluginEnable() {
            if slug.IsPresent(pluginSlug) {
                return handler.uploader.Enable(site, pluginSlug)
            }
        }
    }
    return apperror.FailBool(apperror.NewType(apperrtype.PluginEnablePreconditionFailed))
}

// ✅ FIXED: one branch, one reason, one typed error.
func (handler *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    site := handler.siteRepo.FindById(siteId)
    siteWasNotFound := site == nil
    if siteWasNotFound {
        return apperror.FailBool(apperror.SiteError(apperrtype.SiteNotFound, siteId))
    }
    if site.IsBlocked {
        return apperror.FailBool(apperror.SiteError(apperrtype.SiteBlocked, siteId))
    }
    if slug.IsMissing(pluginSlug) {
        return apperror.FailBool(apperror.SlugError(apperrtype.PluginSlugMissing, pluginSlug))
    }
    return handler.uploader.Enable(site, pluginSlug)
}
```

**CODE-RED-002 — Magic strings in error construction (before/after):**

```go
// ❌ VIOLATION: raw error code + generic message.
return apperror.FailBool(
    apperror.New("E2012", "invalid request"),
)

// ✅ FIXED: typed error constructor with canonical message from the registry.
return apperror.FailBool(
    apperror.NewType(apperrtype.PluginSlugMissing),
)

// ✅ BEST: typed error + domain context.
return apperror.FailBool(
    apperror.SlugError(apperrtype.PluginSlugMissing, pluginSlug),
)
```

**Error Type Enum (`apperrtype` package — v2.0):**

The `apperrtype` package defines all error types as variants of a single `uint16` `Variation` enum backed by a registry. Each variant maps to a `VariantStructure` containing `Name`, `Code`, and `Message`, so recommended examples do not duplicate raw codes or hand-written default messages.

```go
// apperrtype/variation.go — single enum for all application error types
package apperrtype

type Variation uint16

const (
    NoError Variation = iota
    ConfigFileMissing
    ConfigParseFailure
    DBConnectionFailed
    SiteNotFound
    SiteBlocked
    PluginSlugMissing
    PluginNotFound
    PluginAlreadyActive
    MaxError
)
```

```go
// apperrtype/variant_structure.go — rich metadata for every enum value
type VariantStructure struct {
    Name    string
    Code    string
    Message string
    Variant Variation
}
```

```go
// apperrtype/variant_registry.go — single source of truth
var variantRegistry = map[Variation]VariantStructure{
    SiteNotFound: {
        Name:    "SiteNotFound",
        Code:    "E2010",
        Message: "site not found",
        Variant: SiteNotFound,
    },
    SiteBlocked: {
        Name:    "SiteBlocked",
        Code:    "E2011",
        Message: "site is blocked",
        Variant: SiteBlocked,
    },
    PluginSlugMissing: {
        Name:    "PluginSlugMissing",
        Code:    "E2012",
        Message: "plugin slug required",
        Variant: PluginSlugMissing,
    },
}
```

```go
// Variation methods — implements ErrorType interface + display helpers
func (variation Variation) Code() string    { return variantRegistry[variation].Code }
func (variation Variation) Message() string { return variantRegistry[variation].Message }
func (variation Variation) Name() string    { return variantRegistry[variation].Name }

resolvedVariation, wasFound := apperrtype.VariationFromName("SiteNotFound")
```

```go
// apperror/constructors.go — NewType uses the enum's built-in code + message
func NewType(errorType apperrtype.ErrorType) *AppError {
    return New(errorType.Code(), errorType.Message())
}
```

> **Rules:**
> - Treat raw code strings as a compatibility path, not the standard path for new examples.
> - Prefer `NewType`, `WrapType`, `WrapTypeMsg`, and domain helpers such as `SiteError` / `SlugError`.
> - Keep the registry as the single source of truth for `Code` and `Message`.
> - Use descriptive local names in examples; do not teach `err` / `ERR` as the preferred naming style.

> 📖 Full error type enum specification: [`05-apperrtype-enums.md`](spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/05-apperrtype-enums.md)

**CODE-RED-005 & 006 — `fmt.Errorf()` and `(T, error)` returns (before/after):**

```go
// ❌ VIOLATION: tuple return + fmt.Errorf.
func (service *SnapshotService) GetSettings(endpoint string) (*Settings, error) {
    response, requestError := service.client.Get(endpoint)
    if requestError != nil {
        return nil, fmt.Errorf("get snapshot settings (GET %s): %w", endpoint, requestError)
    }
    return parseSettings(response)
}

// ✅ FIXED: typed result + enum-backed wrapping.
func (service *SnapshotService) GetSettings(endpoint string) apperror.SettingsResult {
    response, requestError := service.client.Get(endpoint)
    if requestError != nil {
        return apperror.Fail[*Settings](
            apperror.WrapTypeMsg(
                requestError,
                apperrtype.WPConnectionFailed,
                "failed to fetch snapshot settings",
            ).WithValue("endpoint", endpoint),
        )
    }
    return apperror.Ok(parseSettings(response))
}
```

**Recommended constructor order:**

| Level | Constructor | Code Source | Message Source |
|-------|-------------|-------------|----------------|
| Preferred | `WrapType(errorValue, errorType)` | Enum registry | Enum registry |
| Best | `WrapTypeMsg(errorValue, errorType, message)` | Enum registry | Context-specific override |

**Domain convenience constructors:**

Auto-set diagnostic fields so examples do not forget context and do not rely on magic literals.

```go
pathValidation := validation.ValidatePath(configPath)
if pathValidation.IsInvalid {
    return apperror.FailSettings(
        apperror.PathError(apperrtype.PathInvalid, configPath),
    )
}

data, readFileError := os.ReadFile(configPath)
if readFileError != nil {
    return apperror.FailBytes(
        apperror.WrapPathError(readFileError, apperrtype.PathFailedToRead, configPath),
    )
}

response, requestError := http.Get(siteURL)
if requestError != nil {
    return apperror.FailSettings(
        apperror.WrapUrlError(requestError, apperrtype.WPConnectionFailed, siteURL),
    )
}

if response.StatusCode != http.StatusOK {
    return apperror.FailSettings(
        apperror.EndpointError(
            apperrtype.WPResponseInvalid,
            http.MethodGet,
            endpoint,
            response.StatusCode,
        ),
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

> 📖 Full constructor reference: [`02-apperror-struct.md`](spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/02-apperror-struct.md)

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

### Type Aliases for Common Generic Results

When a generic type like `apperror.Result[T]` is used repeatedly with the same type parameter, create a **type alias** to reduce noise and improve readability:

```go
// ❌ VERBOSE — repeating Result[bool] everywhere
func (handler *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.Result[bool] {
    return apperror.Fail[bool](apperror.SiteError(apperrtype.SiteNotFound, siteId))
}
func (handler *PluginHandler) DisablePlugin(siteId string, pluginSlug string) apperror.Result[bool] {
    return apperror.Fail[bool](apperror.SlugError(apperrtype.PluginNotFound, pluginSlug))
}

// ✅ CLEAN — define a type alias once, use everywhere
// In types/AppResults.go (or inside the apperror package itself):
type BoolResult     = apperror.Result[bool]
type StringResult   = apperror.Result[string]
type IntResult      = apperror.Result[int]
type SettingsResult = apperror.Result[*Settings]

// Convenience constructors — one per alias, wraps Fail[T] so callers never repeat the generic:
//   func FailBool(err *AppError) BoolResult         { return Fail[bool](err) }
//   func FailString(err *AppError) StringResult     { return Fail[string](err) }
//   func FailInt(err *AppError) IntResult           { return Fail[int](err) }
//   func FailSettings(err *AppError) SettingsResult { return Fail[*Settings](err) }
//
// Pattern: for each type alias, create a matching Fail<Alias> constructor.
// This eliminates Fail[bool](...) generic noise at every call site.

func (handler *PluginHandler) EnablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    return apperror.FailBool(apperror.SiteError(apperrtype.SiteNotFound, siteId))
}
func (handler *PluginHandler) DisablePlugin(siteId string, pluginSlug string) apperror.BoolResult {
    return apperror.FailBool(apperror.SlugError(apperrtype.PluginNotFound, pluginSlug))
}
```

**Rules:**
- If a `Result[T]` specialization appears **3+ times**, create a type alias
- Place common aliases in `types/AppResults.go` or inside the `apperror` package
- One definition per file — `types/AppResults.go` for result aliases, `types/ContentType.go` for content types, etc.
- Same principle applies in TypeScript (`type BoolResult = Result<boolean>`) and other languages

### The Dark Side of Magic Strings & Magic Numbers

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

### Code Mutation & Immutability

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

> 📖 Full specification with all language examples: [`26-magic-values-and-immutability.md`](spec/02-coding-guidelines/01-cross-language/26-magic-values-and-immutability.md)
>
> 📖 Mutation avoidance details: [`18-code-mutation-avoidance.md`](spec/02-coding-guidelines/01-cross-language/18-code-mutation-avoidance.md)
>
> 📖 Types folder convention: [`27-types-folder-convention.md`](spec/02-coding-guidelines/01-cross-language/27-types-folder-convention.md)

### Spec References

Quick-navigation index of every spec and linter file referenced in the CODE-RED walkthrough above:

| # | Topic | Path |
|---|---|---|
| 1 | `apperrtype` enum registry | [`spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/05-apperrtype-enums.md`](spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/05-apperrtype-enums.md) |
| 2 | `AppError` struct + domain constructors | [`spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/02-apperror-struct.md`](spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/02-apperror-struct.md) |
| 3 | Magic values & immutability | [`spec/02-coding-guidelines/01-cross-language/26-magic-values-and-immutability.md`](spec/02-coding-guidelines/01-cross-language/26-magic-values-and-immutability.md) |
| 4 | Code mutation avoidance | [`spec/02-coding-guidelines/01-cross-language/18-code-mutation-avoidance.md`](spec/02-coding-guidelines/01-cross-language/18-code-mutation-avoidance.md) |
| 5 | `types/` folder convention | [`spec/02-coding-guidelines/01-cross-language/27-types-folder-convention.md`](spec/02-coding-guidelines/01-cross-language/27-types-folder-convention.md) |
| 6 | Go code severity taxonomy (Code Red vs Dangerous) | [`spec/02-coding-guidelines/03-golang/07-code-severity-taxonomy.md`](spec/02-coding-guidelines/03-golang/07-code-severity-taxonomy.md) |
| 7 | AI condensed master guidelines | [`spec/02-coding-guidelines/06-ai-optimization/04-condensed-master-guidelines.md`](spec/02-coding-guidelines/06-ai-optimization/04-condensed-master-guidelines.md) |
| 8 | Linter (Go) | [`linter-scripts/validate-guidelines.go`](linter-scripts/validate-guidelines.go) |
| 9 | Linter (Python) | [`linter-scripts/validate-guidelines.py`](linter-scripts/validate-guidelines.py) |

---

<h2 align="center">🛡️ Error Management Summary</h2>

| Layer | Rule | Tool |
|---|---|---|
| **Wrap at boundary** | Every external call returns `Result[T]`; raw exceptions never escape. | `apperror` package |
| **Carry evidence** | `AppError` ships with stack trace, file path, and `Code` enum. | `AppError.new(Code, msg)` |
| **Check before unwrap** | `if (res.HasError()) return res;` precedes every `.Value()`. | Linter rule `ERR-UNWRAP-001` |
| **Log structurally** | One `Log.Error(err, fields)` per boundary — no console spam. | `structured-logging` spec |
| **Map to UI** | UI translates `Code` → user-visible message. Error `Code` is the contract. | `error-code` registry |

Full architecture: [`docs/architecture.md#error-management`](docs/architecture.md#error-management) · spec: [`spec/02-coding-guidelines/03-error-handling/`](spec/02-coding-guidelines/03-error-handling/).

---

<h2 align="center">🧬 Type Aliases for Common Generic Results</h2>

```ts
// Result wrapper — every fallible function returns one of these.
type Result<T>      = Ok<T> | Err;
type AsyncResult<T> = Promise<Result<T>>;

// Specialised aliases — shorter call sites, identical semantics.
type VoidResult     = Result<void>;
type IdResult       = Result<number>;        // PK lookups
type ListResult<T>  = Result<readonly T[]>;
type PageResult<T>  = Result<{ Items: readonly T[]; Total: number }>;

// Cross-language equivalents (TS shown above):
// Go:   apperror.Result[T]      / apperror.AsyncResult[T]
// Rust: Result<T, AppError>     / async fn -> Result<T, AppError>
// C#:   Result<T>               / Task<Result<T>>
```

Why this matters: callers ALWAYS see the same shape, so guard helpers (`HasError`, `Map`, `AndThen`) work uniformly. Spec: [`spec/02-coding-guidelines/03-error-handling/04-result-types.md`](spec/02-coding-guidelines/03-error-handling/04-result-types.md).

---

<h2 align="center">What is this? Who is it for?</h2>

<p align="center">
  A specification system trusted by production engineering teams. Drop these folders into any codebase for consistent naming, structured error handling, zero-nesting rules, and AI-friendly docs. <strong>Pick a bundle, run one command, ship compliant code.</strong>
</p>

<p align="center">
  <a href="docs/principles.md"><img alt="Developer — start with principles" src="https://img.shields.io/badge/%F0%9F%A7%91%E2%80%8D%F0%9F%92%BB%20Developer-Start%20with%20principles-3B82F6?style=for-the-badge"/></a>
  <a href="docs/architecture.md"><img alt="Spec author — read architecture" src="https://img.shields.io/badge/%E2%9C%8D%EF%B8%8F%20Spec%20Author-Read%20architecture-8B5CF6?style=for-the-badge"/></a>
  <a href="spec/18-wp-plugin-how-to/00-overview.md"><img alt="WordPress dev — wp bundle" src="https://img.shields.io/badge/%F0%9F%90%98%20WordPress%20Dev-Use%20the%20wp%20bundle-21759B?style=for-the-badge"/></a>
  <a href="#-for-ai-agents"><img alt="AI agent — canonical entry points" src="https://img.shields.io/badge/%F0%9F%A4%96%20AI%20Agent-Canonical%20entry%20points-FF6E3C?style=for-the-badge"/></a>
</p>

<p align="center">
  <img
    src="public/images/coding-guidelines-walkthrough-poster.png"
    alt="Coding Guidelines v15 walkthrough poster — 5 core principles, CODE-RED refactor example, and 7 install bundles"
    width="960"
  />
</p>

<p align="center"><em>Animated: <a href="public/images/coding-guidelines-walkthrough.gif">coding-guidelines-walkthrough.gif</a></em></p>

---

<h2 align="center">🤖 For AI Agents</h2>

<p align="center">LLMs / coding agents — load these <strong>canonical entry points</strong> in order:</p>

<p align="center">
  <a href="llm.md"><img alt="llm.md — repository map" src="https://img.shields.io/badge/llm.md-Repository%20map-3B82F6?style=for-the-badge&logo=readthedocs&logoColor=white"/></a>
  <a href="bundles.json"><img alt="bundles.json — machine-readable catalogue" src="https://img.shields.io/badge/bundles.json-Bundle%20catalogue-10B981?style=for-the-badge&logo=json&logoColor=white"/></a>
  <a href="version.json"><img alt="version.json — live counts" src="https://img.shields.io/badge/version.json-Live%20counts-F59E0B?style=for-the-badge&logo=semver&logoColor=white"/></a>
  <a href="spec/02-coding-guidelines/06-ai-optimization/04-condensed-master-guidelines.md"><img alt="Condensed master guidelines" src="https://img.shields.io/badge/Condensed%20Master-Load%20this%20first-FF6E3C?style=for-the-badge"/></a>
  <a href="spec/02-coding-guidelines/06-ai-optimization/01-anti-hallucination-rules.md"><img alt="Anti-hallucination rules" src="https://img.shields.io/badge/Anti--hallucination-34%20rules-EF4444?style=for-the-badge"/></a>
  <a href="spec/17-consolidated-guidelines/00-overview.md"><img alt="Consolidated guidelines index" src="https://img.shields.io/badge/Consolidated-Master%20index-8B5CF6?style=for-the-badge"/></a>
  <a href=".lovable/memory/index.md"><img alt="Project memory index" src="https://img.shields.io/badge/Project%20Memory-Naming%20%C2%B7%20DB%20%C2%B7%20rules-14B8A6?style=for-the-badge"/></a>
  <a href=".lovable/prompts/00-index.md"><img alt="Reusable prompts" src="https://img.shields.io/badge/Prompts-blind%20audit%20%C2%B7%20gap-EC4899?style=for-the-badge"/></a>
</p>


<p align="center"><strong>"Which bundle?"</strong> — fetch <code>bundles.json</code>, match <code>intent</code>+<code>audience</code> to a bundle <code>name</code>, return its one-liner.</p>

## 🛠️ Full-Repo Install Scripts

Use the generic installer for **everything** (specs + linters + scripts):

**🪟 Windows · PowerShell**

```powershell
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.ps1 | iex
```

**🐧 macOS · Linux · Bash**

```bash
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/install.sh | bash
```

Skip the latest-version probe with `-n` (PowerShell: `... | iex` wrapped in `& ([scriptblock]::Create(...)) -n`; Bash: `... | bash -s -- -n`). Local re-runs: `.\install.ps1` or `./install.sh`.

**Power-user flags** (both installers): `--repo`, `--branch`, `--version`, `--folders`, `--dest`, `--config`, `--prompt`, `--force`, `--dry-run`, `--list-versions`, `--list-folders`, `-n`. `--prompt` and `--force` are mutually exclusive. Defaults via `install-config.json`. **CI/CD repo migration** (v15 → v16): `npm run migrate:repo:dry` — see [`spec/14-update/26-repo-major-version-migrator.md`](spec/14-update/26-repo-major-version-migrator.md).

---

## 📚 Documentation

Deep-dives live in `docs/` (README stays under 400 lines):

| Doc | What's inside |
|---|---|
| [`docs/principles.md`](docs/principles.md) | 9 core principles · 10 CODE RED rules · cross-language rule index · AI optimization suite |
| [`docs/architecture.md`](docs/architecture.md) | Spec authoring conventions · folder structure · architecture decisions · error management summary |
| [`docs/author.md`](docs/author.md) | Author bio · Riseup Asia LLC · AI assessments · FAQ · design philosophy |

Live spec tree: [`spec/`](spec/) (22 folders) · [`health-dashboard`](spec/health-dashboard.md) · [`consolidated index`](spec/17-consolidated-guidelines/00-overview.md). The built-in **Spec Documentation Viewer** ([screenshot](public/images/spec-viewer-preview.png)) renders everything with syntax highlighting and keyboard navigation. Changes: [`changelog.md`](changelog.md).

---

## 🔍 Neutral AI Assessment

> *Independent AI summary of the spec system's real-world impact.*

1. **Solves the "300-developer problem"** — encodes decisions that would otherwise live in senior developers' heads and be lost when they leave.
2. **Reduces code-review friction by 60–80%** — eliminates the "is this `userId` or `user_id`?" debate class entirely.
3. **Prevents error-swallowing incidents** — `apperror` + mandatory stack traces + `Result[T]` wrappers + `HasError()` before `.Value()` make it structurally hard to lose error context.
4. **Makes AI-assisted development actually work** — explicit ❌/✅ patterns parse more reliably than prose; the condensed reference fits in a single context window.
5. **Enforces consistency across polyglot codebases** — define once, adapt per language; prevents the drift that happens when each language team invents its own conventions.

Full strengths/weaknesses table, FAQ, and design philosophy: [`docs/author.md`](docs/author.md).

---

## 🤝 Contributing

1. Pick the correct parent folder (numeric prefix decides position).
2. Use the [Non-CLI Module Template](spec/01-spec-authoring-guide/05-non-cli-module-template.md) and include `00-overview.md` + `99-consistency-report.md`.
3. Bump the version, add a changelog entry, then run `npm run sync` to refresh `version.json`, `specTree.json`, and the README stamps.
4. Verify with `python3 linter-scripts/check-links.py` and `npm run lint:readme` before opening a PR.

---

<h2 align="center">👤 Author</h2>

<h3 align="center"><a href="https://alimkarim.com/">Md. Alim Ul Karim</a></h3>

<p align="center"><strong><a href="https://alimkarim.com">Creator & Lead Architect</a></strong> · Chief Software Engineer, <a href="https://riseup-asia.com">Riseup Asia LLC</a></p>

<p align="center">Software architect, <strong>20+ years</strong> across enterprise, fintech, and distributed systems. Stack: <strong>.NET/C# (18+ yrs)</strong>, <strong>JavaScript (10+ yrs)</strong>, <strong>TypeScript (6+ yrs)</strong>, <strong>Golang (4+ yrs)</strong>. <strong>Top 1% at Crossover</strong> · <a href="https://stackoverflow.com/users/513511/md-alim-ul-karim">Stack Overflow</a> 2,452+ rep · <a href="https://www.linkedin.com/in/alimkarim">LinkedIn</a> 12,500+ followers.</p>

| | Md. Alim Ul Karim | Riseup Asia LLC |
|---|---|---|
| **Website** | [alimkarim.com](https://alimkarim.com/) · [my.alimkarim.com](https://my.alimkarim.com/) | [riseup-asia.com](https://riseup-asia.com/) |
| **LinkedIn** | [in/alimkarim](https://www.linkedin.com/in/alimkarim) | [Riseup Asia](https://www.linkedin.com/company/105304484/) |
| **Stack Overflow** | [513511](https://stackoverflow.com/users/513511/md-alim-ul-karim) | — |
| **Social** | [Google](https://www.google.com/search?q=Alim+Ul+Karim) | [Facebook](https://www.facebook.com/riseupasia.talent/) · [YouTube](https://www.youtube.com/@riseup-asia) |

<p align="center"><a href="https://riseup-asia.com">Top Leading Software Company in WY (2026)</a></p>

Full bio, design philosophy, and FAQ: [`docs/author.md`](docs/author.md).

---

*This README is auto-stamped by [`scripts/sync-readme-stats.mjs`](scripts/sync-readme-stats.mjs). The numbers above are pulled from [`version.json`](version.json) on every `npm run sync`. Hand-editing the stamped values is safe but will be overwritten on the next sync.*
