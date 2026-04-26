# `linters-cicd/` — Coding-Guidelines Linter Pack

Portable, language-agnostic CI/CD checks for the **CODE RED** rules from
this repository's coding guidelines. Drop into any pipeline with one line.

> **Spec:** [`spec/02-coding-guidelines/06-cicd-integration/`](../spec/02-coding-guidelines/06-cicd-integration/00-overview.md)

---

## Quick start

### GitHub Actions (one-liner)

```yaml
- uses: alimtvnetwork/coding-guidelines-v17/linters-cicd@v3.9.0
  with:
    path: .
```

### Any other CI

```bash
curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v17/releases/latest/download/install.sh | bash
bash ./linters-cicd/run-all.sh --path . --output coding-guidelines.sarif
```

### Local run (text output)

```bash
bash ./linters-cicd/run-all.sh --path . --format text
```

---

## First-run integration checklist (for a blind AI agent)

Use this checklist when an autonomous AI agent is dropped into a
**brand-new repo** with no prior context and asked to wire in this
linter pack. Follow the steps **in order**. Do not skip, do not
improvise. Every step has a deterministic success signal — if you do
not see it, stop and report, do not "fix" by guessing.

### Pre-flight (read-only, no writes yet)

1. **Confirm the host shell.** Run `uname -s` and `python3 --version`.
   Required: any POSIX shell + Python ≥ 3.10. If Python is missing,
   stop — install it first; do **not** rewrite checks in another
   language.
2. **Detect the CI platform** by listing the repo root:
   - `.github/workflows/` → GitHub Actions (use the composite Action)
   - `.gitlab-ci.yml` → GitLab CI (copy from `examples/other-repo-integration/gitlab/`)
   - `azure-pipelines.yml` or `.azure/` → Azure DevOps
   - `Jenkinsfile` → Jenkins
   - none of the above → default to the `install.sh` + `run-all.sh` path
3. **Detect target languages** by file extension count
   (`.go`, `.ts`/`.tsx`, `.php`). Pass the result to `--languages`
   later. If detection is ambiguous, omit `--languages` and let the
   pack auto-detect — do **not** invent a language list.

### Install (one and only one of these)

4. **GitHub Actions repo:** add the snippet from
   [`ci/github-actions.yml`](./ci/github-actions.yml) verbatim. Pin to
   the exact tag printed in [`VERSION`](./VERSION). Do **not** use
   `@main` or `@latest` in committed workflows.
5. **Any other CI / local:** run the install one-liner exactly as
   written in *Quick start → Any other CI* above. Verification is
   **on by default** — never pass `-n` / `-NoVerify` on a first run.

### Smoke run (must pass before opening a PR)

6. Run: `bash ./linters-cicd/run-all.sh --path . --format text`
7. Expected first-run signals:
   - Exit `0` → clean repo, proceed to step 9.
   - Exit `1` → real findings; copy the text output into the PR
     description, do **not** auto-fix in the same commit.
   - Exit `2` → tool failure; re-run with `--debug-timeout` and
     report the stderr. Do **not** retry blindly more than twice.
8. Re-run with SARIF for CI upload:
   `bash ./linters-cicd/run-all.sh --path . --format sarif --output coding-guidelines.sarif`
   then validate with `python3 linters-cicd/scripts/validate-sarif.py coding-guidelines.sarif`.

### Wire into the pipeline

9. Commit the workflow file from step 4 **or** the platform template
   from [`examples/other-repo-integration/`](../examples/other-repo-integration/).
10. Upload `coding-guidelines.sarif` as a build artifact using the
    platform's native upload step — do not rename the file.
11. Open the PR. The job must run on `pull_request` and `push` to the
    default branch. Anything else is wrong; revert and re-read step 4.

### Outputs the AI should explicitly ignore

The following are **expected noise** on a first run and must **not**
trigger a fix-up commit, a workflow rewrite, or a retry loop:

| Output | Meaning | Action |
|---|---|---|
| `note: tree-sitter wheel cached` | First-run wheel download | Ignore |
| `warning: no <lang> files found, skipping` | Auto-detect skipped a language | Ignore |
| `STYLE-*` findings (warning severity) | Non-blocking style hints | Report, do not auto-fix |
| `__pycache__/` files appearing under `linters-cicd/` | Python bytecode cache | Do **not** commit; add to `.gitignore` if missing |
| Lines starting with `::debug::` (GitHub) | Action debug stream | Ignore unless reproducing a failure |
| `coding-guidelines.sarif` size > 1 MB | Large but valid | Ignore unless > 10 MB (then see [`99-troubleshooting.md`](../spec/02-coding-guidelines/06-cicd-integration/99-troubleshooting.md)) |
| Pre-existing version-drift warnings in repo READMEs | Unrelated to this pack | Ignore |

### Hard "do not" list for the AI

- Do **not** edit files under `linters-cicd/checks/`, `linters-cicd/codegen/`,
  or `linters-cicd/scripts/` to make findings disappear.
- Do **not** add `--severity warning` to silence errors.
- Do **not** pass `-n` to `install.sh` or `-NoVerify` to `install.ps1`.
- Do **not** pin to `@main`, `@latest`, or a branch name in committed CI.
- Do **not** commit the generated `coding-guidelines.sarif` to the repo.
- Do **not** "upgrade" pinned linter versions opportunistically — that
  is a separate, reviewed change governed by the version-sync workflow.

### Success definition

A first-run integration is **done** when, and only when, all of these
hold simultaneously: the workflow file is committed at a pinned tag,
the CI job runs green (or red with real findings reported, not
silenced), `coding-guidelines.sarif` is uploaded as an artifact, and
no file under `linters-cicd/` has been modified.

---

## What it checks (Phase 1)

| Rule | Severity | Languages |
|------|----------|-----------|
| `CODE-RED-001` No nested `if` | error | go, ts |
| `CODE-RED-002` Boolean naming | error | go, ts |
| `CODE-RED-003` Magic strings | error | go, ts |
| `CODE-RED-004` Function length 8–15 | error | go, ts |
| `CODE-RED-006` File length ≤ 300 | error | universal |
| `CODE-RED-008` Positive conditions | error | go, ts |
| `STYLE-002` No `else` after `return` | warning | go, ts |

Future phases add PHP, Python, Rust, and any language you ask for —
plugin model documented in
[`02-plugin-model.md`](../spec/02-coding-guidelines/06-cicd-integration/02-plugin-model.md).

---

## Output

SARIF 2.1.0 by default, plain text via `--format text`. The contract is
in [`01-sarif-contract.md`](../spec/02-coding-guidelines/06-cicd-integration/01-sarif-contract.md).

---

## Distribution

| Channel | How |
|---------|-----|
| GitHub composite Action | `uses: alimtvnetwork/coding-guidelines-v17/linters-cicd@vX.Y.Z` |
| Versioned ZIP | Attached to every GitHub Release as `coding-guidelines-linters-vX.Y.Z.zip` |
| `install.sh` one-liner | `curl ... | bash` (verifies SHA-256) |

---

## Installer exit codes

Both `install.sh` (`-n` flag) and `install.ps1` (`-NoVerify` switch) follow
the same exit-code contract from
[spec §8 — Exit Codes (Normative)](../spec/14-update/27-generic-installer-behavior.md#8-exit-codes-normative).

| Code | Meaning | Raised when verification is **ON** (default) | Raised when verification is **OFF** (`-n` / `-NoVerify`) |
|------|---------|----------------------------------------------|-----------------------------------------------------------|
| `0`  | Success | ✅ install completed and checksum matched     | ✅ install completed (checksum **not** validated)          |
| `1`  | Generic failure (download / extract) | ✅ | ✅ |
| `2`  | Unknown / invalid flag | ✅ | ✅ |
| `3`  | Pinned release or asset not found (PINNED MODE only) | ✅ | ✅ |
| `4`  | **Checksum mismatch** — downloaded zip does not match `checksums.txt` | ✅ exits `4` and aborts | ❌ **never raised** — corrupted or tampered files install silently |

### Verification ON (default, recommended)

```bash
curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v17/releases/latest/download/install.sh | bash
# checksum mismatch → exit 4
```

```powershell
irm https://github.com/alimtvnetwork/coding-guidelines-v17/releases/latest/download/install.ps1 | iex
# checksum mismatch → exit 4
```

### Verification OFF (`-n` / `-NoVerify`, NOT recommended)

```bash
curl -fsSL .../install.sh | bash -s -- -n
# checksum mismatch → NO exit 4 — install proceeds even on tampered zip
```

```powershell
& ([scriptblock]::Create((irm .../install.ps1))) -NoVerify
# checksum mismatch → NO exit 4 — install proceeds even on tampered zip
```

The PowerShell installer additionally prints a loud multi-line warning
banner on every `-NoVerify` run — see
[spec §9 — Security Considerations](../spec/14-update/27-generic-installer-behavior.md#9-security-considerations).

---

## CI templates

Copy-paste workflows for every major platform live under
[`ci/`](./ci/) — GitHub Actions, GitLab CI, Azure DevOps, Bitbucket
Pipelines, Jenkins, and a pre-commit hook.

---

## Author

Md. Alim Ul Karim · Riseup Asia LLC · 2026
