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

### `reason` for `ignored-deleted` rows

The `reason` field on `ignored-deleted` rows is per-source so a
reviewer can see *why* a path was classified as deleted. Two source
vocabularies are emitted today:

| Source | Triggered by | `reason` substring (stable for log-grep) |
|---|---|---|
| `diff-D` | A real `D`-status row from `git diff --name-status` | `git diff reported D (deleted)` |
| `changed-files-D` | An authored `--changed-files` payload row shaped exactly `D\tpath` | `--changed-files payload row shaped` |

The full `reason` text is intentionally not part of the machine
contract (it may be re-worded for clarity), but the substrings above
are stable and safe to grep in CI logs. New provenance tags will be
added alongside their parser changes; an unknown tag falls back to
a clearly labelled "provenance unknown" reason rather than crashing.

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

## Ready-to-copy example: every `status` × scored / unscored

The worked example above shows the four most common cases. The
payload below is the **full matrix**: every `status` value in the
closed audit vocabulary paired with each shape `similarity` can
take (`{kind, score: int, old_path}`, `{kind, score: null,
old_path}`, and `null`). It's a verified `--with-similarity --json`
output, ready to drop straight into a fixture, a doc snippet, or
a downstream consumer's mock.

The same payload is shipped as a checked-in artifact at
[`linter-scripts/examples/rename-intake-audit.json`](examples/rename-intake-audit.json)
so test code can `json.load()` it without copy-paste drift.

| `status` | `similarity` shape | When it happens |
|---|---|---|
| `matched` | `{kind, score: int, old_path}` | Git's `R<nn>` / `C<nn>` row, post-state under `--root` with an allowed extension. |
| `matched` | `{kind, score: null, old_path}` | Authored `--changed-files` payload using `R\told\tnew` or `old => new` (no leading score). |
| `matched` | `null` | Plain `A` / `M` row — no rename/copy provenance to attach. |
| `ignored-extension` | `{kind, score: int, old_path}` | Renamed to / from an allow-listed extension; rename signal preserved so callers can audit it. |
| `ignored-extension` | `{kind, score: null, old_path}` | Same, but the source payload was unscored. |
| `ignored-extension` | `null` | Plain row whose extension isn't allow-listed. |
| `ignored-out-of-root` | `{kind, score: int, old_path}` | Rename whose post-state path falls outside `--root`. |
| `ignored-out-of-root` | `{kind, score: null, old_path}` | Same, unscored intake. |
| `ignored-out-of-root` | `null` | Plain row outside `--root`. |
| `ignored-missing` | `{kind, score: int, old_path}` | Rename whose post-state file vanished from disk (revert-during-push, .gitignore on checkout). |
| `ignored-missing` | `null` | Plain row whose post-state file is missing. |
| `ignored-deleted` | `null` | `D` row, or the **pre-state** half of a rename — there is no post-state to score, so `similarity` is **always** `null` for this status. |

> **Note** — `ignored-deleted` rows always carry `similarity: null`
> because the row represents a path that no longer exists; the
> rename's *new* side (with the score) is recorded as a separate
> `matched` / `ignored-*` row in the same audit.

```json
[
  {
    "path": "docs/new-name.md",
    "status": "matched",
    "reason": "under --root, extension allowed, file present on disk",
    "similarity": {"kind": "R", "score": 92, "old_path": "docs/old-name.md"}
  },
  {
    "path": "spec/copy.md",
    "status": "matched",
    "reason": "under --root, extension allowed, file present on disk",
    "similarity": {"kind": "C", "score": 75, "old_path": "spec/template.md"}
  },
  {
    "path": "spec/renamed-no-score.md",
    "status": "matched",
    "reason": "under --root, extension allowed, file present on disk",
    "similarity": {"kind": "R", "score": null, "old_path": "spec/old.md"}
  },
  {
    "path": "spec/copy-no-score.md",
    "status": "matched",
    "reason": "under --root, extension allowed, file present on disk",
    "similarity": {"kind": "C", "score": null, "old_path": "spec/src.md"}
  },
  {
    "path": "readme.md",
    "status": "matched",
    "reason": "under --root, extension allowed, file present on disk",
    "similarity": null
  },
  {
    "path": "spec/notes.txt",
    "status": "ignored-extension",
    "reason": "extension '.txt' not in allowlist ['.md']",
    "similarity": {"kind": "R", "score": 88, "old_path": "spec/legacy.txt"}
  },
  {
    "path": "spec/draft.txt",
    "status": "ignored-extension",
    "reason": "extension '.txt' not in allowlist ['.md']",
    "similarity": {"kind": "R", "score": null, "old_path": "spec/sketch.txt"}
  },
  {
    "path": "spec/scratch.txt",
    "status": "ignored-extension",
    "reason": "extension '.txt' not in allowlist ['.md']",
    "similarity": null
  },
  {
    "path": "tools/moved-here.md",
    "status": "ignored-out-of-root",
    "reason": "path is outside --root spec",
    "similarity": {"kind": "R", "score": 95, "old_path": "spec/moved-from-here.md"}
  },
  {
    "path": "tools/cloned-here.md",
    "status": "ignored-out-of-root",
    "reason": "path is outside --root spec",
    "similarity": {"kind": "C", "score": null, "old_path": "spec/cloned-from-here.md"}
  },
  {
    "path": "docs/outside.md",
    "status": "ignored-out-of-root",
    "reason": "path is outside --root spec",
    "similarity": null
  },
  {
    "path": "spec/missing-rename.md",
    "status": "ignored-missing",
    "reason": "post-state path is not on disk (reverted later in the push, or filtered by .gitignore on checkout)",
    "similarity": {"kind": "R", "score": 81, "old_path": "spec/old-missing-name.md"}
  },
  {
    "path": "spec/missing.md",
    "status": "ignored-missing",
    "reason": "post-state path is not on disk (reverted later in the push, or filtered by .gitignore on checkout)",
    "similarity": null
  },
  {
    "path": "spec/deleted.md",
    "status": "ignored-deleted",
    "reason": "git diff reported D (deleted)",
    "similarity": null
  }
]
```

Reading the payload: scan a row's `similarity`. `null` ⇒ no
rename/copy info (a plain row, or any `ignored-deleted` row).
An object whose `score` is an integer ⇒ git observed and rated
the pair. An object whose `score` is `null` ⇒ the row IS a
rename/copy (`kind` is meaningful) but no percentage was ever
recorded. Treat `score: 0` as "git observed and rated 0% similar"
— it is **not** the same as `score: null`.

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
  `--only-changed-status`, `--similarity-csv`.
- `linter-scripts/tests/test_with_similarity_flag.py` — executable
  examples of every shape documented above.
- `linter-scripts/tests/test_similarity_csv_export.py` — schema
  examples for the `--similarity-csv` export, including the
  scored-vs-unscored distinction.

## CSV export (`--similarity-csv PATH`)

For spreadsheet review (Excel, Numbers, LibreOffice, `csvkit`,
pandas), the same audit can be exported as RFC 4180 CSV to a file
path or to STDOUT (`-`). The header is **always**
`path,status,reason,kind,score,old_path` regardless of whether
`--with-similarity` was passed; the four similarity columns simply
stay empty when no `_RenameSimilarity` is attached.

| `score` cell | Meaning |
|---|---|
| Empty (`""`) | **Unscored** — plain A/M/D row, OR an authored `--changed-files` payload that omitted the percentage. |
| `"0"` | Git observed the rename/copy and rated the pair entirely dissimilar. |
| `"1"` … `"100"` | Git's similarity percentage. |

`ISBLANK(E2)` and `E2=0` are **not** the same condition — keep them
distinct when filtering. Dedupe and `--only-changed-status` run
BEFORE the export, so the CSV mirrors what you saw on STDERR.

## Per-kind score labels (`--similarity-labels`)

`score` is an integer, but its *meaning* depends on the row's kind:
for an `R` row it's how alike the two paths are (100 = byte-identical
move); for a `C` row it's how much of the source survived in the
copy (100 = verbatim duplicate). The two are not directly comparable
— a 90 % rename and a 90 % copy describe different observations.

`--similarity-labels` (opt-in, requires `--with-similarity`) makes
that distinction explicit by attaching a canonical `score_kind`
discriminator to every R/C row. The vocabulary is closed:

| `score_kind` | Applies to | Score semantics |
|---|---|---|
| `rename-similarity` | `kind=R`, integer score | How alike the two paths are. |
| `copy-similarity` | `kind=C`, integer score | How much of the source survived. |
| `unscored` | `kind=R` or `kind=C`, `score=null` | Kind is meaningful, magnitude isn't. |
| *(absent / empty)* | plain A/M/D rows | No rename/copy provenance to label. |

Surfaces touched:

- **JSON audit** — adds `score_kind` to the nested `similarity`
  object. Plain rows whose `similarity` is `null` get no label
  (absence already means "no provenance"). The legacy schema is
  preserved byte-for-byte when the flag is off.
- **Text table** — appends a `meaning` column after `old`. Plain
  rows render `-` for visual consistency with the other similarity
  cells.
- **CSV export** — appends a 7th `score_kind` column. The first six
  columns are unchanged so positional readers that hard-code indices
  0–5 keep working without modification; opt into index 6 only when
  you care about the discriminator.

Score-of-`0` is classified by kind, **not** as `unscored` —
`unscored` is reserved for `score=null` (authored payloads without a
percentage). A `C` row with `score=0` is `copy-similarity` (git
observed the pair and rated them entirely dissimilar), not
`unscored`.