# `rename_intake` — diff-mode audit JSON schema

The `--list-changed-files` audit emitted by
[`check-placeholder-comments.py`](./check-placeholder-comments.py)
documents *which* repo-relative paths the diff-mode intake considered
and *why* each one was kept or skipped. With `--with-similarity` the
same payload is enriched with rename/copy provenance recovered from
`git diff --name-status -M -C` (or the equivalent
`--changed-files` payload).

This file is the canonical schema reference. It documents the JSON
shape, the score/unscored distinction, and the STDOUT/STDERR contract
so dashboards and downstream tools can ingest the audit without
scraping the human text table.

## Stream contract — STDERR vs STDOUT

The audit is **always written to STDERR**, regardless of `--json` or
the verbosity flags. STDOUT is reserved for the linter's primary
payload:

| Stream | Content | Format |
|---|---|---|
| **STDOUT** | The human violation summary, **or** with `--json` a single-document JSON object containing the violations array. | Always one well-formed document. |
| **STDERR** | The `--list-changed-files` audit table (text columns) **or** with `--json` a JSON array of `rename_intake` records. Plus the usual progress / dedupe-footer lines. | Text rows or one JSON array. |

This split lets a CI job pipe STDOUT into `jq` for violation triage
while a separate sink (artifact upload, dashboard ingest, log scraper)
consumes the audit on STDERR. **No interleaving.** A row never lands on
STDOUT and a violation never lands on STDERR.

The audit array is a single JSON document — it is emitted in one write
after all rows are collected, so partial / streaming readers see either
the complete array or nothing.

## Record schema

Each row is a JSON object with the following fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `path` | `string` | yes | Repo-relative POSIX path of the considered file (the post-rename / post-copy "new" side for R/C rows). |
| `status` | `string` | yes | One of the closed audit vocabulary: `matched`, `ignored-extension`, `ignored-out-of-root`, `ignored-missing`, `ignored-deleted`. |
| `reason` | `string` | yes | Human-readable explanation for the `status`. Stable enough for log search but not part of the machine contract — do not parse. |
| `similarity` | `object \| null` | only with `--with-similarity` | Rename/copy provenance, see below. Absent from the object entirely when the flag is not set (not `null`). |

Without `--with-similarity` the `similarity` key is **explicitly
removed** from every record so dashboards parsing the legacy schema
continue to work unchanged. The flag is purely additive.

### `similarity` sub-object

When `--with-similarity` is on, every record carries a `similarity`
key whose value is either `null` (plain `A` / `M` / `D` rows, no
rename/copy observed) or an object:

| Field | Type | Description |
|---|---|---|
| `kind` | `string` | `"R"` for rename, `"C"` for copy. No other values. |
| `score` | `integer \| null` | Git's similarity percentage (0–100), or `null` when the row is **unscored** — see next section. |
| `old_path` | `string` | The OLD-side repo-relative path the rename/copy is from. Always present on R/C rows. |

## `score` — scored vs unscored

Git emits the similarity percentage on `--name-status -M -C` rows
(e.g. `R092\told\tnew` → 92 % similar). The audit preserves that
integer verbatim in `score`. Two cases produce a `null` score, which
the text renderer prints as a single dash (`-`):

1. **Authored `--changed-files` payloads** that omit the percentage.
   Both shapes are accepted:
   - tab form `R\told\tnew` (no leading score) → `score: null`
   - arrow form `old => new` → `score: null`
   These are common when the changed-file list is hand-built or
   concatenated from tools that don't preserve git's score column.
2. **Plain rows** (`A` / `M` / `D`) where `similarity` itself is
   `null` — there is no rename/copy to score.

A score of `0` is **not** the same as a missing score. `0` means git
observed the rename pair and rated them entirely dissimilar; `null`
means the score was never recorded. Keep them distinct in dashboards.

The text renderer reserves the marker `?` for a future "unknown but
expected" state; it is **not currently emitted**. Today only `-` (for
`null`) and the integer string appear in the `score` column.

## Worked example

`git diff --name-status -M -C main...HEAD` against a branch that
renamed one file, copied one, modified one, and deleted one yields:

```text
R092    docs/old-name.md    docs/new-name.md
C075    spec/template.md    spec/copy.md
M       readme.md
D       legacy.md
```

With `python3 linter-scripts/check-placeholder-comments.py
--diff-base main --list-changed-files --with-similarity --json` the
STDERR audit is:

```json
[
  {
    "path": "docs/new-name.md",
    "status": "matched",
    "reason": "in --root and extension allowed",
    "similarity": {"kind": "R", "score": 92, "old_path": "docs/old-name.md"}
  },
  {
    "path": "spec/copy.md",
    "status": "matched",
    "reason": "in --root and extension allowed",
    "similarity": {"kind": "C", "score": 75, "old_path": "spec/template.md"}
  },
  {
    "path": "readme.md",
    "status": "matched",
    "reason": "in --root and extension allowed",
    "similarity": null
  },
  {
    "path": "legacy.md",
    "status": "ignored-deleted",
    "reason": "file no longer exists on disk (D row)",
    "similarity": null
  }
]
```

Drop `--with-similarity` and the four `similarity` keys disappear
entirely (legacy schema).

## Compatibility notes

- **Field order is not part of the contract.** Parse by key, not by
  position. The current implementation emits the keys in the order
  shown above, but that may change.
- **Unknown statuses** are never emitted today — the closed vocabulary
  is enforced at the renderer. New statuses, if added, will land in a
  major version bump and be announced in `CHANGELOG.md`.
- **`--dedupe-changed-files`** runs before serialisation; the JSON
  array contains at most one record per `path` when that flag is set,
  with first-seen-wins semantics applied to the `similarity` record
  too.
- **`--only-changed-status`** runs after dedupe and after similarity
  attachment, so filtered-out rows are absent from the array but their
  totals still appear in the human footer on STDERR.

## See also

- [`check-placeholder-comments.py --help`](./check-placeholder-comments.py)
  — full flag reference for `--list-changed-files`,
  `--with-similarity`, `--dedupe-changed-files`,
  `--only-changed-status`.
- `linter-scripts/tests/test_with_similarity_flag.py` — executable
  examples of every shape documented above.