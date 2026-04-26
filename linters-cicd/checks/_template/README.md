# `_template/` — Custom Rule Starter Kit

> **Audience:** an autonomous AI agent (or human) adding a new linter
> rule in a single iteration, with no prior tribal knowledge.
>
> **Status:** This folder is a **template only**. It is intentionally
> NOT registered in `checks/registry.json` and the orchestrator
> (`run-all.sh`) skips it. Copy it, rename it, then register.

This kit contains a **complete, working rule** (`TEMPLATE-001` — flag
leftover `var_dump()` / `print_r()` / `error_log()` debug calls in
PHP) plus its fixtures and unit tests. Every file is the minimum
viable shape for a real production rule. Copy → rename → adapt.

---

## What you get

| File | Purpose | When you copy, rename to… |
|---|---|---|
| `php.py` | The check itself — CLI entry, regex/AST scan, SARIF emit | `<your-slug>/php.py` (or `typescript.py`, `go.py`, etc.) |
| `fixtures/dirty.php` | Source that MUST trigger findings | `fixtures/dirty.<ext>` |
| `fixtures/clean.php` | Source that MUST stay silent | `fixtures/clean.<ext>` |
| `test_template.py` | Unit + end-to-end test — locks the contract | move to `linters-cicd/tests/test_<your_rule>.py` |
| `README.md` | This file | leave behind in `_template/`; do NOT copy |

---

## The 7-step checklist (do not skip a step)

A blind AI that follows these in order will land a working,
CI-blocking rule in one PR. Every step has a deterministic
verification signal — if you don't see it, stop.

### 1. Pick a rule ID and slug

Format: `<DOMAIN>-<TOPIC>-<NNN>` (e.g. `WP-NONCE-001`,
`SQLI-RAW-001`, `STYLE-099`). Slug is the kebab-case folder name
(e.g. `wp-nonce-verification`). Both must be unique across
`checks/registry.json`.

```bash
grep -E '"[A-Z]+-[A-Z0-9-]+":' linters-cicd/checks/registry.json
```

### 2. Copy the template

```bash
cp -r linters-cicd/checks/_template linters-cicd/checks/<your-slug>
rm linters-cicd/checks/<your-slug>/README.md
mv linters-cicd/checks/<your-slug>/test_template.py \
   linters-cicd/tests/test_<your_rule>.py
```

### 3. Edit `php.py` (or rename to your target language)

Change exactly **five** things — leave the boilerplate alone:

1. The module docstring (1 sentence + spec link).
2. `RULE.id`, `RULE.name`, `RULE.short_description`,
   `RULE.help_uri_relative`.
3. `DEBUG_CALL_RE` → your detection pattern. Strict by default;
   broaden only with a fixture that proves the expansion.
4. The `Finding(...)` `level` (`"error"` for must-block,
   `"warning"` for advisory) and `message` text.
5. `walk_files(args.path, [<your extensions>], ...)` and the
   `tool_name` string in `SarifRun(...)`.

**Do NOT touch:** the `sys.path.insert` block, the `build_parser`
call, the `parse_exclude_paths` call, the `emit()` return, the
`if __name__ == "__main__"` guard.

### 4. Replace the fixtures

`fixtures/dirty.<ext>` — minimum source that triggers ≥ 1 finding
per code path your regex/visitor handles. Add inline comments
pointing at expected line numbers.

`fixtures/clean.<ext>` — adjacent legitimate code that MUST NOT
trigger. Include the most plausible false-positive shapes you can
think of (calls inside comments, calls inside string literals,
calls on similarly-named functions).

### 5. Update the test file

Open `linters-cicd/tests/test_<your_rule>.py` and change:

- `TEMPLATE_DIR = ROOT / "checks" / "_template"` →
  `RULE_DIR = ROOT / "checks" / "<your-slug>"`
- the expected finding count in
  `test_dirty_fixture_produces_three_findings` to your fixture's
  actual count
- the expected `rule_id` and `level` sets

### 6. Register the rule

Add an entry to `linters-cicd/checks/registry.json`. Keep the
existing alphabetic-by-ID order:

```json
"YOUR-RULE-001": {
  "name": "YourRuleNameInPascalCase",
  "level": "warning",
  "spec": "<spec-section-relative-to-spec-root>.md",
  "languages": {
    "php": "checks/<your-slug>/php.py"
  }
}
```

If your rule covers multiple languages, add one `php.py` /
`typescript.py` / `go.py` sibling per language and list each
under `languages`.

### 7. Verify everything (mandatory, in order)

```bash
# 7a. Unit tests must all pass
python3 linters-cicd/tests/run.py

# 7b. The orchestrator must dispatch your rule
bash linters-cicd/run-all.sh \
  --path linters-cicd/checks/<your-slug>/fixtures \
  --rules YOUR-RULE-001 \
  --format text \
  --output /tmp/your-rule.txt
cat /tmp/your-rule.txt
# Expected: exit code 1, your rule id appears, dirty.<ext> is
# flagged, clean.<ext> is silent.

# 7c. SARIF must validate
bash linters-cicd/run-all.sh \
  --path linters-cicd/checks/<your-slug>/fixtures \
  --rules YOUR-RULE-001 \
  --format sarif \
  --output /tmp/your-rule.sarif
python3 linters-cicd/scripts/validate-sarif.py /tmp/your-rule.sarif
# Expected: exit code 0, "OK SARIF 2.1.0".

# 7d. Cross-link checker stays green (proves help_uri_relative
# points at a real spec section)
python3 linter-scripts/check-spec-cross-links.py \
  --root spec --repo-root .
# Expected: "OK All internal spec cross-references resolve."
```

If any of 7a–7d fails, **fix the new rule** — do not weaken an
existing test, do not edit `_lib/`, do not touch other checks.

---

## What the template intentionally does NOT show

These are deliberate omissions. Reach for them only when your
rule actually needs them, and copy from a sibling rule that
already uses the pattern:

| Need | Look at |
|---|---|
| AST parsing (instead of regex) | `checks/nested-if/typescript.py` |
| Multi-line span scanning with paren matching | `checks/sqli-raw-execute/_shared.py` |
| Allow-list lookups | `checks/boolean-naming/_lib usage` |
| Inline suppression handling | `checks/_lib/suppressions.py` |
| Universal (any-language) scan | `checks/file-length/universal.py` |
| Per-file timeout on slow scans | `checks/_lib/per_file_timeout.py` |
| Markdown link parsing | `checks/_lib/markdown_links.py` |
| SQL grammar specifics | `checks/free-text-columns/sql.py` |

---

## Anti-patterns the AI MUST avoid

- ❌ Editing `_lib/` to make your rule work. Add a helper to
  `checks/<your-slug>/_shared.py` instead.
- ❌ Importing from another check's directory. Each check is
  self-contained; share via `_lib/` only.
- ❌ Marking findings `level="error"` to "make sure people see
  them". Errors block merges — reserve for genuine
  must-fix violations.
- ❌ Skipping `strip_comments()` (or its language equivalent).
  False positives inside comments destroy linter trust faster
  than missed findings.
- ❌ Writing a fixture that depends on an external file, network
  call, or environment variable. Fixtures are committed,
  hermetic source files only.
- ❌ Pointing `help_uri_relative` at a spec section that doesn't
  exist yet. Either create the spec section first or pick the
  closest existing one — the cross-link checker (step 7d) will
  catch broken pointers.
- ❌ Leaving `_template/` in `registry.json`. The orchestrator
  intentionally skips it; never wire it up.

---

## Definition of done

The new rule is done when, and only when, all of these hold:

- [ ] New folder `checks/<your-slug>/` contains `php.py` (or the
      target-language file), `fixtures/dirty.<ext>`,
      `fixtures/clean.<ext>`.
- [ ] `linters-cicd/tests/test_<your_rule>.py` exists and passes.
- [ ] `checks/registry.json` lists the new rule ID.
- [ ] `python3 linters-cicd/tests/run.py` exit code 0.
- [ ] `bash linters-cicd/run-all.sh --rules <YOUR-RULE-ID> ...`
      exits 1 against `dirty.<ext>` and 0 against `clean.<ext>`.
- [ ] `validate-sarif.py` reports OK on the produced SARIF.
- [ ] `check-spec-cross-links.py` reports OK.
- [ ] No file under `_lib/`, no other rule's folder, and no test
      outside `tests/test_<your_rule>.py` was modified.
