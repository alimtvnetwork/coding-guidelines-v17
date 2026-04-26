# Read Memory Prompt

**Version:** 1.0.0 (canonical, supersedes v3.2.0 reference-only stub)
**Updated:** 2026-04-23

---

> **Trigger:** Saying **"read memory"** in chat refers to this prompt.

> **Purpose:** Mandatory onboarding sequence for any AI assistant joining this project. Internalize all specifications, rules, and conventions before writing a single line of code.

> **Rule #0:** Follow every phase sequentially. Do not skip, summarize prematurely, or assume knowledge from training data. The specs are the single source of truth.

---

## Table of Contents

1. [Phase 1 — AI Context Layer](#phase-1--ai-context-layer)
2. [Phase 2 — Consolidated Guidelines](#phase-2--consolidated-guidelines)
3. [Phase 3 — Spec Authoring Rules](#phase-3--spec-authoring-rules)
4. [Phase 4 — Deep-Dive Source Specs](#phase-4--deep-dive-source-specs-task-driven)
5. [Anti-Hallucination Contract](#anti-hallucination-contract)
6. [Memory Update Protocol](#memory-update-protocol)
7. [Completion Confirmation](#completion-confirmation)
8. [CI/CD Issues — Lessons Learned](#cicd-issues--lessons-learned)

---

## Phase 1 — AI Context Layer

**Goal:** Load the project's identity, hard rules, and institutional memory into your working context.

### Step 1.1 — Read core files in EXACT order

| Order | File | What You Learn |
|-------|------|----------------|
| 1 | `.lovable/overview.md` | Project summary, tech stack, navigation map |
| 2 | `.lovable/strictly-avoid.md` | **Hard prohibitions** — violating ANY of these is a critical failure |
| 3 | `.lovable/user-preferences` | How the human expects you to communicate and behave |
| 4 | `.lovable/memory/index.md` | Index of all institutional knowledge files |
| 5 | `.lovable/plan.md` | Current active roadmap and priorities |
| 6 | `.lovable/suggestions.md` | Pending improvement ideas (not yet approved) |

### Step 1.2 — Read EVERY file referenced in `.lovable/memory/index.md`

- If the index lists 12 files, you read 12 files. No exceptions.
- If there are subfolders, traverse them recursively.
- If a file is missing or empty, note it — do not silently skip.

### Step 1.3 — Self-check (answer these internally before continuing)

- [ ] What are the project's **CODE RED** rules?
- [ ] What naming conventions are enforced (files, folders, DB columns, variables)?
- [ ] What is the error handling philosophy?
- [ ] What is the current plan and what tasks are in progress?
- [ ] What patterns/tools/approaches are **strictly forbidden**?

> ⛔ **DO NOT proceed to Phase 2 until every file above has been read and internalized.**

---

## Phase 2 — Consolidated Guidelines

**Goal:** Absorb the project's unified rulebook — the self-contained guideline documents under `spec/17-consolidated-guidelines/`.

> **Path note:** This project numbers its consolidated guidelines folder as `17-consolidated-guidelines/` (not `12-`). Always use the actual folder.

### Instructions

1. Navigate to `spec/17-consolidated-guidelines/`.
2. Read every numbered file (`01-*.md` through the highest-numbered file) in order.
3. Each file is self-contained. Treat each as a standalone policy document.

### After reading, confirm internally

- [ ] Total number of guideline files read.
- [ ] One-sentence summary of the key rule from each file.
- [ ] Any rules that contradict your default training (these are intentional — the spec wins).

> ⛔ **DO NOT proceed to Phase 3 until all guideline files have been read.**

---

## Phase 3 — Spec Authoring Rules

**Goal:** Understand how specifications themselves are structured.

### Instructions

1. Navigate to `spec/01-spec-authoring-guide/`.
2. Read all files in numeric order.

### After reading, confirm you understand

| Concept | Where It's Defined |
|---------|-------------------|
| File and folder naming conventions | Spec authoring guide |
| Required files in every spec folder (`00-overview.md`, `99-consistency-report.md`) | Spec authoring guide |
| The `.lovable/` folder structure and its purpose | `07-memory-folder-guide.md` |
| Linter infrastructure requirements | `10-mandatory-linter-infrastructure.md` |

> ⛔ **DO NOT begin any task until Phases 1–3 are complete.**

---

## Phase 4 — Deep-Dive Source Specs (Task-Driven)

**Goal:** Before performing any task, read the relevant source spec(s) so your work is compliant.

### Lookup Table

| If your task involves... | Read this spec folder |
|--------------------------|----------------------|
| Writing or reviewing code | `spec/02-coding-guidelines/` |
| Error handling | `spec/03-error-manage/` |
| Database schema or queries | `spec/04-database-conventions/` |
| SQLite or multi-database architecture | `spec/05-split-db-architecture/` |
| Configuration systems | `spec/06-seedable-config-architecture/` |
| UI theming, CSS variables, design tokens | `spec/07-design-system/` |
| Documentation viewer features | `spec/08-docs-viewer-ui/` |
| Code block rendering | `spec/09-code-block-system/` |
| PowerShell scripts | `spec/11-powershell-integration/` |
| CI/CD pipelines | `spec/12-cicd-pipeline-workflows/` |
| CLI self-update system | `spec/14-update/` |
| Distribution and runner | `spec/15-distribution-and-runner/` |
| WordPress plugins | `spec/18-wp-plugin-how-to/` |
| App-specific features | `spec/21-app/` |
| Known app bugs/issues | `spec/22-app-issues/` |
| App-specific database schema | `spec/23-app-db/` |
| App-specific UI and design system | `spec/24-app-ui-design-system/` |

### Reading order within each folder

1. `00-overview.md` — always first
2. All numbered files in order
3. `99-consistency-report.md` — always last (if present)

---

## Anti-Hallucination Contract

These rules are **absolute and non-negotiable**.

1. **Never Invent Rules** — If a spec does not mention a rule, that rule does not exist.
2. **Specs Override Training Data** — When pre-trained knowledge conflicts with a spec, the spec wins.
3. **Cite Your Sources** — Reference the specific file and section. Example: *Per `spec/02-coding-guidelines/03-naming.md` § "Database Columns": all column names use PascalCase.*
4. **Ask When Uncertain** — Do not guess, infer, or "use best judgment."
5. **Never Merge Conventions** — Do not blend project conventions with conventions from training.
6. **No Filler** — Never append boilerplate like "Let me know if you have questions!" or "Hope this helps!"

---

## Memory Update Protocol

```
New information discovered
│
├─ Institutional knowledge (pattern, convention, decision)?
│  └─ YES → Write to `.lovable/memory/<topic>/` and update `.lovable/memory/index.md`
│
├─ Something that must NEVER be done?
│  └─ YES → Add to `.lovable/strictly-avoid.md`
│
├─ Suggestion / improvement idea (not yet approved)?
│  └─ YES → Add to `.lovable/suggestions.md`
│
├─ CI/CD validator finding (CODE-RED-* / STYLE-*)?
│  └─ YES → Add `.lovable/cicd-issues/NN-short-description.md` + update `.lovable/cicd-index.md`
│
└─ None of the above → Do not persist it
```

### Critical Rules

- The memory folder is `.lovable/memory/` — **never** `.lovable/memories/` (no trailing `s`).
- When adding a new memory file, **always** update the index at `.lovable/memory/index.md`.
- When modifying an existing memory, preserve all other content — do not truncate or overwrite unrelated entries.
- Single-file convention: plans live in `plan.md`, suggestions in `suggestions.md`. Never create per-task folders under `.lovable/` (see `.lovable/memory/avoid/01-avoid-per-task-folders.md`).

---

## Completion Confirmation

After completing **Phases 1 through 3**, respond with exactly this format:

```
✅ Onboarding complete.
- Memory files read: [X]
- Consolidated guidelines read: [Y]
- Spec authoring files read: [Z]

I understand:
- CODE RED rules: [list the top 3–5]
- Naming conventions: [brief summary]
- Error handling approach: [one sentence]
- Active plan: [current milestone or focus]
- Strict avoidances: [top 3–5 forbidden patterns]

Ready for tasks.
```

Then **stop and wait** for instructions. Do not suggest next steps. Do not ask exploratory questions. Just wait.

---

## CI/CD Issues — Lessons Learned

Read every file in `.lovable/cicd-issues/` (sequence starts at `01-`) and internalize the "What NOT to repeat" sections. The index lives at `.lovable/cicd-index.md`.

| # | Issue | Rule(s) | Key takeaway |
|---|-------|---------|--------------|
| 01 | README boolean negatives + style | CODE-RED-023, STYLE-001/004 | Never write `!variable` in any example or production file. |
| 02 | InstallSection.tsx 337 lines | STYLE-005 | Split components by responsibility before crossing 300 lines. |
| 03 | fuzzyMatch.ts function length + negative guards | CODE-RED-004/012/023 | Never let a scoring/parsing function grow past 15 lines. |
| 04 | useSearchKeyboard.ts raw `!` | CODE-RED-023 | Never write `if (!fn())` — assign to a positively-named const first. |
| 05 | Markdown highlighter newline violations | STYLE-001/003/004 | Always run `linters-cicd/run-all.sh` before committing. |
| 06 | Version drift after `package.json` bump | version-drift | Run `npm run sync` in the same commit as the version bump. |
| 07 | Cross-spec link checker false-positives | missing-file | Link checker is **file-relative**, not repo-root-relative. |

---

*Read prompt — v1.0.0 — 2026-04-23 — Triggered by saying "read memory".*
