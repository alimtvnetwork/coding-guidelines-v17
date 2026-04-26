# 03 — `--similarity-legend` rolled back; "update help with examples" target absent

## Task as received

> Update the CLI `--help` text with examples showing how to enable
> and disable the similarity legend for rename/copy intake.

## Ambiguity

The previous turn implemented `--similarity-legend={auto,on,off}` on
`linter-scripts/check-placeholder-comments.py` (CLI arg + resolver +
renderer + 19 tests in `tests/test_similarity_legend_flag.py`, full
suite 171/171 passing at the time). At the start of this turn the
working tree contains **none** of those changes:

* `rg "similarity.legend|_SIMILARITY_LEGEND|legend_mode"` over both
  the linter and the entire `tests/` directory returns zero hits.
* `linter-scripts/tests/test_similarity_legend_flag.py` does not
  exist.

Same silent-rollback pattern documented in
`02-prior-task-rolled-back.md` (which itself also rolled back). The
user's request "update the help text with examples" presupposes the
flag exists — so the literal phrasing is unsatisfiable in isolation.

## Inference applied (no-questions-mode)

Most reasonable interpretation: re-land the flag exactly as before,
then extend its `help=` string with concrete `Examples:` lines
showing how to enable (`--similarity-legend on`) and disable
(`--similarity-legend off`) the legend during a rename/copy intake
(`--list-changed-files --with-similarity` with a `--changed-files`
or `--diff-base` payload). The examples-in-help-text convention
matches the existing `--include-mdx` and `--include-txt` flags
(grep `Examples:` in the source).

## Follow-up the user may want

1. A persistent fix for the silent rollbacks (memory entry?
   git-hook? `.lovable/` policy?).
2. Whether the help should also document the `auto` default
   alongside the `on`/`off` examples — implemented as yes (a
   one-liner pinning the auto = "TTY only" semantic).
