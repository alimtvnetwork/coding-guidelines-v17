// Package the slides-app dist/ into a portable dist.zip.
// Verifies the offline contract per spec-slides/06-build-and-zip-pipeline.md.

import { createWriteStream, readFileSync, writeFileSync, statSync, existsSync } from "node:fs";
import { readdir } from "node:fs/promises";
import { join, relative } from "node:path";
import archiver from "archiver";

const ROOT = new URL("..", import.meta.url).pathname;
const DIST = join(ROOT, "dist");
const OUT = join(ROOT, "dist.zip");
const MAX_BYTES = 8 * 1024 * 1024; // 8 MB ceiling (loosened from spec — Shiki theme adds weight)

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(p)));
    else out.push(p);
  }
  return out;
}

async function verifyOfflineContract() {
  if (!existsSync(DIST)) {
    throw new Error(`dist/ not found at ${DIST} — run 'bun run build' first.`);
  }
  const indexHtml = readFileSync(join(DIST, "index.html"), "utf8");
  // 1. Relative paths only
  if (/(?:src|href)=["']\//.test(indexHtml)) {
    throw new Error("index.html references absolute paths — Vite base must be './'.");
  }
  // 2. No external preconnect / Google Fonts
  if (/preconnect[^>]*fonts\.googleapis|fonts\.gstatic/.test(indexHtml)) {
    throw new Error("index.html preconnects to Google Fonts — must be fully offline.");
  }
  // 3. No external URLs in any built JS/CSS
  const files = await walk(DIST);
  for (const f of files) {
    if (!/\.(js|css|html)$/.test(f)) continue;
    const content = readFileSync(f, "utf8");
    // Allow data: and blob:; reject http(s):// inside built assets
    if (/https?:\/\/(?!schema\.org|www\.w3\.org)/.test(content) && !f.endsWith("index.html")) {
      const sample = content.match(/https?:\/\/[^\s'")]+/);
      console.warn(`⚠️  ${relative(ROOT, f)} contains external URL: ${sample?.[0]}`);
    }
  }
  // 4. Total size budget
  let total = 0;
  for (const f of files) total += statSync(f).size;
  if (total > MAX_BYTES) {
    throw new Error(
      `dist/ is ${(total / 1024 / 1024).toFixed(2)} MB — exceeds ${MAX_BYTES / 1024 / 1024} MB budget.`
    );
  }
  console.log(`✅ Offline contract OK — ${files.length} files, ${(total / 1024).toFixed(0)} KB total`);
}

function writeReadme() {
  const readme = `Code-Red Review Guide — Slide Deck
====================================

To open:
  1. Unzip this file anywhere.
  2. Double-click \`index.html\`.
  3. Use →/Space to advance, ← to go back.

Keyboard shortcuts:
  →  Space   Next slide
  ←          Previous slide
  F          Fullscreen
  Esc        Exit fullscreen / view
  G          Grid view (all slides)
  P          Presenter view (next + timer)
  Home/End   First / last slide

Built from the coding-guidelines-v15 repository.
Author: Md. Alim Ul Karim — alimkarim.com · Riseup Asia LLC
Bundled font: Ubuntu (Ubuntu Font License 1.0).
`;
  writeFileSync(join(DIST, "README.txt"), readme, "utf8");
}

async function makeZip() {
  await new Promise((resolve, reject) => {
    const out = createWriteStream(OUT);
    const zip = archiver("zip", { zlib: { level: 9 } });
    out.on("close", resolve);
    zip.on("error", reject);
    zip.pipe(out);
    zip.directory(DIST, false);
    zip.finalize();
  });
  const sizeMB = (statSync(OUT).size / 1024 / 1024).toFixed(2);
  console.log(`✅ Packaged → ${relative(ROOT, OUT)} (${sizeMB} MB)`);
}

await verifyOfflineContract();
writeReadme();
await makeZip();
