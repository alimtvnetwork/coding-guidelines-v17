# Coding Principles & Standards

> **Version:** <!-- STAMP:VERSION -->3.95.0<!-- /STAMP:VERSION -->
> **Updated:** <!-- STAMP:UPDATED -->2026-04-24<!-- /STAMP:UPDATED -->
> **Source of truth:** [`spec/02-coding-guidelines/`](../spec/02-coding-guidelines/00-overview.md). This page is a navigable summary — it does **not** redefine rules.

---

## Core Development Principles

- **With great power comes great responsibility** — *Uncle Ben (Spider-Man). Every developer wields the power of creation; use it wisely and own your impact.*
- **Make more projects at once** — *Scale through parallel workstreams, not serial bottlenecks.*
- **Steer the AI toward proper coding** — *AI is a tool, not a replacement for judgment. Guide it with clear specs and rigorous review.*
- **A function is an atomic bomb** — *By Alim Karim. One poorly designed function can destroy an entire codebase. Respect the blast radius.*
- **Specific types over `Any`, `Unknown`, or generics** — *In the worst case, use generic `T` — never surrender to type ambiguity.*
- **Managing error is more important than coding** — *A feature that crashes is worse than a feature that doesn't exist. Error handling is not optional.*
- **Spec first, then code** — *Writing the spec is thinking; coding is execution. Don't code until you know what you're building.*
- **Don't trust AI — use the best** — *Skepticism is healthy. Leverage Lovable, Claude Code, Emergent, or Bolt, but verify every output.*
- **Automate with GitHub workflows** — *Shell scripts and PowerShell in CI/CD eliminate human error and enforce consistency.*

---

## 🔴 CODE RED Rules (Automatic PR Rejection)

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

---

## Key Standards by Language

| Standard | Go | TypeScript | PHP | Rust | C# |
|----------|-----|-----------|-----|------|-----|
| Enum type | `byte` + `iota` | String enum | String-backed + `Type` suffix | Standard `enum` | PascalCase enum |
| Error handling | `apperror.Result[T]` | `Promise<T>` | `try/catch Throwable` | `Result<T, E>` | Exceptions + guard clauses |
| File naming | `PascalCase.go` | `PascalCase.tsx` | `PascalCase.php` | `snake_case.rs` | `PascalCase.cs` |
| Boolean prefix | `isActive` | `isActive` | `$isActive` | `is_active` | `IsActive` |
| Abbreviations | `Id` not `ID` | `Id` not `ID` | `Id` not `ID` | Rust stdlib conventions | `Id` not `ID` |

---

## Cross-Language Rule Index

| # | File | Category |
|---|------|----------|
| 02 | `02-boolean-principles/` | Naming — P1–P8 boolean rules (subfolder) |
| 03 | `03-casting-elimination-patterns.md` | Type Safety |
| 04 | `04-code-style/` | Style — braces, nesting, spacing, function size |
| 06 | `06-cyclomatic-complexity.md` | Architecture |
| 07 | `07-database-naming.md` | Type Safety |
| 08 | `08-dry-principles.md` | Architecture |
| 10 | `10-function-naming.md` | Naming |
| 12 | `12-no-negatives.md` | Naming |
| 13 | `13-strict-typing.md` | Type Safety |
| 14 | `14-test-naming-and-structure.md` | Testing |
| 15 | `15-master-coding-guidelines/` | Reference — consolidated cross-language |
| 16 | `16-lazy-evaluation-patterns.md` | Patterns |
| 17 | `17-regex-usage-guidelines.md` | Patterns |
| 18 | `18-code-mutation-avoidance.md` | Type Safety |
| 19 | `19-null-pointer-safety.md` | Type Safety |
| 20 | `20-nesting-resolution-patterns.md` | Patterns |
| 21 | `21-newline-styling-examples.md` | Style |
| 22 | `22-variable-naming-conventions.md` | Naming |
| 23 | `23-solid-principles.md` | Architecture |
| 24 | `24-boolean-flag-methods.md` | Method Design |
| 25 | `25-generic-return-types.md` | Type Safety |
| 26 | `26-magic-values-and-immutability.md` | Type Safety |
| 27 | `27-types-folder-convention.md` | Architecture |

Full reference: [`spec/02-coding-guidelines/01-cross-language/00-overview.md`](../spec/02-coding-guidelines/01-cross-language/00-overview.md).

---

## Worked Examples

The full before/after refactor catalogue (CODE-RED-001 nested-if, CODE-RED-005/006 raw `error` returns, `apperrtype` enum, magic-string elimination, mutation avoidance) lives in:

- [`spec/02-coding-guidelines/01-cross-language/20-nesting-resolution-patterns.md`](../spec/02-coding-guidelines/01-cross-language/20-nesting-resolution-patterns.md)
- [`spec/02-coding-guidelines/01-cross-language/26-magic-values-and-immutability.md`](../spec/02-coding-guidelines/01-cross-language/26-magic-values-and-immutability.md)
- [`spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/`](../spec/03-error-manage/02-error-architecture/06-apperror-package/01-apperror-reference/00-overview.md)

---

## AI Optimization Suite

| File | Purpose | Size |
|------|---------|------|
| `01-anti-hallucination-rules.md` | 34 rules preventing common AI mistakes | ~260 lines |
| `02-ai-quick-reference-checklist.md` | 72-check pre-output validation | ~148 lines |
| `03-common-ai-mistakes.md` | Top 15 AI mistakes with before/after | ~350 lines |
| `04-condensed-master-guidelines.md` | Sub-200-line distillation for AI context | ~219 lines |
| `05-enum-naming-quick-reference.md` | Cross-language enum cheat sheet | ~229 lines |

**Usage:** Load `04-condensed-master-guidelines.md` into your AI context, then validate output against `02-ai-quick-reference-checklist.md`.

Full folder: [`spec/02-coding-guidelines/06-ai-optimization/`](../spec/02-coding-guidelines/06-ai-optimization/00-overview.md).