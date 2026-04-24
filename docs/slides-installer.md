# Slides Installer — Behavior &amp; Flags

> **Spec:** This document describes the `slides` bundle's installer.
> Both `slides-install.sh` and `slides-install.ps1` conform to
> **[spec/14-update/27-generic-installer-behavior.md](../spec/14-update/27-generic-installer-behavior.md)** —
> the cross-bundle contract for flags (`--no-discovery`, `--no-main-fallback`,
> `--offline` / `--use-local-archive`), the §7 startup banner (`mode:` / `source:`
> lines), and the §8 exit-code policy (0–5). The slides-specific extensions
> below (auto-open, main-branch fallback) layer on top of that contract.

The `slides` bundle is delivered by `slides-install.sh` (Linux/macOS) and `slides-install.ps1` (Windows). Both scripts share the same behavior, generated from `bundles.json` via `scripts/generate-bundle-installers.mjs`.

## What you get

The archive ships three top-level folders into the install target:

| Folder | Purpose |
|--------|---------|
| `slides-app/dist/` | **Pre-built** HTML+JS+CSS. Double-click `index.html` — no Node/Bun/npm install or build step required. |
| `slides-app/` | React/Vite source. Edit + rebuild only if you want to customize the deck. |
| `spec-slides/` | Markdown source decks consumed by the slides app. |

## Auto-open

After install completes, `slides-app/dist/index.html` opens in your default browser:

- **Windows** — `Start-Process` (PowerShell)
- **macOS** — `open`
- **Linux** — `xdg-open` (falls back to printing the path if unavailable)

Suppress with `-NoOpen` (PowerShell) or `--no-open` (Bash). The path is printed instead so you can open it manually.

## Main-branch tarball fallback

When `-Version` / `--version` is omitted, the installer fetches the live `main` branch zip/tarball directly from `codeload.github.com`. This means:

- No `git` binary required.
- No release-existence probe — works behind firewalls that block `api.github.com`.
- Always reflects the latest `main`.

If a pinned version is requested but its release archive is missing (404), the installer warns and falls back to the `main` branch automatically.

## Offline mode

Pass `-Offline` (PowerShell) or `--offline` (Bash) to refuse all network downloads. The script:

1. Prints a `Net: OFFLINE` banner.
2. Exits with code `2` and prints the URL it would have fetched.

Use this in air-gapped CI or when you want to pre-stage the archive locally and confirm the installer never reaches out.

## Examples

### PowerShell (Windows)

```powershell
# default: main branch, auto-open
irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.ps1 | iex

# pinned version, do not auto-open
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.ps1))) -Version v3.66.0 -NoOpen

# offline — fails fast if download required
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.ps1))) -Offline
```

### Bash (Linux/macOS)

```bash
# default: main branch, auto-open
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.sh | bash

# pinned version, do not auto-open
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.sh | bash -s -- --version v3.66.0 --no-open

# offline — fails fast if download required
curl -fsSL https://raw.githubusercontent.com/alimtvnetwork/coding-guidelines-v15/main/slides-install.sh | bash -s -- --offline
```

## Exit codes

The installer uses a small, stable set of exit codes so you can branch on them in CI scripts.

| Code | Name                  | Meaning                                                                 | Recoverable? |
|------|-----------------------|-------------------------------------------------------------------------|--------------|
| `0`  | Success               | Archive downloaded, extracted, **all verify probes passed**, auto-open attempted. | n/a          |
| `1`  | Generic failure       | Unknown CLI flag, missing `curl`/`wget`, main-branch tarball download failed, or unhandled error. | Usually     |
| `2`  | Offline blocked       | `--offline` / `-Offline` set but a network download was required.       | Yes — re-run without offline, or pre-stage the archive. |
| `3`  | Verification failed   | Archive extracted but one or more required paths (e.g. `slides-app/dist/index.html`, `spec-slides/`) are missing on disk. | Yes — see §Verification failures below. |

> Auto-open failures (missing `xdg-open`, `start`, `open`) **do not** change the exit code. The install is still considered successful (`0`) because the artifacts are on disk; only the browser launch was skipped. The script always prints the exact entry path so you can open it manually.

## Troubleshooting by failure scenario

### 1. Offline blocked (exit `2`)

**Symptom**

```
❌ --offline set but main-branch tarball is required.
   URL: https://codeload.github.com/alimtvnetwork/coding-guidelines-v15/tar.gz/refs/heads/main
   Re-run without --offline (network access needed to fetch the bundle).
```

**Cause** — You passed `--offline` / `-Offline` but the script has no archive cached locally.

**Fixes**

- Re-run **without** `--offline` to allow the download.
- Or pre-stage the archive yourself and skip the installer:
  ```bash
  curl -fsSL "https://codeload.github.com/alimtvnetwork/coding-guidelines-v15/tar.gz/refs/heads/main" -o repo.tar.gz
  tar -xzf repo.tar.gz --strip-components=1 -C ./vendor "coding-guidelines-v15-main/slides-app" "coding-guidelines-v15-main/spec-slides"
  ```
- For pinned-version offline installs, mirror the release archive to your internal artifact store and host it behind a URL the installer can reach.

### 2. Missing release archive (exit `1` or fallback to main)

**Symptom**

```
⚠️  release archive not found for v3.66.0 — falling back to main branch
```

or, if `--offline`:

```
❌ --offline set but versioned archive requires network download.
```

**Cause** — `--version vX.Y.Z` was passed but `https://github.com/.../releases/download/vX.Y.Z/slides.tar.gz` returned 404 (release was never cut, archive failed to upload, or the version string is wrong).

**Fixes**

- Let the script fall back to `main` (default behavior) — usually the warning is enough.
- Run **without** `--version` to use the live `main` branch unconditionally.
- Confirm the version exists: `https://github.com/alimtvnetwork/coding-guidelines-v15/releases`.
- If you need that exact version, re-run the release workflow that builds and uploads `slides.tar.gz`.

### 3. Network / download failure (exit `1`)

**Symptoms**

```
❌ Neither curl nor wget found. Install one and retry.
```

```
❌ failed to download main-branch tarball from https://codeload.github.com/...
```

**Causes & fixes**

| Cause                              | Fix                                                                  |
|------------------------------------|----------------------------------------------------------------------|
| No `curl` or `wget` on PATH (Bash) | `sudo apt-get install curl` / `sudo dnf install curl` / `brew install curl` |
| Corporate proxy blocks `codeload.github.com` | Set `HTTPS_PROXY` env var, or pre-stage the archive (see §1).        |
| Firewall blocks all of GitHub      | Mirror the tarball internally and edit the `archive_url` in your fork. |
| TLS/cert error                     | Update CA bundles (`update-ca-certificates`); avoid `-k` / `--insecure`. |
| PowerShell `Invoke-WebRequest` SSL error | Run `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12` once before re-running. |

### 4. Extraction failure (exit `1`)

**Symptoms** — `tar: …: Cannot open: No such file or directory`, `Expand-Archive : The archive entry was found to be corrupt`, or partial extraction warnings.

**Causes & fixes**

- **Truncated download** — re-run; the script writes to a fresh `mktemp` directory each time.
- **Out of disk in `$TMPDIR`** — `df -h /tmp` (Linux/macOS) or `Get-PSDrive` (Windows). Free space and retry.
- **Permissions** — installer needs write access to both `$TMPDIR` and `--target` / `-Target`. Avoid running into a directory you do not own.
- **`tar` missing on Windows Bash shells** — install Git Bash or use `slides-install.ps1` instead.

### 5. Verification failed (exit `3`)

**Symptom**

```
❌ Install verification FAILED — 2 required path(s) missing:
     • file: /home/me/vendor/slides-app/dist/index.html
     • dir : /home/me/vendor/spec-slides

   The archive was downloaded and extracted but did NOT contain
   the expected artifacts.
```

**Cause** — Extraction succeeded but one or more probes from `bundles.json` `verify[]` are missing on disk after the copy.

**Most common root causes**

1. **Pinned `--version` predates the prebuilt artifact.** Older releases shipped source-only. **Fix:** re-run **without** `--version` to fetch the `main` branch tarball, which always includes `slides-app/dist/`.
2. **Release workflow build step failed silently.** The `.tar.gz` was uploaded without `slides-app/dist/` inside it. **Fix:** check the GitHub Actions release log for the `slides` bundle build step; re-run it; bump the version.
3. **Partial overwrite.** A previous run with a different `--target` left stale folders that hid the new copy. **Fix:** delete the install target and re-run cleanly:
   ```bash
   rm -rf ./vendor && curl -fsSL .../slides-install.sh | bash -s -- --target ./vendor
   ```
4. **`cp` permission denied during extraction.** Look earlier in the output for `Permission denied` lines. **Fix:** install to a directory you own, or `sudo` the entire installer (rare and not recommended).

### 6. Auto-open failure (exit code unchanged — still `0`)

The installer **never** fails the install because the browser could not launch. It does, however, print actionable diagnostics.

**Symptom — Linux**

```
❌ 'xdg-open' not installed — cannot auto-launch browser.
   Install with one of:
     Debian/Ubuntu : sudo apt-get install xdg-utils
     Fedora/RHEL   : sudo dnf install xdg-utils
     Arch          : sudo pacman -S xdg-utils
   Or open the path above manually in your browser.
```

**Symptom — macOS** (extremely rare)

```
❌ 'open' command not found on macOS (this is unexpected).
```

**Symptom — Windows / WSL / Git Bash**

```
❌ 'start' command not found in this shell.
```

**Fixes**

- Copy the printed `file://...` URL into your browser address bar.
- Linux: install `xdg-utils` (commands above).
- WSL: launch from PowerShell or use `explorer.exe slides-app/dist/index.html`.
- CI / headless: pass `--no-open` / `-NoOpen` to suppress the auto-open attempt entirely.
- Locked-down browsers / RDP sessions that swallow `Start-Process`: open the printed path manually — the script always shows it before attempting to launch.

### 7. Unknown flag (exit `1`)

**Symptom** — `❌ Unknown option: --foo`

**Fix** — Run `bash slides-install.sh --help` (or read the header of the `.ps1` file) for the supported flags: `--version`, `--target`, `--no-open`, `--offline`.

## Quick reference — exit-code branching in CI

```bash
set +e
curl -fsSL "$URL" | bash -s -- --target ./vendor --no-open
code=$?
set -e

case "$code" in
  0) echo "✅ slides installed at ./vendor" ;;
  2) echo "ℹ️  offline mode blocked download — using cached copy"; restore_cached_vendor ;;
  3) echo "❌ verification failed — refusing to publish"; exit 1 ;;
  *) echo "❌ installer failed with code $code"; exit "$code" ;;
esac
```

```powershell
$ErrorActionPreference = 'Continue'
& ([scriptblock]::Create((irm $url))) -Target .\vendor -NoOpen
switch ($LASTEXITCODE) {
  0 { Write-Host "✅ slides installed" }
  2 { Write-Host "ℹ️  offline mode blocked download" }
  3 { Write-Error "❌ verification failed — refusing to publish"; exit 1 }
  default { Write-Error "❌ installer failed with code $LASTEXITCODE"; exit $LASTEXITCODE }
}
```

## GitHub Actions — full workflow snippet

Drop-in workflow that runs the installer, branches on the documented exit
codes, and **fails the build** when verification (`exit 3`) reports missing
artifacts. Offline blocks (`exit 2`) are surfaced as a warning so cached
vendor directories can take over without aborting the run.

```yaml
# .github/workflows/install-slides.yml
name: Install slides bundle

on:
  pull_request:
  push:
    branches: [main]

jobs:
  install:
    runs-on: ubuntu-latest
    env:
      SLIDES_INSTALLER_URL: https://github.com/alimtvnetwork/coding-guidelines-v15/releases/latest/download/slides-install.sh
      SLIDES_TARGET: ./vendor/slides
    steps:
      - uses: actions/checkout@v4

      - name: Run slides installer
        id: install
        shell: bash
        run: |
          set +e
          curl -fsSL "$SLIDES_INSTALLER_URL" | bash -s -- \
            --target "$SLIDES_TARGET" \
            --no-open
          code=$?
          set -e
          echo "code=$code" >> "$GITHUB_OUTPUT"
          case "$code" in
            0)
              echo "::notice title=Slides installed::Artifacts ready at $SLIDES_TARGET"
              ;;
            2)
              echo "::warning title=Offline mode::Installer refused to download (exit 2). Falling back to cached vendor."
              ;;
            3)
              echo "::error title=Verification failed::Required paths missing after extraction (exit 3)."
              exit 1
              ;;
            *)
              echo "::error title=Installer failed::Unexpected exit code $code"
              exit "$code"
              ;;
          esac

      - name: Upload installed bundle
        if: steps.install.outputs.code == '0'
        uses: actions/upload-artifact@v4
        with:
          name: slides-bundle
          path: ${{ env.SLIDES_TARGET }}
          if-no-files-found: error
```

### Exit-code policy at a glance

| Exit | Job result   | Reason                                            |
|------|--------------|---------------------------------------------------|
| `0`  | ✅ success    | Archive extracted **and** verification passed     |
| `2`  | ⚠️ warning   | `--offline` blocked a required download           |
| `3`  | ❌ **fail**  | Verification missed `slides-app/dist/index.html` or `spec-slides` |
| any other | ❌ fail | Network, extraction, or unknown-flag failure      |

> Verification failures (`3`) are always treated as a hard build break — the
> installer reported success up to extraction, but the artifacts your
> downstream steps depend on are not on disk. Do not downgrade this to a
> warning.