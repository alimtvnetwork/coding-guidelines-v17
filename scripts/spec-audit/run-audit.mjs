#!/usr/bin/env node
// Spec Audit Pipeline — single-command refresh of audit artifacts.
// Outputs: spec-audit-report.md, spec-audit-scores.csv, spec-audit-raw.json
// Usage:  bun run spec:audit  (or `node scripts/spec-audit/run-audit.mjs`)

import { readdirSync, statSync, readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';

const SPEC_ROOT = 'spec';
const OUT_DIR = process.env.SPEC_AUDIT_OUT_DIR || 'spec-audit-output';
const SKIP_FOLDERS = new Set(['21-app', '22-app-issues', '23-app-db', '24-app-ui-design-system']);
const API_KEY = process.env.LOVABLE_API_KEY;
const MODEL = process.env.SPEC_AUDIT_MODEL || 'google/gemini-2.5-flash';
const GATEWAY_URL = 'https://ai.gateway.lovable.dev/v1/chat/completions';

function listSpecFolders() {
  return readdirSync(SPEC_ROOT)
    .filter((n) => /^\d{2}-/.test(n))
    .filter((n) => statSync(join(SPEC_ROOT, n)).isDirectory())
    .sort();
}

function collectFolderText(folder) {
  const dir = join(SPEC_ROOT, folder);
  const files = readdirSync(dir).filter((f) => f.endsWith('.md')).sort();
  const parts = [`# Folder: ${folder}`, `Files: ${files.length}`, ''];
  for (const f of files) {
    const content = readFileSync(join(dir, f), 'utf8').slice(0, 6000);
    parts.push(`--- FILE: ${f} ---`, content, '');
  }
  return parts.join('\n').slice(0, 60000);
}

function buildPrompt(folder, text) {
  return `You are auditing the spec folder "${folder}" for AI-implementation readiness.

Score each axis 0-100 (integers):
- completeness: are all needed files/sections present?
- specificity: are contracts concrete (regex, schemas, exit codes) vs prose?
- testability: can outcomes be verified deterministically?
- consistency: do overview/inventory/files agree?
- ai_implementability: could a mediocre AI implement this with 100% confidence?

Then return STRICT JSON ONLY (no prose) with this shape:
{
  "folder": "${folder}",
  "scores": {"completeness":N,"specificity":N,"testability":N,"consistency":N,"ai_implementability":N},
  "overall_score": N,
  "severity": "critical|high|medium|low|ok",
  "purpose_summary": "one sentence",
  "top_failures": [{"issue":"...","why_it_fails_ai":"...","fix":"..."}],
  "missing_to_reach_100": ["...","..."]
}

Severity rule: <40 critical, 40-59 high, 60-79 medium, 80-89 low, >=90 ok.

SPEC CONTENT:
${text}`;
}

async function callGateway(prompt) {
  const res = await fetch(GATEWAY_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${API_KEY}` },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: prompt }],
      response_format: { type: 'json_object' },
    }),
  });
  if (!res.ok) throw new Error(`Gateway ${res.status}: ${await res.text()}`);
  const json = await res.json();
  const content = json.choices?.[0]?.message?.content || '{}';
  return JSON.parse(content);
}

async function auditFolder(folder) {
  const text = collectFolderText(folder);
  const prompt = buildPrompt(folder, text);
  const result = await callGateway(prompt);
  result.folder = `spec/${folder}`;
  result.excluded_from_corpus = SKIP_FOLDERS.has(folder);
  if (result.excluded_from_corpus) {
    result.exclusion_reason = 'Intentional stub — placeholder for future app-specific content';
  }
  return result;
}

function avg(nums) {
  return nums.length ? Math.round((nums.reduce((a, b) => a + b, 0) / nums.length) * 10) / 10 : 0;
}

function median(nums) {
  if (!nums.length) return 0;
  const s = [...nums].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : Math.round(((s[m - 1] + s[m]) / 2) * 10) / 10;
}

function summarize(results) {
  const kept = results.filter((r) => !r.excluded_from_corpus);
  const skipped = results.filter((r) => r.excluded_from_corpus);
  const scores = kept.map((r) => r.overall_score);
  const axes = ['completeness', 'specificity', 'testability', 'consistency', 'ai_implementability'];
  const axisAverages = {};
  for (const a of axes) axisAverages[a] = avg(kept.map((r) => r.scores?.[a] ?? 0));
  const sevCounts = { critical: 0, high: 0, medium: 0, low: 0, ok: 0 };
  for (const r of kept) sevCounts[r.severity] = (sevCounts[r.severity] ?? 0) + 1;
  return {
    audit_date: new Date().toISOString().slice(0, 10),
    model: MODEL,
    total_folders: results.length,
    effective_corpus_size: kept.length,
    excluded_count: skipped.length,
    excluded_folders: skipped.map((r) => basename(r.folder)),
    corpus_average_effective: avg(scores),
    median_effective: median(scores),
    severity_counts: sevCounts,
    axis_averages_effective: axisAverages,
    folders: results,
  };
}

function writeJson(summary) {
  writeFileSync(join(OUT_DIR, 'spec-audit-raw.json'), JSON.stringify(summary, null, 2));
}

function writeCsv(summary) {
  const headers = ['folder', 'overall_score', 'severity', 'completeness', 'specificity', 'testability', 'consistency', 'ai_implementability', 'excluded'];
  const lines = [headers.join(',')];
  for (const r of summary.folders) {
    const s = r.scores || {};
    lines.push([r.folder, r.overall_score, r.severity, s.completeness ?? '', s.specificity ?? '', s.testability ?? '', s.consistency ?? '', s.ai_implementability ?? '', r.excluded_from_corpus ? 'yes' : 'no'].join(','));
  }
  writeFileSync(join(OUT_DIR, 'spec-audit-scores.csv'), lines.join('\n'));
}

function writeMarkdown(summary) {
  const lines = [];
  lines.push('# Spec Audit — AI-Implementation Readiness');
  lines.push('');
  lines.push(`**Audit date:** ${summary.audit_date}`);
  lines.push(`**Model:** \`${summary.model}\``);
  lines.push(`**Folders audited:** ${summary.total_folders} (effective corpus: ${summary.effective_corpus_size}, ${summary.excluded_count} stubs excluded)`);
  lines.push('');
  lines.push('> Excluded stubs: ' + summary.excluded_folders.map((f) => `\`${f}\``).join(', '));
  lines.push('');
  lines.push('## Executive summary');
  lines.push('');
  lines.push('| Metric | Value |');
  lines.push('|---|---|');
  lines.push(`| Effective average | **${summary.corpus_average_effective}/100** |`);
  lines.push(`| Median | ${summary.median_effective}/100 |`);
  lines.push('');
  lines.push('### Severity distribution');
  lines.push('');
  lines.push('| Severity | Count |');
  lines.push('|---|---|');
  for (const [k, v] of Object.entries(summary.severity_counts)) lines.push(`| ${k} | ${v} |`);
  lines.push('');
  lines.push('### Axis averages (effective)');
  lines.push('');
  lines.push('| Axis | Avg |');
  lines.push('|---|---|');
  for (const [k, v] of Object.entries(summary.axis_averages_effective)) lines.push(`| ${k} | ${v} |`);
  lines.push('');
  lines.push('## Per-folder scores (worst → best, effective only)');
  lines.push('');
  lines.push('| Folder | Score | Severity | Top failure |');
  lines.push('|---|---|---|---|');
  const sorted = [...summary.folders].filter((r) => !r.excluded_from_corpus).sort((a, b) => a.overall_score - b.overall_score);
  for (const r of sorted) {
    const tf = (r.top_failures?.[0]?.issue || '').replace(/\|/g, '\\|').slice(0, 100);
    lines.push(`| \`${basename(r.folder)}\` | ${r.overall_score} | ${r.severity} | ${tf} |`);
  }
  lines.push('');
  lines.push('## Excluded stubs (not counted)');
  lines.push('');
  for (const r of summary.folders.filter((x) => x.excluded_from_corpus)) {
    lines.push(`- \`${basename(r.folder)}\` — score ${r.overall_score} (excluded)`);
  }
  lines.push('');
  writeFileSync(join(OUT_DIR, 'spec-audit-report.md'), lines.join('\n'));
}

async function main() {
  if (!API_KEY) {
    console.error('❌ LOVABLE_API_KEY not set. Cannot run spec audit.');
    process.exit(1);
  }
  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });
  const folders = listSpecFolders();
  console.log(`🔍 Auditing ${folders.length} spec folders with ${MODEL}...`);
  const results = [];
  for (const f of folders) {
    process.stdout.write(`  • ${f} ... `);
    try {
      const r = await auditFolder(f);
      results.push(r);
      console.log(`${r.overall_score} (${r.severity})${r.excluded_from_corpus ? ' [excluded]' : ''}`);
    } catch (e) {
      console.log(`FAILED: ${e.message}`);
      results.push({ folder: `spec/${f}`, overall_score: 0, severity: 'critical', scores: {}, top_failures: [{ issue: 'Audit call failed', why_it_fails_ai: e.message, fix: 'Retry' }], missing_to_reach_100: [], excluded_from_corpus: SKIP_FOLDERS.has(f) });
    }
  }
  const summary = summarize(results);
  writeJson(summary);
  writeCsv(summary);
  writeMarkdown(summary);
  console.log('');
  console.log(`✅ Done. Effective avg: ${summary.corpus_average_effective}/100 (median ${summary.median_effective})`);
  console.log(`📄 Artifacts written to ${OUT_DIR}/:`);
  console.log(`   - spec-audit-report.md`);
  console.log(`   - spec-audit-scores.csv`);
  console.log(`   - spec-audit-raw.json`);
}

main().catch((e) => { console.error(e); process.exit(1); });
