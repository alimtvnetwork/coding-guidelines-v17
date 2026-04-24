# Strictly Avoid — Quick Reference

**Version:** 3.2.0  
**Updated:** 2026-04-19

---

⛔ **Every rule below is a hard prohibition. Violating any of these is a blocking issue.**

---

## Folder & Structure

- **Never create `.lovable/memories/`** — only `.lovable/memory/` exists. Causes confusion, splits files, breaks indexes.
- **Never create per-task folders under `.lovable/`** like `completed-tasks/`, `pending-tasks/`, or a `suggestions/` directory — plans and suggestions each live in **one file** (`plan.md`, `suggestions.md`) with a `## Completed` / `## Implemented` section. See `.lovable/memory/avoid/01-avoid-per-task-folders.md`.
- **Never use `v1` namespace** — the project repo is `alimtvnetwork/coding-guidelines-v17`. Any `v1` reference is a bug.
- **Never touch the `.release` folder** — managed externally.
- **Never sync** `01-app`, `02-app-issues`, `03-general`, `03-tasks`, or `12-consolidated-guidelines` from upstream sibling repos. All maintained locally.

## Error Handling

- **Never swallow errors** — no empty `catch`, no `_ := fn()`. 🔴 CODE RED.
- **Never use generic error messages** — always include file path, entity ID, or operation context. 🔴 CODE RED.
- **Never use `fmt.Errorf`** — always use `apperror.Wrap()` with error codes.

## Naming

- **Never use underscores** in identifier names (Zero-Underscore policy) — except Rust identifiers and Go test files.
- **Never use `Not`/`No` prefixes on boolean DB columns** — `IsNotActive`, `HasNoLicense`, `HasNoAccess`, `HasNoChildren` are forbidden. Use the positive form or the **Approved Inverse** (`IsDisabled`, `IsInvalid`, `IsIncomplete`, `IsUnavailable`, `IsUnread`, `IsHidden`, `IsBroken`, `IsLocked`, `IsUnpublished`, `IsUnverified`). See `spec/04-database-conventions/01-naming-conventions.md` Rules 2 + 8 (v3.5.0). Enforced by `BOOL-NEG-001`.
- **Never use `can`, `was`, `will`, `not`, `no` as boolean prefixes** — only `is`/`has` (rarely `should`).
- **Never use UUIDs for primary keys** — integer PKs with `{TableName}Id` only.
- **Never use camelCase for DB columns or JSON keys** — PascalCase only.
- **Never persist a derived inverse boolean** as a second DB column — derive in code per Rule 9. Use `linters-cicd/codegen/`.

## Schema Design

- **Never omit `Description TEXT NULL`** from entity/reference/master-data tables (Rule 10).
- **Never omit `Notes` and `Comments` (TEXT NULL)** from transactional / invoice / billing / payment tables (Rule 11).
- **Never make these columns `NOT NULL`** — they are optional context (Rule 12).

## Code Style

- **Never nest `if` blocks** — zero nesting is absolute. 🔴 CODE RED.
- **Never exceed 15 lines per function** (excluding error handling and blanks).
- **Never use `any` in TypeScript** — use generics or `unknown` with narrowing.
- **Never use `interface{}`/`any` in Go exported APIs.**
- **Never use `unwrap()` in Rust production code.**
- **Never use magic strings** — always use enums or named constants.

## Suppressions

- **Never add an inline `codeguidelines:disable=` comment without a reason** — `STYLE-099` will flag it.

## Dependencies

- **Never upgrade Axios beyond 1.14.0 / 0.30.3** — versions 1.14.1 and 0.30.4 are blocked.

## Communication

- **Never append boilerplate** like "If you have any questions..." or "Do you understand? Always add this part...".

---

*Strictly avoid — v3.2.0 — 2026-04-19*
