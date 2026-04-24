# GitLab CI — Step-by-Step Wiring

> **Estimated time:** 5 minutes
> **Result:** Findings render in the MR widget under "Code Quality" and
> "Security & Compliance → Vulnerability Report".

---

## Step 1 — Drop the file in your repo

Copy [`.gitlab-ci.yml`](./.gitlab-ci.yml) to the **root** of the target
repo. If your repo already has a `.gitlab-ci.yml`, copy only the
`coding-guidelines` job and the `stages:` entry into it.

```bash
cp examples/other-repo-integration/gitlab/.gitlab-ci.yml /path/to/your-repo/
```

## Step 2 — Verify the required files exist on the runner

The job installs everything itself; the runner only needs:

| Tool | Why | Provided by |
|------|-----|-------------|
| `curl` | Download `install.sh` | `python:3.11-slim` image |
| `unzip` | Extract release ZIP | `apt-get` line in `before_script` |
| `python3` | Run the checks + SARIF merger | base image |
| `bash` | Run `run-all.sh` | base image |

**No pre-installed plugins are required.**

## Step 3 — (Optional) Convert SARIF to GitLab Code Quality

GitLab's MR widget natively understands the `sast:` report type used in
the template. If you also want the **Code Quality** widget, add a second
artifact using the bundled converter:

```yaml
    - python3 ./linters-cicd/scripts/sarif-to-codequality.py \
        coding-guidelines.sarif > gl-code-quality-report.json
  artifacts:
    reports:
      sast: coding-guidelines.sarif
      codequality: gl-code-quality-report.json
```

## Step 4 — Commit, push, open an MR

You should see, on the MR page:

1. **Pipeline tab** — green/red `coding-guidelines` job.
2. **Security widget** — list of findings with `CODE-RED-NNN` rule IDs.
3. **Job artifacts** — `coding-guidelines.sarif` downloadable for 30 days.

## Step 5 — Pin a version (production)

Replace the `install.sh` line with a tagged URL:

```yaml
    - curl -fsSL https://github.com/alimtvnetwork/coding-guidelines-v15/releases/download/v3.79.0/install.sh | bash
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `bash: linters-cicd/run-all.sh: No such file or directory` | `install.sh` failed — check the runner has outbound `https://github.com` access. |
| `python3: not found` | Switch image to `python:3.11-slim` (template default). |
| Findings job is green but MR widget is empty | The `reports.sast:` key requires GitLab ≥ 13.10. Older instances: download the artifact instead. |
| Want it to **not** block merge | Add `allow_failure: true` to the job. |