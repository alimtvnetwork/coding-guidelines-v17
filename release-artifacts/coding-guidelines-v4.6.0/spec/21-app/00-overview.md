# App

**Version:** 3.2.0  
**Updated:** 2026-04-16  
**AI Confidence:** Production-Ready  
**Ambiguity:** None

---

## Overview

App-specific specification content at the root spec level. This folder contains implementation specs, feature definitions, workflows, and architecture decisions that are specific to application-level work — as opposed to foundational, cross-cutting guidelines.

---

## Placement Rule

Any content that defines a specific application feature, workflow, or implementation detail belongs here. Foundational, reusable principles belong in the core fundamentals range (`01–20`).

---

## Contents

_No app-specific specs added yet. Add specs as numbered files within this folder._

---

## Cross-References

| Reference | Location |
|-----------|----------|
| App Issues | [../22-app-issues/00-overview.md](../22-app-issues/00-overview.md) |
| Spec Authoring Guide | [../01-spec-authoring-guide/00-overview.md](../01-spec-authoring-guide/00-overview.md) |

---

## Verification

_Auto-generated section — see `spec/21-app/97-acceptance-criteria.md` for the full criteria index._

### AC-APP-000: App-level conformance: Overview

**Given** Run the application's integration smoke suite.  
**When** Run the verification command shown below.  
**Then** Boot sequence completes; health endpoint returns 200; no unhandled promise rejections appear in the log.

**Verification command:**

```bash
npm run test
```

**Expected:** exit 0. Any non-zero exit is a hard fail and blocks merge.

_Verification section last updated: 2026-04-21_
