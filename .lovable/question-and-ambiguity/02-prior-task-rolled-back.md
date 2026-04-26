# 02 — Prior task (per-source `ignored-deleted` reason) rolled back

## Original request (this task)
> Extend the `--json` output to include the new `ignored-deleted`
> status and reason for deleted paths in the changed-files audit
> trail.

## Context
The previous task in this session ("Add a `reason` value for each
audit-trail entry so I can see why a deleted path was marked
`ignored-deleted`") reported success and 131/132 passing tests, but
on inspection at the start of this task the working tree shows:

- `_DELETED_REASON` map: **absent**
- `_parse_name_status` / `_normalise_changed_lines` `deleted` param:
  still `list[str]`, not the `list[tuple[str, str]]` the prior task
  introduced
- `_resolve_changed_md` audit emitter: still using the old static
  `"git reported D (deleted): no post-state file to lint"` string
- `linter-scripts/tests/test_ignored_deleted_reason.py`: **does
  not exist on disk**
- README "`reason` for `ignored-deleted` rows" subsection: absent

i.e. the entire prior task was reverted before this task started.
Likely cause: an apply_patch session that returned success but
didn't persist, or a separate revert between turns.

## Ambiguity
How should "the new `ignored-deleted` status and reason" be
interpreted given that "new" doesn't actually exist in the tree?

## Options considered

### Option A — Re-implement the per-source reason work, then verify JSON carries it
- **Pros:** Restores the contract the prior task established;
  delivers what this task literally asks for (the JSON payload now
  carries the diversified per-source reason).
- **Cons:** Re-does work that was nominally done already; risks
  diverging slightly from the rolled-back version's exact text
  (kept identical here on purpose).

### Option B — Treat "new" as the existing single static reason, just confirm JSON shape
- **Pros:** Minimal change.
- **Cons:** The user clearly said "new" — the existing reason has
  been static for the lifetime of the audit trail. Doing nothing
  would silently fail the user's intent.

## Chosen — Option A
**Recommendation rationale:** The user's wording references "the
new" reason as if it already exists, which only makes sense if the
prior task's output is intended to persist. Re-applying the
per-source map is the only interpretation that makes both tasks
coherent.

## Reversibility
Trivial. The diff is the same as task 01's diff plus the JSON
coverage assertion. If the rollback was intentional, deleting the
`_DELETED_REASON` map + reverting the parser signatures restores
the prior state in a single revert.