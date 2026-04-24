# Spec Cross-Link Checker

`check-spec-cross-links.py` walks `spec/`, parses every markdown link, and
fails CI if any internal link points to a missing file or a non-existent
heading anchor.

## Local run

```bash
python3 linter-scripts/check-spec-cross-links.py --root spec
# Optional: JSON report
python3 linter-scripts/check-spec-cross-links.py --root spec --json
# Optional: GitHub annotations
python3 linter-scripts/check-spec-cross-links.py --root spec --github
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | All internal links resolve |
| 1    | One or more broken links / missing sections |
| 2    | Invocation error |

## What is checked

- Markdown links of the form `[text](path)` and `[text](path#anchor)`.
- Path must resolve to an existing file (relative to source `.md`, or absolute from repo root).
- If `#anchor` is present, it must match an existing H1–H6 heading slug in the target file.
- Links inside fenced code blocks (```` ``` ```` or `~~~`) are ignored — they are examples, not real references.
- External URLs (`http://`, `https://`, `mailto:`, etc.) and project schemes (`mem://`, `user-uploads://`, `knowledge://`) are skipped.

## Allowlist (waivers)

Known-broken links live in `linter-scripts/spec-cross-links.allowlist`,
one waiver per line:

```
# Comments start with `#` (only at line start; anchor `#` inside entries is preserved)
spec/path/to/file.md:42:./missing-target.md
spec/other.md:99:./file.md#missing-section
```

Format: `<relpath-from-repo-root>:<line>:<exact-target-as-written>`.
Remove a waiver as soon as the underlying link is fixed.

## CI

Runs as the `cross-links` job in `.github/workflows/ci.yml` on every push
and pull request to `main`.

---

## Auto-Fix Suggester (companion)

`suggest-spec-cross-link-fixes.py` consumes the same allowlist and the
same broken-link set as the checker, then proposes the closest match for
each failure using `difflib.SequenceMatcher`:

- `missing-file` → fuzzy-match against every `*.md` under `spec/` (basename
  match wins ties).
- `missing-section` → fuzzy-match the requested anchor against the slug of
  every heading in the resolved target file.

### Modes

| Flag | Behavior |
|------|----------|
| _(default)_ | Report-only. Always exits 0. Used by CI as advisory annotations. |
| `--apply` | Rewrite files in place when `confidence >= --min-confidence` (default `0.82`). Exits 1 if any low-confidence breakage remains. |
| `--github` | Emit GitHub Actions annotations (`::warning` for auto-fixable, `::notice` for manual-review). |
| `--json`   | Machine-readable report on stdout. |

### Local usage

```bash
# Preview what would change
python3 linter-scripts/suggest-spec-cross-link-fixes.py --root spec

# Apply high-confidence fixes only
python3 linter-scripts/suggest-spec-cross-link-fixes.py --root spec --apply

# Stricter threshold
python3 linter-scripts/suggest-spec-cross-link-fixes.py --root spec --apply --min-confidence 0.9
```

### CI integration

The `cross-links` job runs the suggester unconditionally after the
blocking checker. Suggestions are uploaded as the
`spec-cross-links-suggestions` artifact and surfaced as PR annotations.
The suggester never fails the build — it is purely advisory so reviewers
can opt in to applying fixes locally.
