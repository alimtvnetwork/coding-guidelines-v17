# GitHub Repo Metadata (Manual Action Required)

**Version:** 1.0.0  
**Updated:** 2026-04-22

The repository's GitHub-side metadata (description, topics, social
preview) cannot be set from inside the repo — it must be configured by
a maintainer with `Settings` access. This file is the canonical
checklist so any maintainer can apply it in 60 seconds.

---

## §1 — Repository Description

**Where:** `https://github.com/alimtvnetwork/coding-guidelines-v15` →
gear icon next to "About" → **Description**.

**Set to (exact text):**

```
Production-grade coding standards with zero-nesting enforcement and AI-optimized spec architecture for Go, TypeScript, PHP, Rust, and C# — drop-in conventions for elite engineering teams.
```

(198 chars — fits the 350-char GitHub limit comfortably.)

---

## §2 — Website

**Where:** Same dialog → **Website** field.

**Set to:**

```
https://alimkarim.com/
```

---

## §3 — Topics (≤ 20 allowed; 12 recommended)

**Where:** Same dialog → **Topics** field.

**Add these topics, in this order** (lowercase, hyphenated):

```
coding-guidelines
coding-guidelines-v15
coding-standards
spec-driven-development
ai-friendly
ai-onboarding
error-handling
linters
golang
typescript
php
wordpress
rust
c-sharp
```

---

## §4 — Social Preview Image

**Where:** Repo → `Settings` → `Social preview` → **Edit**.

**Upload:** [`public/images/coding-guidelines-walkthrough-poster.png`](../public/images/coding-guidelines-walkthrough-poster.png)

(960×540 — meets GitHub's 1280×640 minimum after upscaling, or
regenerate at premium 1920×960 for sharper rendering.)

---

## §5 — Releases Settings

- **Where:** Repo → `Releases` → ⚙️ → check "Include all assets in
  source code archives".
- Tags MUST follow `v<MAJOR>.<MINOR>.<PATCH>` (e.g. `v3.59.0`) — the
  release pipeline parses this format.

---

## §6 — Branch Protection (recommended)

- **Where:** `Settings` → `Branches` → `main`.
- Enable: "Require a pull request before merging" (≥ 1 review).
- Enable: "Require status checks to pass before merging" → tick the
  cross-link checker + linter workflows.

---

## §7 — Verification

After applying §1–§4, the repo card on `https://github.com/alimtvnetwork`
SHOULD render with:

- Brand icon (set in `Settings` → `General` → `Display`)
- Description visible without truncation
- All 12 topics as pills
- Social preview image when shared on Twitter/LinkedIn/Slack

---

*GitHub repo metadata — applied by a maintainer with Settings access — 2026-04-22*