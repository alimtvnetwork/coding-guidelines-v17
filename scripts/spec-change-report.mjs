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
//   node scripts/spec-change-report.mjs                # staged+unstaged+untracked
//   node scripts/spec-change-report.mjs --all          # full repo, no scoping
//   node scripts/spec-change-report.mjs --staged       # only staged spec files
//   node scripts/spec-change-report.mjs --unstaged     # only unstaged + untracked
//   node scripts/spec-change-report.mjs --html-only    # skip PDF rendering
//   node scripts/spec-change-report.mjs --no-pdf       # alias for --html-only
//   node scripts/spec-change-report.mjs --editor <id>  # vscode|cursor|none
//   node scripts/spec-change-report.mjs --out <dir>    # custom out dir
//   node scripts/spec-change-report.mjs --help         # show usage
//
// Exit codes:
//   0  no findings in scope
//   1  findings present (CI-friendly)
//   2  validator crashed
//   3  invalid CLI flag combination
//
// Documented in: docs/spec-author-dx.md (Wave 2 add-on)
// =====================================================================

import { execSync, spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync, copyFileSync, renameSync, unlinkSync } from "node:fs";
import { resolve, relative, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

// ---------------------------------------------------------------------
// CLI parsing
// ---------------------------------------------------------------------
const USAGE = `Usage: node scripts/spec-change-report.mjs [options]

Scoping (mutually exclusive — pick at most one):
  --all          Validate the entire repo, no scoping
  --staged       Only spec files in the git index (git diff --cached)
  --unstaged     Only modified-but-unstaged + untracked spec files
  (default)      Union of staged + unstaged + untracked

Output:
  --html-only    Skip PDF rendering (alias: --no-pdf)
  --editor <id>  Deep-link scheme for finding rows.
                 vscode (default), cursor, or none for plain text.
  --out <dir>    Output directory (default: /mnt/documents)

Other:
  --help, -h     Show this message

Exit codes: 0 clean · 1 findings · 2 validator crash · 3 bad CLI flags`;

function parseArgs(argv) {
  const flags = {
    scopeAll: false,
    scopeStaged: false,
    scopeUnstaged: false,
    htmlOnly: false,
    editor: detectDefaultEditor(),
    outDir: "/mnt/documents",
    help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case "--all":      flags.scopeAll = true; break;
      case "--staged":   flags.scopeStaged = true; break;
      case "--unstaged": flags.scopeUnstaged = true; break;
      case "--html-only":
      case "--no-pdf":   flags.htmlOnly = true; break;
      case "--editor": {
        const next = argv[i + 1];
        if (!next || next.startsWith("--")) {
          console.error(`[spec-change-report] --editor requires one of: vscode, cursor, none`);
          process.exit(3);
        }
        if (!["vscode", "cursor", "none"].includes(next)) {
          console.error(`[spec-change-report] unknown --editor value: ${next} (expected vscode|cursor|none)`);
          process.exit(3);
        }
        flags.editor = next;
        i += 1;
        break;
      }
      case "--out": {
        const next = argv[i + 1];
        if (!next || next.startsWith("--")) {
          console.error(`[spec-change-report] --out requires a directory path`);
          process.exit(3);
        }
        flags.outDir = resolve(next);
        i += 1;
        break;
      }
      case "--help":
      case "-h": flags.help = true; break;
      default:
        console.error(`[spec-change-report] unknown flag: ${a}`);
        console.error(USAGE);
        process.exit(3);
    }
  }
  const scopeFlags = [flags.scopeAll, flags.scopeStaged, flags.scopeUnstaged].filter(Boolean).length;
  if (scopeFlags > 1) {
    console.error(`[spec-change-report] --all, --staged, and --unstaged are mutually exclusive`);
    console.error(USAGE);
    process.exit(3);
  }
  return flags;
}

// ---------------------------------------------------------------------
// Editor / deep-link helpers
// ---------------------------------------------------------------------
function detectDefaultEditor() {
  const term = (process.env.TERM_PROGRAM || "").toLowerCase();
  const editor = (process.env.EDITOR || "").toLowerCase();
  if (term.includes("cursor") || editor.includes("cursor")) return "cursor";
  // vscode is the safe default — both VS Code and Cursor handle vscode://
  return "vscode";
}

function buildDeepLink(file, line) {
  if (FLAGS.editor === "none") return null;
  // vscode:// works in VS Code, Cursor, and most VS Code forks.
  // cursor:// is Cursor's native scheme.
  const scheme = FLAGS.editor === "cursor" ? "cursor" : "vscode";
  const abs = resolve(REPO_ROOT, file);
  // Browsers leave `:` alone in path segments, which is what VS Code wants.
  return `${scheme}://file${abs}:${Math.max(1, line || 1)}`;
}

// The cross-link checker's "detail" field looks like:
//   "text: ... · target: ../foo.md · detail: /abs/path/to/foo.md"
// or "/abs/path/to/foo.md#anchor". Pull the resolved local file out of
// the `detail:` segment so we can deep-link to the broken target too.
function buildTargetLink(detailString) {
  if (FLAGS.editor === "none" || !detailString) return null;
  const m = detailString.match(/detail:\s*([^\s·]+)/);
  if (!m) return null;
  let target = m[1];
  // Drop a trailing "#anchor" — editors don't honor it for plain files.
  const hashIdx = target.indexOf("#");
  if (hashIdx !== -1) target = target.slice(0, hashIdx);
  if (!target || !existsSync(target)) return null;
  const scheme = FLAGS.editor === "cursor" ? "cursor" : "vscode";
  return `${scheme}://file${target}:1`;
}

const FLAGS = parseArgs(process.argv.slice(2));
if (FLAGS.help) {
  console.log(USAGE);
  process.exit(0);
}
const OUT_DIR = FLAGS.outDir;

// ---------------------------------------------------------------------
// 1. Determine which spec files changed
// ---------------------------------------------------------------------
function readGit(cmd) {
  try {
    return execSync(cmd, { cwd: REPO_ROOT, encoding: "utf8" });
  } catch (err) {
    console.warn(`[spec-change-report] git command failed: ${cmd}\n  ${err.message}`);
    return "";
  }
}

function filterSpecMarkdown(blob) {
  return blob
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.startsWith("spec/") && s.endsWith(".md"));
}

function listChangedSpecFiles() {
  if (FLAGS.scopeAll) return { scope: null, label: "entire repo" };

  const staged   = readGit("git diff --cached --name-only --diff-filter=ACMR");
  const unstaged = readGit("git diff --name-only --diff-filter=ACMR");
  const untracked = readGit("git ls-files --others --exclude-standard");

  let files = [];
  let label = "";
  if (FLAGS.scopeStaged) {
    files = filterSpecMarkdown(staged);
    label = "staged spec files";
  } else if (FLAGS.scopeUnstaged) {
    files = [...filterSpecMarkdown(unstaged), ...filterSpecMarkdown(untracked)];
    label = "unstaged + untracked spec files";
  } else {
    files = [
      ...filterSpecMarkdown(staged),
      ...filterSpecMarkdown(unstaged),
      ...filterSpecMarkdown(untracked),
    ];
    label = "changed spec files (staged + unstaged + untracked)";
  }
  return { scope: new Set(files), label };
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

function buildHtml({ scope, scopeLabel, validator, crossLink, validatorRaw, crossLinkRaw, generatedAt }) {
  const scopedFileCount = scope ? scope.size : null;
  const scopeBadge = scope === null
    ? scopeLabel
    : `${scopedFileCount} ${scopeLabel}`;
  const totalCodeRed = validator.filter((f) => f.severity === "code-red").length;
  const totalStyle = validator.filter((f) => f.severity === "style").length;
  const totalLink = crossLink.length;
  const grandTotal = totalCodeRed + totalStyle + totalLink;
  const status = grandTotal === 0 ? "Clean" : "Findings present";
  const statusClass = grandTotal === 0 ? "ok" : "fail";

  const validatorByFile = groupBy(validator, (f) => f.file);
  const linkByFile = groupBy(crossLink, (f) => f.file);
  const allFiles = new Set([...validatorByFile.keys(), ...linkByFile.keys()]);

  const fileSections = [...allFiles]
    .sort()
    .map((file) => {
      const v = validatorByFile.get(file) || [];
      const l = linkByFile.get(file) || [];
      const fileLink = buildDeepLink(file, 1);
      const fileHeading = fileLink
        ? `<a class="file-link" href="${escapeHtml(fileLink)}">${escapeHtml(file)}</a>`
        : escapeHtml(file);
      const rows = [
        ...v.map(
          (f) => {
            const link = buildDeepLink(f.file, f.line);
            const lineCell = link
              ? `<a class="line-link" href="${escapeHtml(link)}">L${f.line}</a>`
              : `L${f.line}`;
            return `
          <tr class="sev-${f.severity}">
            <td class="num">${lineCell}</td>
            <td class="rule"><code>${escapeHtml(f.rule)}</code></td>
            <td class="kind">${f.severity === "code-red" ? "<span class='dot dot-red'></span> Code Red" : "<span class='dot dot-amber'></span> Style"}</td>
            <td class="msg">${escapeHtml(f.message)}</td>
          </tr>`;
          }
        ),
        ...l.map(
          (f) => {
            const sourceLink = buildDeepLink(f.file, f.line);
            const lineCell = sourceLink
              ? `<a class="line-link" href="${escapeHtml(sourceLink)}">L${f.line}</a>`
              : `L${f.line}`;
            const targetLink = buildTargetLink(f.detail);
            const detailCell = targetLink
              ? `${escapeHtml(f.detail)} · <a class="target-link" href="${escapeHtml(targetLink)}">open target</a>`
              : escapeHtml(f.detail);
            return `
          <tr class="sev-link">
            <td class="num">${lineCell}</td>
            <td class="rule"><code>${escapeHtml(f.kind)}</code></td>
            <td class="kind"><span class='dot dot-blue'></span> Link</td>
            <td class="msg">${detailCell}</td>
          </tr>`;
          }
        ),
      ].join("");
      return `
        <section class="file-block">
          <h3>${fileHeading} <span class="count">(${v.length + l.length})</span></h3>
          <table>
            <thead><tr><th>Line</th><th>Rule</th><th>Kind</th><th>Detail</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </section>`;
    })
    .join("\n");

  const emptyState = grandTotal === 0
    ? `<p class="empty">No findings in scope (${escapeHtml(scopeBadge)}).</p>`
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
  a.line-link, a.file-link, a.target-link {
    color: #2b6cb0; text-decoration: none; border-bottom: 1px dotted #90cdf4;
  }
  a.line-link:hover, a.file-link:hover, a.target-link:hover {
    color: #2c5282; border-bottom-color: #2b6cb0;
  }
  a.file-link { font-family: inherit; }
  a.target-link { font-size: 0.82rem; }
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
  .editor-badge { font-size: 0.78rem; color: #2c5282; background: #ebf8ff;
                  border: 1px solid #bee3f8; padding: 0.1rem 0.45rem;
                  border-radius: 999px; }
  footer { margin-top: 2rem; color: #718096; font-size: 0.78rem; text-align: center; }
</style>
</head>
<body>
  <h1>Spec Change Report</h1>
  <p class="meta">
    Generated <strong>${escapeHtml(generatedAt)}</strong> · Scope: ${escapeHtml(scopeBadge)} ·
    <span class="status ${statusClass}">${status}</span>${
      FLAGS.editor === "none"
        ? ""
        : ` · <span class="editor-badge">deep links → ${escapeHtml(FLAGS.editor)}</span>`
    }
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
  if (FLAGS.htmlOnly) return "skipped";
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
  const { scope, label: scopeLabel } = listChangedSpecFiles();
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
    scopeLabel,
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
  if (pdfRenderer === "skipped") {
    console.log(`[spec-change-report]  PDF: skipped (--html-only)`);
  } else if (pdfRenderer) {
    console.log(`[spec-change-report]  PDF: ${relative(REPO_ROOT, pdfPath)} (via ${pdfRenderer})`);
  } else {
    console.log(`[spec-change-report]  PDF: skipped (no wkhtmltopdf / chromium found)`);
  }
  console.log(
    `[spec-change-report] Scope: ${scope === null ? "all" : scope.size + " file(s) — " + scopeLabel} · ` +
      `Findings: ${findings} (${validator.filter((f) => f.severity === "code-red").length} code-red, ` +
      `${validator.filter((f) => f.severity === "style").length} style, ${crossLink.length} link)`
  );

  process.exit(findings === 0 ? 0 : 1);
}

main();