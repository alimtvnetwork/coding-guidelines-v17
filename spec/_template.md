# {Title of the Document}

**Version:** 1.0.0
**Updated:** YYYY-MM-DD
**AI Confidence:** Draft
**Ambiguity:** None

---

## Keywords

`keyword-one` · `keyword-two` · `keyword-three`

---

## Scoring

| Criterion | Status |
|-----------|--------|
| `00-overview.md` present in module | ✅ / ❌ |
| AI Confidence assigned | ✅ / ❌ |
| Ambiguity assigned | ✅ / ❌ |
| Keywords present | ✅ / ❌ |
| Scoring table present | ✅ / ❌ |

---

## Purpose

One paragraph: what this document specifies, who reads it, and what they should be able to do after reading it. No project marketing — just scope.

---

## Document Inventory

(For `00-overview.md` files only — list every sibling file in this module.)

| # | File | Purpose |
|---|------|---------|
| 01 | `01-…md` | … |
| 99 | `99-consistency-report.md` | Structural health check |

---

## Specification

The actual content. Use H2 (`##`) for top-level sections, H3 (`###`) for sub-sections, H4 (`####`) only when truly needed. Avoid H5+.

### Examples

Use fenced code blocks with the language hint set:

```ts
// TypeScript example
```

```go
// Go example
```

Tables for rule comparisons:

| ❌ Don't | ✅ Do | Why |
|---------|------|-----|
| … | … | … |

---

## Cross-References

Add file-relative links here. Always include `.md`. The block below is
wrapped in an HTML comment so the cross-link checker auto-skips its
placeholder targets — replace it with real links before committing.

<!-- placeholder cross-references — auto-skipped by check-spec-cross-links.py
- [Related module](../NN-related-module/00-overview.md)
- [Strictly-avoid quick reference](../17-consolidated-guidelines/00-strictly-avoid-quickref.md)
-->

---

## Pre-flight checklist (delete before committing)

- [ ] H1 title matches the file's purpose
- [ ] Version + Updated date filled in (ISO `YYYY-MM-DD`)
- [ ] AI Confidence + Ambiguity assigned
- [ ] Keywords list non-empty
- [ ] Scoring table filled in
- [ ] Cross-references resolve (run `python linter-scripts/check-spec-cross-links.py --root spec --repo-root .`)
- [ ] Validator passes (`python linter-scripts/validate-guidelines.py`)
- [ ] Sync scripts run in order — see `17-consolidated-guidelines/01-spec-authoring.md` §X.2

---

*Spec template — see `17-consolidated-guidelines/01-spec-authoring.md` for full authoring conventions.*