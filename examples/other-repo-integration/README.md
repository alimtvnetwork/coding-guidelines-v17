# Wiring the Coding-Guidelines Linter into Another Repo

> **Version:** 1.0.0
> **Pack version targeted:** v3.79.0
> **Updated:** 2026-04-23

This folder is a **copy-paste starter kit** for teams who want to add the
`coding-guidelines-v15` linter pack to a repository that lives **outside**
this monorepo. Pick your CI platform, follow the numbered steps, commit
the file, push.

All three platforms produce the **same SARIF 2.1.0 file**
(`coding-guidelines.sarif`) so downstream tooling stays identical.

---

## What you get from every platform

| Item | Path | Purpose |
|------|------|---------|
| SARIF report | `coding-guidelines.sarif` | Machine-readable findings (schema 2.1.0) |
| Build artifact | uploaded by each CI | Download + audit findings |
| Non-zero exit | on CODE RED finding | Blocks merge automatically |

---

## Pick your platform

| Platform | Folder | Findings render in |
|----------|--------|--------------------|
| GitLab CI | [`gitlab/`](./gitlab/) | MR widget (Code Quality + SAST) |
| Azure DevOps | [`azure-devops/`](./azure-devops/) | SARIF SAST extension tab |
| Jenkins | [`jenkins/`](./jenkins/) | Warnings-NG plugin dashboard |

GitHub Actions users do **not** need this kit — use the one-liner
`uses: alimtvnetwork/coding-guidelines-v15/linters-cicd@v3.79.0` instead.

---

## The three-line contract (memorize this)

Every platform does the same thing:

```bash
# 1. INSTALL — downloads linters-cicd/ into the workspace
curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v15/releases/latest/download/install.sh | bash

# 2. RUN — emits SARIF, exits 1 on CODE RED
bash ./linters-cicd/run-all.sh --path . --format sarif --output coding-guidelines.sarif

# 3. UPLOAD — platform-specific artifact upload
```

Everything below is just glue around those three lines.

---

## Pinning a version (recommended)

`latest` is convenient for trying it; **pin a tag in production** so a new
release never surprises a passing build:

```bash
curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v15/releases/download/v3.79.0/install.sh | bash
```

---

*Maintained by Md. Alim Ul Karim · Riseup Asia LLC.*