#!/usr/bin/env node
// ============================================================
// generate-readme-txt.mjs
// ============================================================
// Generates ./readme.txt containing exactly:
//
//   let's start now DD-MMM-YYYY HH:MM:SS AM/PM
//
// where:
//   {date:dd-MMM-YYYY}        → zero-padded day, 3-letter month (English),
//                               4-digit year   (e.g. 09-Jan-2026)
//   {time:12 hr clock format} → HH:MM:SS in 12-hour clock with AM/PM
//                               (e.g. 03:07:42 PM)
//
// Always uses the system local time at the moment the script runs.
//
// USAGE
//   node scripts/generate-readme-txt.mjs            # writes ./readme.txt
//   node scripts/generate-readme-txt.mjs --print    # also echo to stdout
// ============================================================

import { writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const OUT_PATH = resolve(ROOT, "readme.txt");

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function pad2(n) {
  return String(n).padStart(2, "0");
}

function formatDate(d) {
  // dd-MMM-YYYY  →  09-Jan-2026
  return `${pad2(d.getDate())}-${MONTHS[d.getMonth()]}-${d.getFullYear()}`;
}

function format12hTime(d) {
  // HH:MM:SS AM/PM  →  03:07:42 PM
  const h24 = d.getHours();
  const period = h24 >= 12 ? "PM" : "AM";
  let h12 = h24 % 12;
  if (h12 === 0) h12 = 12;
  return `${pad2(h12)}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())} ${period}`;
}

function buildLine(d = new Date()) {
  return `let's start now ${formatDate(d)} ${format12hTime(d)}`;
}

const line = buildLine();
writeFileSync(OUT_PATH, line + "\n", "utf8");

if (process.argv.includes("--print")) {
  process.stdout.write(line + "\n");
}
process.stdout.write(`Wrote ${OUT_PATH}\n`);
