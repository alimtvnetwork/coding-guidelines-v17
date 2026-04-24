# Spec Audit Pipeline

One-command refresh of AI-implementation-readiness audit artifacts.

## Usage

```bash
bun run spec:audit
# or
node scripts/spec-audit/run-audit.mjs
```

## What it does

1. Walks every `spec/NN-*/` folder.
2. Sends each folder's markdown content to the Lovable AI Gateway with a strict scoring rubric.
3. Scores 5 axes (completeness, specificity, testability, consistency, ai_implementability) 0–100.
4. Excludes the 4 stub folders per `mem://constraints/skip-stub-spec-folders`.
5. Writes 3 artifacts to `spec-audit-output/`:
   - `spec-audit-report.md` — human-readable report
   - `spec-audit-scores.csv` — flat table for dashboards
   - `spec-audit-raw.json` — structured AI output

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `LOVABLE_API_KEY` | required | AI Gateway auth |
| `SPEC_AUDIT_MODEL` | `google/gemini-2.5-flash` | Override audit model |
| `SPEC_AUDIT_OUT_DIR` | `spec-audit-output` | Override output directory |

## Output directory

`spec-audit-output/` is generated and should not be committed. Add it to your local `.gitignore` if needed.
