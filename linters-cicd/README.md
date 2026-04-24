# `linters-cicd/` — Coding-Guidelines Linter Pack

Portable, language-agnostic CI/CD checks for the **CODE RED** rules from
this repository's coding guidelines. Drop into any pipeline with one line.

> **Spec:** [`spec/02-coding-guidelines/06-cicd-integration/`](../spec/02-coding-guidelines/06-cicd-integration/00-overview.md)

---

## Quick start

### GitHub Actions (one-liner)

```yaml
- uses: alimtvnetwork/coding-guidelines-v15/linters-cicd@v3.9.0
  with:
    path: .
```

### Any other CI

```bash
curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v15/releases/latest/download/install.sh | bash
bash ./linters-cicd/run-all.sh --path . --output coding-guidelines.sarif
```

### Local run (text output)

```bash
bash ./linters-cicd/run-all.sh --path . --format text
```

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
| GitHub composite Action | `uses: alimtvnetwork/coding-guidelines-v15/linters-cicd@vX.Y.Z` |
| Versioned ZIP | Attached to every GitHub Release as `coding-guidelines-linters-vX.Y.Z.zip` |
| `install.sh` one-liner | `curl ... | bash` (verifies SHA-256) |

---

## CI templates

Copy-paste workflows for every major platform live under
[`ci/`](./ci/) — GitHub Actions, GitLab CI, Azure DevOps, Bitbucket
Pipelines, Jenkins, and a pre-commit hook.

---

## Author

Md. Alim Ul Karim · Riseup Asia LLC · 2026
