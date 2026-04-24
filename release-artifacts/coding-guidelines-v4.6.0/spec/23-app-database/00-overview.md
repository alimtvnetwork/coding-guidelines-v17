# App Database

**Version:** 3.2.0  
**Updated:** 2026-04-16  
**AI Confidence:** Draft  
**Ambiguity:** None

---

## Keywords

`app-database` · `schema` · `migrations` · `queries` · `data-model`

---

## Scoring

| Criterion | Status |
|-----------|--------|
| `00-overview.md` present | ✅ |
| AI Confidence assigned | ✅ |
| Ambiguity assigned | ✅ |
| Keywords present | ✅ |
| Scoring table present | ✅ |

---

## Purpose

Application-specific database specifications. Covers the app's data model, table designs, migration strategies, query patterns, and any database decisions unique to this application. This complements the core `04-database-conventions/` (general naming/schema rules) and `05-split-db-architecture/` (SQLite partitioning) with app-specific schema details.

---

## Document Inventory

| # | File | Purpose |
|---|------|---------|
| — | *(empty — awaiting content)* | — |

---

## Cross-References

- [Database Conventions (Core)](../04-database-conventions/00-overview.md) — General naming, PK/FK, ORM conventions
- [Split DB Architecture](../05-split-db-architecture/00-overview.md) — SQLite partitioning and migration patterns
- [App](../21-app/00-overview.md) — App-specific features and workflows
- [Consolidated Database Conventions](../17-consolidated-guidelines/18-database-conventions.md) — Consolidated summary

---

*App database — created 2026-04-16*

---

## Verification

_Auto-generated section — see `spec/23-app-database/97-acceptance-criteria.md` for the full criteria index._

### AC-ADB-000: App-database conformance: Overview

**Given** Validate app database migrations against the schema-design rules.  
**When** Run the verification command shown below.  
**Then** Migrations are forward-only; PascalCase naming is preserved; new columns are nullable with no DEFAULT (Rule 12).

**Verification command:**

```bash
python3 linter-scripts/check-forbidden-strings.py
```

**Expected:** exit 0. Any non-zero exit is a hard fail and blocks merge.

_Verification section last updated: 2026-04-21_
