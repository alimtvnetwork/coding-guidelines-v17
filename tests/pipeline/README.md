# Pipeline Smoke Tests

End-to-end smoke tests that exercise `linters-cicd/run-all.sh`
(the orchestrator) against fixtures and the real repo. These
tests are CI-blocking and complement the standalone unit tests
under `linters-cicd/tests/`.

| Script | Closes | Run locally |
|---|---|---|
| `check-bool-neg-001-pipeline.sh` | `.lovable/resolved-issues/01-bool-neg-001-pipeline-untested.md`, suggestion #04 | `npm run test:pipeline:bool-neg` |
| `check-orchestrator-flags.sh` | plan item #11, suggestion #13 | `npm run test:pipeline:orchestrator` |

Run both in sequence: `npm run test:pipeline`.

## What `check-bool-neg-001-pipeline.sh` proves

1. The orchestrator loads `BOOL-NEG-001` from `registry.json`.
2. The check runs end-to-end and emits findings into the merged SARIF.
3. The 10-name allow-list (`IsActive`, `IsDisabled`, ...) silently passes.
4. `--jobs auto` + `--check-timeout` do not drop or duplicate findings.
5. No rule-id collision with the synthetic `STYLE-099` finding.

## What `check-orchestrator-flags.sh` proves

The four v4.24.0 flags behave per spec:

- `--total-timeout N` + `--debug-timeout` → watchdog logs `armed → canceled` on fast completion.
- `--total-timeout 1` against the full repo → watchdog `fired` with `exceeded — terminating run` (or cleanly canceled on very fast hosts).
- `--split-by severity` → per-severity SARIF siblings (`*.error.sarif`, `*.warning.sarif`, ...).
- `--strict` → non-zero exit on unknown TOML keys.

## Adding a new pipeline test

Drop the script under `tests/pipeline/`, set its exit codes to:

- `0` — success
- `1` — drift / spec violation
- `2` — harness error

Then add a `test:pipeline:<name>` script in `package.json` and a CI step in `.github/workflows/ci.yml`.