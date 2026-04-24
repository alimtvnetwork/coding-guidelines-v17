# Azure DevOps Pipelines — Step-by-Step Wiring

> **Estimated time:** 7 minutes
> **Result:** Findings render under the **SARIF SAST Scans Tab**
> extension on each pipeline run.

---

## Step 1 — Install the SARIF SAST extension (one-time, org admin)

Azure DevOps does not natively render SARIF. Install Microsoft's free
extension once per organization:

1. Open: <https://marketplace.visualstudio.com/items?itemName=sariftools.scans>
2. Click **Get it free** → choose your organization → **Install**.

Without this extension, the SARIF file still uploads as a build artifact
(downloadable) but no inline rendering happens.

## Step 2 — Drop the file in your repo

Copy [`azure-pipelines.yml`](./azure-pipelines.yml) to the **root** of
the target repo.

```bash
cp examples/other-repo-integration/azure-devops/azure-pipelines.yml /path/to/your-repo/
```

## Step 3 — Create the pipeline in Azure DevOps

1. Azure DevOps → **Pipelines** → **New pipeline**
2. Pick your repo → **Existing Azure Pipelines YAML file**
3. Path: `/azure-pipelines.yml` → **Continue** → **Run**

## Step 4 — Verify required files & permissions

| Requirement | Why | Notes |
|-------------|-----|-------|
| `ubuntu-latest` agent | Bash + Python pre-installed | Default in template |
| Outbound HTTPS to `github.com` | Download release ZIP | Required |
| Build artifacts enabled | Surface SARIF for the extension | On by default |

No service connections or secrets are required — the install is a public
download.

## Step 5 — First run checklist

After the first pipeline run, confirm:

1. **Logs tab** → step `Run coding-guidelines checks` exits 0 (clean) or 1 (findings).
2. **Artifacts** → `coding-guidelines-sarif/coding-guidelines.sarif` is downloadable.
3. **Scans tab** (added by the extension) → table of findings with rule IDs.

## Step 6 — Pin a version (production)

Replace the install line:

```yaml
    curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v17/releases/download/v3.79.0/install.sh | bash
```

## Step 7 — Branch protection (optional)

To **block PR merges** on findings:

1. Repo → **Branches** → **…** on `main` → **Branch policies**
2. **Build validation** → **+** → pick the pipeline → **Save**.

The job's non-zero exit code on CODE RED findings will now block merge.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Scans tab missing | Extension not installed (see Step 1). |
| `Permission denied` on `run-all.sh` | Ensure the YAML uses `bash` task, not `script:`. Template uses `bash`. |
| Pipeline always green even with findings | Confirm `continueOnError: false` (template default). |
| `python3: command not found` | Switch agent to `ubuntu-latest` or add `UsePythonVersion@0`. |