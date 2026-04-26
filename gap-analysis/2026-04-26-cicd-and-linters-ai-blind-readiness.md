# Gap Analysis — Can a Blind AI Drop the Linters + CI/CD Pack into a New Repo?

**Date:** 2026-04-26
**Subject:** `linters-cicd/`, `linters/`, `linter-scripts/`, `examples/other-repo-integration/`
**Companion document:** [`2026-04-24-installer-blind-ai-readiness.md`](./2026-04-24-installer-blind-ai-readiness.md)
**Audited by:** Lovable AI gap-analysis pass

---

## TL;DR

| Dimension | Score | Verdict |
|-----------|------:|---------|
| Linter pack drop-in (a fresh AI installs `linters-cicd/` and gets it running) | **9.0 / 10** | One-liner works, install + run path is well-documented |
| CI/CD pipeline implementation (AI authors a working `.yml` for GitHub / GitLab / Azure / Jenkins) | **8.6 / 10** | GitHub is trivial; other CIs documented in `examples/other-repo-integration/` |
| Self-update / version-pinning workflow | **7.5 / 10** | Pinning is documented; auto-bump strategy isn't |
| Codegen verification step | **8.5 / 10** | Now wired in CI (`verify-codegen-determinism.sh` + regen-diff guard) — but feature-discovery is weak |
| Custom-rule extension (AI adds a new linter rule for a new repo's domain rules) | **6.5 / 10** | Plugin model exists in spec but has thin onboarding |
| **Overall AI-blind score** | **8.2 / 10** | Production-usable; gaps below |

---

## 1. What a blind AI WILL get right

Given only this repo's documentation (`linters-cicd/README.md`, `examples/other-repo-integration/`, `spec/02-coding-guidelines/06-cicd-integration/`, `spec/12-cicd-pipeline-workflows/`):

| Capability | Source |
|------------|--------|
| Install pack with one curl line | `linters-cicd/README.md` §Quick start |
| Run all checks and emit SARIF 2.1.0 | `linters-cicd/run-all.sh --format sarif --output coding-guidelines.sarif` |
| Wire into GitHub Actions in 5 lines | `linters-cicd/ci/github-actions.yml` (copy-paste ready) |
| Wire into GitLab / Azure / Jenkins | `examples/other-repo-integration/{gitlab,azure-devops,jenkins}/` (each has README + working pipeline file) |
| Pin a specific pack version | `examples/other-repo-integration/README.md` §"Pinning a version" |
| Pre-commit hook | `linters-cicd/ci/pre-commit-hook.sh` |
| Understand the rule set | `linters-cicd/checks/registry.json` enumerates every rule |
| Codegen drift detection (PHP/Go/TS field inversion tables) | `linters-cicd/codegen/scripts/verify-codegen-determinism.sh` + new CI job (`.github/workflows/ci.yml`) |
| Smoke-test the boolean-column-negative rule end-to-end | `tests/pipeline/check-bool-neg-001-pipeline.sh` |
| Validate orchestrator timeout / split / strict flags | `tests/pipeline/check-orchestrator-flags.sh` |

These are real, working artifacts. A fresh AI can wire any of the four major CIs into a new repo using nothing but the documentation in this repo.

---

## 2. What a blind AI WILL get wrong (or have to invent)

### 2.1 Implicit "what languages are supported today?"

| Source | Says |
|--------|------|
| `linters-cicd/README.md` Phase 1 table | Go, TS for most rules; "universal" for file-length |
| `linters-cicd/checks/registry.json` | Source of truth — but not surfaced in the README |
| `examples/other-repo-integration/` README | Doesn't mention language support at all |

**Impact:** An AI integrating the pack into a Python or Rust repo will assume it works, get zero findings (the rule files silently no-op for unsupported extensions), and ship a green build that lints nothing.

**Fix:** Surface a "supported languages today" matrix in `linters-cicd/README.md` AND in the per-platform README under `examples/other-repo-integration/`. Have `run-all.sh` print a `WARNING: 0 files matched supported extensions` when the language detection finds nothing.

### 2.2 No "first-run" output discipline

The shipped `run-all.sh` writes `coding-guidelines.sarif` into the CWD by default. There is no documented `.gitignore` line for it, so AI integrators will commit it. (The shipped repo itself has `linters-cicd/coding-guidelines.sarif` in its tree — exhibit A.)

**Fix:** Add to `examples/other-repo-integration/README.md`: "Add `coding-guidelines.sarif` to `.gitignore` in the consuming repo."

### 2.3 Version-pinning is documented; auto-update isn't

An AI integrating the pack into a long-lived repo needs a story for "how do I keep the pack up to date without breaking my build". The repo's own self-update story (Renovate/Dependabot config, version-bump PR template) is invisible to consumers.

**Fix:** Add `examples/other-repo-integration/renovate.json` (a Renovate config that watches the `coding-guidelines-v17` GitHub release tag and opens PRs to bump the pinned version in the consumer's CI file).

### 2.4 Custom-rule onboarding is buried

`spec/02-coding-guidelines/06-cicd-integration/02-plugin-model.md` defines the plugin model, but a blind AI tasked with "add a rule that flags `console.log` in production TS" has no copy-paste skeleton. The existing rule directories (`linters-cicd/checks/boolean-naming/`, etc.) are the only template — and they're undocumented as templates.

**Fix:** Add `linters-cicd/checks/_template/` with a 30-line skeleton + README walking through "how to add a rule in 10 minutes". The CI smoke-tests in `tests/pipeline/` should grow to cover the template too.

### 2.5 Codegen "what to do when the table changes" is implicit

The new CI guard fails the build with `Codegen drift detected` and instructs to run `npm run codegen:regen`. ✅ That's good. But:
- A blind AI in a downstream repo may not have `npm` or this script — the regen tool lives only in *this* repo.
- The codegen feature's purpose ("invert PHP/Go/TS field names so PascalCase columns map to snake_case structs") is documented in `linters-cicd/codegen/README.md`, but there's no mention of *whether downstream repos need it at all*. They probably don't.

**Fix:** Mark the codegen verification step as "internal to this repo only" in the CI workflow, OR document explicitly under `examples/other-repo-integration/README.md` that the codegen step is opt-in and only useful if the consumer adopts the same field-inversion pattern.

### 2.6 Pipeline test bash scripts assume a specific shell

`tests/pipeline/*.sh` use `bash` features (arrays, `set -euo pipefail`, process substitution). They will break on `sh`-only CI runners (some Alpine-based GitLab runners). Not flagged anywhere.

**Fix:** Add a `Requirements` section to `tests/pipeline/README.md` listing `bash >= 4`, `python3 >= 3.10`, `jq` (if used).

### 2.7 SARIF upload is GitHub-specific

The shipped `linters-cicd/ci/github-actions.yml` uploads SARIF to the Security tab via `permissions: security-events: write`. The other-repo-integration examples *do* show platform-specific equivalents, but the README's "What you get from every platform" table claims `coding-guidelines.sarif` is universal. The platform-native renderings (GitLab Code Quality, Azure SAST, Jenkins Warnings-NG) require additional adapters and are not all 1-to-1 with SARIF.

**Fix:** A short table in the integration README listing each platform's actual viewer fidelity (full SARIF / Code-Quality JSON / Warnings-NG XML) so AI integrators don't promise SARIF features the platform won't render.

---

## 3. Score-Card Per User Question

> **"Can the AI follow the linters and lint scripts in a new repo?"**

**Yes — 9.0 / 10.** The one-liner install, the SARIF contract, the run-all script, and the per-CI starter files are concrete enough that a blind AI builds a working integration in one shot. Failure mode: the AI doesn't realise the pack supports only Go + TS today and ships a no-op linter on a Python/Rust repo (§2.1).

> **"Can the AI implement the CI/CD?"**

**Yes for GitHub Actions — 9.5 / 10.** The composite action `uses: alimtvnetwork/coding-guidelines-v17/linters-cicd@v3.9.0` is one line.

**Yes for GitLab / Azure / Jenkins — 8.0 / 10.** Working pipelines exist in `examples/other-repo-integration/` but they are version-stamped at v3.79.0 in the README header (out of sync with the v3.9.0 referenced elsewhere), which will confuse a blind AI.

> **"Can the AI implement the update / self-update pipeline?"**

**Partially — 7.5 / 10.** Version pinning is documented; a Renovate / Dependabot config is missing (§2.3). See companion doc `2026-04-24-installer-blind-ai-readiness.md` for the installer-side gaps that compound this.

> **"Is there ambiguity?"**

| Ambiguity | Severity |
|-----------|----------|
| Pack version drift (v3.9.0 vs v3.79.0 in different docs) | High — blind AI will pick the wrong one |
| Supported languages not surfaced | High — silent no-op on unsupported repos |
| Codegen step's applicability to downstream repos | Medium — wasted CI time at worst |
| Custom-rule authoring path | Medium — extension story is unclear |
| `.gitignore` for SARIF output | Low — cosmetic but the AI will commit junk |

---

## 4. Recommended Patches (priority order)

| # | Target | Patch | Effort |
|---|--------|-------|--------|
| 1 | `linters-cicd/README.md` + `examples/other-repo-integration/README.md` | Resolve version drift — single source of truth (`linters-cicd/VERSION`) referenced from both | S |
| 2 | `linters-cicd/README.md` | Add "Supported languages today" matrix; have `run-all.sh` warn on zero matched files | S |
| 3 | `examples/other-repo-integration/README.md` | Add `.gitignore` instruction; add `renovate.json` template | S |
| 4 | `linters-cicd/checks/_template/` | Create rule-skeleton template with README; cover via `tests/pipeline/` | M |
| 5 | `examples/other-repo-integration/README.md` | Document codegen step as internal-only / opt-in | S |
| 6 | `tests/pipeline/README.md` | Document bash/python/jq requirements | S |
| 7 | `examples/other-repo-integration/README.md` | Per-platform SARIF rendering fidelity table | M |

---

## 5. Bottom Line

- **Today:** A blind AI can drop this linter pack into a fresh GitHub repo and have a working CI in **under 5 minutes**, with high confidence the build will pass-or-fail correctly on Go and TypeScript.
- **For GitLab / Azure / Jenkins:** Working examples exist; the only friction is the version-drift footgun (§ patch #1).
- **For non-Go/TS repos:** The AI will appear to integrate successfully but will lint nothing. Patch #2 closes this.
- **For long-term maintenance:** Add the Renovate config (patch #3) and the AI's integration becomes self-updating.
- **Score after patches:** projected **9.4 / 10** — competitive with the best off-the-shelf SARIF-emitting linter packs.