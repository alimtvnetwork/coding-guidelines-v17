#!/usr/bin/env node
// =====================================================================
// scripts/spec-change-report.mjs
//
// Run the two spec validators (validate-guidelines.py and
// check-spec-cross-links.py), parse their output, scope the findings to
// the spec files the author actually touched, and emit a concise HTML
// report (and, when wkhtmltopdf / Chromium is available, a PDF too).
//
// Usage:
//   node scripts/spec-change-report.mjs                # only changed files
//   node scripts/spec-change-report.mjs --all          # full repo
//   node scripts/spec-change-report.mjs --out <dir>    # custom out dir
//
// Exit codes:
//   0  no findings in scope
//   1  findings present (CI-friendly)
//   2  validator crashed
//
// Documented in: docs/spec-author-dx.md (Wave 2 add-on)
// =====================================================================

import { execSync, spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync, copyFileSync, renameSync, unlinkSync } from "node:fs";
import { resolve, relative, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const ARGS = new Set(process.argv.slice(2));
const OUT_DIR_FLAG_INDEX = process.argv.indexOf("--out");
const OUT_DIR =
  OUT_DIR_FLAG_INDEX !== -1 && process.argv[OUT_DIR_FLAG_INDEX + 1]
    ? resolve(process.argv[OUT_DIR_FLAG_INDEX + 1])
    : "/mnt/documents";
const SCOPE_ALL = ARGS.has("--all");

// ---------------------------------------------------------------------
// 1. Determine which spec files changed
// ---------------------------------------------------------------------
function listChangedSpecFiles() {
  if (SCOPE_ALL) return null; // null == no scoping
  try {
    const staged = execSync("git diff --cached --name-only --diff-filter=ACMR", {
      cwd: REPO_ROOT,
      encoding: "utf8",
    });
    const unstaged = execSync("git diff --name-only --diff-filter=ACMR", {
      cwd: REPO_ROOT,
      encoding: "utf8",
    });
    const untracked = execSync("git ls-files --others --exclude-standard", {
      cwd: REPO_ROOT,
      encoding: "utf8",
    });
    const set = new Set(
      [staged, unstaged, untracked]
        .join("\n")
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.startsWith("spec/") && s.endsWith(".md"))
    );
    return set;
  } catch (err) {
    console.warn(`[spec-change-report] git diff failed: ${err.message}`);
    return new Set();
  }
}

// ---------------------------------------------------------------------
// 2. Run validators
// ---------------------------------------------------------------------
function runValidator() {
  const r = spawnSync(
    "python3",
    ["linter-scripts/validate-guidelines.py"],
    { cwd: REPO_ROOT, encoding: "utf8" }
  );
  return { stdout: r.stdout || "", stderr: r.stderr || "", status: r.status ?? 0 };
}

function runCrossLinkChecker() {
  const r = spawnSync(
    "python3",
    ["linter-scripts/check-spec-cross-links.py", "--root", "spec", "--repo-root", "."],
    { cwd: REPO_ROOT, encoding: "utf8" }
  );
  return { stdout: r.stdout || "", stderr: r.stderr || "", status: r.status ?? 0 };
}

// ---------------------------------------------------------------------
// 3. Parse validator output
// ---------------------------------------------------------------------
// Each "📄 <path> (N violations)" block is followed by lines like
//   "  🔴 L10    [CODE-RED-004] message"
//   "  ⚠️  L48   [STYLE-003] message"
function parseValidator(stdout) {
  const findings = [];
  let currentFile = null;
  for (const line of stdout.split("\n")) {
    const fileMatch = line.match(/^📄\s+(\S+)\s+\((\d+)\s+violations?\)/);
    if (fileMatch) {
      currentFile = fileMatch[1];
      continue;
    }
    const violation = line.match(
      /^\s+(🔴|⚠️)\s+L(\d+)\s+\[([A-Z0-9-]+)\]\s+(.*)$/
    );
    if (violation && currentFile) {
      findings.push({
        file: currentFile,
        line: Number(violation[2]),
        severity: violation[1] === "🔴" ? "code-red" : "style",
        rule: violation[3],
        message: violation[4].trim(),
      });
    }
  }
  return findings;
}

// "  [missing-file] spec/_template.md:71"
// "    text:   ..."  "    target: ..."  "    detail: ..."
function parseCrossLink(stdout) {
  const findings = [];
  const lines = stdout.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const head = lines[i].match(/^\s+\[([a-z-]+)\]\s+(\S+):(\d+)\s*$/);
    if (!head) continue;
    const [kind, file, line] = [head[1], head[2], Number(head[3])];
    const detailLines = [];
    for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
      const m = lines[j].match(/^\s+(text|target|detail):\s+(.*)$/);
      if (m) detailLines.push(`${m[1]}: ${m[2]}`);
    }
    findings.push({
      file,
      line,
      kind,
      detail: detailLines.join(" · "),
    });
  }
  return findings;
}

// ---------------------------------------------------------------------
// 4. Scope to changed files
// ---------------------------------------------------------------------
function scopeToFiles(findings, scope) {
  if (!scope) return findings;
  return findings.filter((f) => scope.has(f.file));
}

// ---------------------------------------------------------------------
// 5. Render HTML
// ---------------------------------------------------------------------
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function groupBy(arr, keyFn) {
  const m = new Map();
  for (const item of arr) {
    const k = keyFn(item);
    if (!m.has(k)) m.set(k, []);
    m.get(k).push(item);
  }
  return m;
}

function buildHtml({ scope, validator, crossLink, validatorRaw, crossLinkRaw, generatedAt }) {
  const scopeLabel = scope ? `${scope.size} changed spec file(s)` : "entire repo";
  const totalCodeRed = validator.filter((f) => f.severity === "code-red").length;
  const totalStyle = validator.filter((f) => f.severity === "style").length;
  const totalLink = crossLink.length;
  const grandTotal = totalCodeRed + totalStyle + totalLink;
  const status = grandTotal === 0 ? "✅ Clean" : "❌ Findings present";
  const statusClass = grandTotal === 0 ? "ok" : "fail";

  const validatorByFile = groupBy(validator, (f) => f.file);
  const linkByFile = groupBy(crossLink, (f) => f.file);
  const allFiles = new Set([...validatorByFile.keys(), ...linkByFile.keys()]);

  const fileSections = [...allFiles]
    .sort()
    .map((file) => {
      const v = validatorByFile.get(file) || [];
      const l = linkByFile.get(file) || [];
      const rows = [
        ...v.map(
          (f) => `
          <tr class="sev-${f.severity}">
            <td class="num">L${f.line}</td>
            <td class="rule"><code>${escapeHtml(f.rule)}</code></td>
            <td class="kind">${f.severity === "code-red" ? "<span class='dot dot-red'></span> Code Red" : "<span class='dot dot-amber'></span> Style"}</td>
            <td class="msg">${escapeHtml(f.message)}</td>
          </tr>`
        ),
        ...l.map(
          (f) => `
          <tr class="sev-link">
            <td class="num">L${f.line}</td>
            <td class="rule"><code>${escapeHtml(f.kind)}</code></td>
            <td class="kind"><span class='dot dot-blue'></span> Link</td>
            <td class="msg">${escapeHtml(f.detail)}</td>
          </tr>`
        ),
      ].join("");
      return `
        <section class="file-block">
          <h3>${escapeHtml(file)} <span class="count">(${v.length + l.length})</span></h3>
          <table>
            <thead><tr><th>Line</th><th>Rule</th><th>Kind</th><th>Detail</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </section>`;
    })
    .join("\n");

  const emptyState = grandTotal === 0
    ? `<p class="empty">No findings in scope (${escapeHtml(scopeLabel)}).</p>`
    : "";

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Spec Change Report — ${escapeHtml(generatedAt)}</title>
<style>
  :root { color-scheme: light; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         max-width: 980px; margin: 2rem auto; padding: 0 1.5rem; color: #1a202c;
         line-height: 1.5; }
  h1 { margin: 0 0 0.25rem; font-size: 1.6rem; }
  .meta { color: #4a5568; font-size: 0.9rem; margin-bottom: 1.5rem; }
  .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem;
             margin: 1rem 0 2rem; }
  .summary div { background: #f7fafc; border-radius: 8px; padding: 0.9rem 1rem;
                 border: 1px solid #e2e8f0; }
  .summary strong { display: block; font-size: 1.4rem; }
  .summary span { color: #4a5568; font-size: 0.8rem; text-transform: uppercase;
                  letter-spacing: 0.04em; }
  .status { display: inline-block; padding: 0.25rem 0.6rem; border-radius: 999px;
            font-weight: 600; font-size: 0.85rem; }
  .status.ok { background: #c6f6d5; color: #22543d; }
  .status.fail { background: #fed7d7; color: #742a2a; }
  .file-block { margin: 1.5rem 0; border: 1px solid #e2e8f0; border-radius: 8px;
                padding: 1rem 1.25rem; background: #fff; }
  .file-block h3 { margin: 0 0 0.75rem; font-size: 1rem; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; word-break: break-all; }
  .count { color: #718096; font-weight: normal; font-size: 0.85rem; }
  table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
  th, td { text-align: left; padding: 0.4rem 0.5rem; vertical-align: top;
           border-bottom: 1px solid #edf2f7; }
  th { background: #f7fafc; font-weight: 600; color: #2d3748; }
  td.num { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: #4a5568; width: 3.5rem; }
  td.rule { width: 9rem; }
  td.kind { width: 6.5rem; }
  tr.sev-code-red td.kind { color: #c53030; }
  tr.sev-style td.kind { color: #b7791f; }
  tr.sev-link td.kind { color: #2b6cb0; }
  .dot { display: inline-block; width: 0.55rem; height: 0.55rem; border-radius: 50%;
         margin-right: 0.35rem; vertical-align: middle; }
  .dot-red { background: #e53e3e; }
  .dot-amber { background: #d69e2e; }
  .dot-blue { background: #3182ce; }
  details.raw { margin-top: 2rem; }
  details.raw summary { cursor: pointer; color: #4a5568; font-size: 0.85rem; }
  pre { background: #1a202c; color: #e2e8f0; padding: 0.9rem 1rem; border-radius: 6px;
        overflow-x: auto; font-size: 0.78rem; line-height: 1.45; }
  .empty { background: #f0fff4; border: 1px solid #9ae6b4; padding: 1.25rem;
           border-radius: 8px; color: #22543d; font-weight: 500; }
  footer { margin-top: 2rem; color: #718096; font-size: 0.78rem; text-align: center; }
</style>
</head>
<body>
  <h1>Spec Change Report</h1>
  <p class="meta">
    Generated <strong>${escapeHtml(generatedAt)}</strong> · Scope: ${escapeHtml(scopeLabel)} ·
    <span class="status ${statusClass}">${status}</span>
  </p>

  <div class="summary">
    <div><strong>${grandTotal}</strong><span>Total findings</span></div>
    <div><strong>${totalCodeRed}</strong><span>Code Red</span></div>
    <div><strong>${totalStyle}</strong><span>Style</span></div>
    <div><strong>${totalLink}</strong><span>Cross-link</span></div>
  </div>

  ${emptyState || fileSections}

  <details class="raw">
    <summary>Raw validate-guidelines.py output</summary>
    <pre>${escapeHtml(validatorRaw || "(no output)")}</pre>
  </details>
  <details class="raw">
    <summary>Raw check-spec-cross-links.py output</summary>
    <pre>${escapeHtml(crossLinkRaw || "(no output)")}</pre>
  </details>

  <footer>Generated by <code>scripts/spec-change-report.mjs</code></footer>
</body>
</html>`;
}

// ---------------------------------------------------------------------
// 6. Optional PDF rendering
// ---------------------------------------------------------------------
function tryRenderPdf(htmlPath, pdfPath) {
  // Chromium's headless renderer cannot serve files from FUSE-mounted
  // paths (e.g. /mnt/documents) — it falls back to "view source" mode
  // and prints raw HTML. Copy the HTML to a real tmp dir, render there,
  // then move the PDF back.
  const tmpHtml = resolve(tmpdir(), `spec-change-report-${process.pid}.html`);
  const tmpPdf = resolve(tmpdir(), `spec-change-report-${process.pid}.pdf`);
  try {
    copyFileSync(htmlPath, tmpHtml);
  } catch (err) {
    return null;
  }

  const candidates = [
    ["wkhtmltopdf", ["--quiet", "--enable-local-file-access", tmpHtml, tmpPdf]],
    ["chromium", ["--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", `--print-to-pdf=${tmpPdf}`, `file://${tmpHtml}`]],
    ["google-chrome", ["--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", `--print-to-pdf=${tmpPdf}`, `file://${tmpHtml}`]],
  ];
  let renderer = null;
  for (const [bin, args] of candidates) {
    const which = spawnSync("which", [bin], { encoding: "utf8" });
    if (which.status !== 0) continue;
    const r = spawnSync(bin, args, { encoding: "utf8" });
    if (r.status === 0 && existsSync(tmpPdf)) { renderer = bin; break; }
  }

  if (renderer) {
    try { copyFileSync(tmpPdf, pdfPath); } catch { renderer = null; }
  }
  for (const p of [tmpHtml, tmpPdf]) {
    try { if (existsSync(p)) unlinkSync(p); } catch { /* ignore */ }
  }
  return renderer;
}

// ---------------------------------------------------------------------
// 7. Main
// ---------------------------------------------------------------------
function main() {
  const scope = listChangedSpecFiles();
  const v = runValidator();
  const c = runCrossLinkChecker();

  if (v.status === 2 || c.status === 2) {
    console.error("[spec-change-report] validator crashed");
    console.error(v.stderr || c.stderr);
    process.exit(2);
  }

  const validator = scopeToFiles(parseValidator(v.stdout), scope);
  const crossLink = scopeToFiles(parseCrossLink(c.stdout), scope);
  const generatedAt = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";

  const html = buildHtml({
    scope,
    validator,
    crossLink,
    validatorRaw: v.stdout,
    crossLinkRaw: c.stdout,
    generatedAt,
  });

  mkdirSync(OUT_DIR, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const htmlPath = resolve(OUT_DIR, `spec-change-report-${stamp}.html`);
  const pdfPath = resolve(OUT_DIR, `spec-change-report-${stamp}.pdf`);
  writeFileSync(htmlPath, html, "utf8");

  const pdfRenderer = tryRenderPdf(htmlPath, pdfPath);
  const findings = validator.length + crossLink.length;

  console.log(`[spec-change-report] HTML: ${relative(REPO_ROOT, htmlPath)}`);
  if (pdfRenderer) {
    console.log(`[spec-change-report]  PDF: ${relative(REPO_ROOT, pdfPath)} (via ${pdfRenderer})`);
  } else {
    console.log(`[spec-change-report]  PDF: skipped (no wkhtmltopdf / chromium found)`);
  }
  console.log(
    `[spec-change-report] Scope: ${scope ? scope.size + " changed file(s)" : "all"} · ` +
      `Findings: ${findings} (${validator.filter((f) => f.severity === "code-red").length} code-red, ` +
      `${validator.filter((f) => f.severity === "style").length} style, ${crossLink.length} link)`
  );

  process.exit(findings === 0 ? 0 : 1);
}

main();