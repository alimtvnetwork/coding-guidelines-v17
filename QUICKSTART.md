# Quickstart — Coding-Guidelines Linter Pack

> **Pack version:** v3.79.0
> **Updated:** 2026-04-23
> **Goal:** get from zero to a green/red SARIF report in under 2 minutes.

The pack is the script `linters-cicd/run-all.sh`. It scans your repo,
emits **SARIF 2.1.0**, and exits non-zero on CODE RED findings.

---

## 1. Run it locally (any OS with bash + Python 3)

### a. From inside this repo

```bash
bash ./linters-cicd/run-all.sh \
  --path . \
  --format sarif \
  --output coding-guidelines.sarif
```

### b. From any other repo (one-liner installer)

```bash
# Step 1 — install the pack into ./linters-cicd/
curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v17/releases/latest/download/install.sh | bash

# Step 2 — run it
bash ./linters-cicd/run-all.sh \
  --path . \
  --format sarif \
  --output coding-guidelines.sarif
```

### c. Pin a version (recommended for production)

```bash
curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v17/releases/download/v3.79.0/install.sh | bash
```

### d. Read the report in the terminal (no SARIF viewer needed)

```bash
bash ./linters-cicd/run-all.sh --path . --format text
```

### e. Common useful flags

| Flag | What it does |
|------|--------------|
| `--languages go,typescript` | Limit to specific languages (default: auto-detect) |
| `--rules CODE-RED-001` | Run only one rule |
| `--exclude-rules STYLE-002` | Skip noisy rules |
| `--jobs auto` | Parallelize across CPU cores |
| `--baseline .codeguidelines-baseline.sarif` | Only fail on **new** findings vs baseline |
| `--refresh-baseline .codeguidelines-baseline.sarif` | Snapshot current findings as the baseline |

### f. Exit codes

| Code | Meaning |
|------|---------|
| `0` | No findings (or `--refresh-baseline` mode) |
| `1` | One or more findings emitted — **fail the build** |
| `2` | Tool error (timeout, malformed input) |

---

## 2. Run it in GitHub Actions (copy-paste)

Save this as **`.github/workflows/coding-guidelines.yml`** in any repo:

```yaml
name: Coding Guidelines

on:
  pull_request:
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write   # required to upload SARIF to the Security tab
    steps:
      - uses: actions/checkout@v4

      - name: Run coding-guidelines linters
        uses: alimtvnetwork/coding-guidelines-v17/linters-cicd@v3.79.0
        with:
          path: .
          languages: go,typescript     # remove this line to auto-detect
          fail-on-warning: false       # true = STYLE warnings also block merge
```

That's it. The composite Action does install + run + SARIF upload in one
step. Findings will appear in three places:

1. **Pull request** — inline annotations on changed lines.
2. **Security tab** → **Code scanning** — full report with rule IDs.
3. **Actions tab** → workflow run → **Artifacts** — `coding-guidelines.sarif`.

### Don't want to use the composite Action?

Hand-rolled equivalent (uses `install.sh` + the official SARIF upload):

```yaml
- name: Install linter pack
  run: curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v17/releases/download/v3.79.0/install.sh | bash

- name: Run checks
  run: bash ./linters-cicd/run-all.sh --path . --format sarif --output coding-guidelines.sarif

- name: Upload SARIF
  if: always()
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: coding-guidelines.sarif
    category: coding-guidelines
```

---

## 3. Other CI platforms

Step-by-step starter kits live in
[`examples/other-repo-integration/`](./examples/other-repo-integration/):

- [GitLab CI](./examples/other-repo-integration/gitlab/)
- [Azure DevOps](./examples/other-repo-integration/azure-devops/)
- [Jenkins](./examples/other-repo-integration/jenkins/)

All of them run the **same three lines** — install, run, upload SARIF —
so behavior is identical across platforms.

---

## 4. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `bash: linters-cicd/run-all.sh: No such file or directory` | `install.sh` failed — re-run with internet access. |
| `python3: command not found` | Install Python 3.11+ (`apt install python3` / `brew install python`). |
| Exit `2` (tool error) | Re-run with `--check-timeout 60` and `--jobs 1` to isolate the failing check. |
| Too many findings on first run | Snapshot a baseline: `--refresh-baseline .codeguidelines-baseline.sarif`, commit it, then use `--baseline` going forward. |

Full spec: [`spec/02-coding-guidelines/06-cicd-integration/`](./spec/02-coding-guidelines/06-cicd-integration/).

---

*Maintained by Md. Alim Ul Karim · Riseup Asia LLC.*