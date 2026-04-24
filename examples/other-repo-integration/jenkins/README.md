# Jenkins — Step-by-Step Wiring

> **Estimated time:** 10 minutes
> **Result:** Findings render in the **Warnings Next Generation** plugin
> dashboard with trend charts and per-build deltas.

---

## Step 1 — Install required Jenkins plugins (one-time, admin)

| Plugin | Purpose | Required? |
|--------|---------|-----------|
| **Docker Pipeline** | Run job in a `python:3.11-slim` container | ✅ Yes |
| **Warnings Next Generation** | Render SARIF in the UI | ✅ Yes |
| **Pipeline: Stage View** | Stage timing visualization | Optional |

Install via **Manage Jenkins → Plugins → Available**.

## Step 2 — Drop the file in your repo

Copy [`Jenkinsfile`](./Jenkinsfile) to the **root** of the target repo.

```bash
cp examples/other-repo-integration/jenkins/Jenkinsfile /path/to/your-repo/
```

## Step 3 — Create the Jenkins job

1. **New Item** → **Multibranch Pipeline** (recommended) or **Pipeline**
2. **Branch Sources** → add your Git repo
3. **Build Configuration** → Mode: `by Jenkinsfile`, Script Path: `Jenkinsfile`
4. **Save** → Jenkins discovers branches and runs the pipeline.

## Step 4 — Verify required files & agent capabilities

| Requirement | Why |
|-------------|-----|
| Agent with Docker available | Pipeline uses `agent { docker { ... } }` |
| Outbound HTTPS to `github.com` | Download release ZIP |
| `archiveArtifacts` permission | Surface SARIF for download |

If your agents do **not** have Docker, swap the agent block:

```groovy
agent any
stages {
    stage('Setup Python') {
        steps { sh 'python3 --version || sudo apt-get install -y python3' }
    }
    // ... rest unchanged
}
```

## Step 5 — First run checklist

After the first build, confirm:

1. **Console Output** → install + run-all both succeed.
2. **Build artifacts** → `coding-guidelines.sarif` listed and downloadable.
3. **Sidebar** → **Coding Guidelines** entry (added by Warnings-NG)
   shows the findings table with `CODE-RED-NNN` rule IDs.

## Step 6 — Pin a version (production)

Edit the install line in `Jenkinsfile`:

```groovy
sh 'curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v17/releases/download/v3.79.0/install.sh | bash'
```

## Step 7 — Quality gates (optional but recommended)

The `recordIssues` step in the template fails the build on any **new**
finding compared to the reference build. Tune the thresholds:

```groovy
recordIssues(
    tools: [sarif(pattern: 'coding-guidelines.sarif', id: 'coding-guidelines')],
    qualityGates: [
        [threshold: 1, type: 'NEW', unstable: false],   // any new = FAILED
        [threshold: 1, type: 'TOTAL_ERROR', unstable: false]  // any CODE RED = FAILED
    ]
)
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `docker: not found` on agent | Install Docker on the agent **or** switch to the `agent any` variant in Step 4. |
| Sidebar entry missing | Warnings-NG plugin not installed (see Step 1). |
| SARIF parsed but no findings shown | Confirm `tools: [sarif(...)]` (not `checkstyle` / `pmd`). |
| Build green but findings present | Quality gate threshold too high — see Step 7. |
| `Permission denied` on `run-all.sh` | The release ZIP preserves perms; ensure `unzip` (not custom extractor) was used. |