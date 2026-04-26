/**
 * Builds HTML for fenced code blocks with line numbers, copy, download, fullscreen.
 */
import { escapeHtml, highlightCode, resolveDisplayLang } from "./highlighter";
import {
  LANG_LABELS, LANG_COLORS, LANG_EXTENSIONS,
  DEFAULT_ACCENT_COLOR, DEFAULT_EXTENSION, EXPAND_LINE_THRESHOLD,
} from "./constants";

interface HeaderOpts {
  label: string;
  accentColor: string;
  lineCount: number;
  id: number;
  escaped: string;
  ext: string;
}

function buildLineNumbersHtml(lineCount: number): string {
  return Array.from({ length: lineCount }, (_, i) =>
    `<span class="code-line-number">${i + 1}</span>`
  ).join("");
}

function buildCodeLinesHtml(renderedLines: string[]): string {
  return renderedLines
    .map((line, i) => `<span class="code-line" data-line="${i + 1}">${line || " "}</span>`)
    .join("");
}

function buildFontControls(id: number): string {
  return `<div class="code-font-controls">
          <button class="code-tool-btn font-decrease-btn" title="Decrease font size" data-block-id="${id}">A-</button>
          <button class="code-tool-btn font-reset-btn" title="Reset font size" data-block-id="${id}">A</button>
          <button class="code-tool-btn font-increase-btn" title="Increase font size" data-block-id="${id}">A+</button>
        </div>`;
}

function buildCopyButton(escaped: string): string {
  return `<button class="code-tool-btn copy-code-btn" data-code="${escaped.replace(/"/g, "&quot;")}" title="Copy code">
          <svg class="copy-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <svg class="check-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
          <span class="copy-label">Copy</span>
        </button>`;
}

function buildDownloadButton(opts: HeaderOpts): string {
  return `<button class="code-tool-btn download-code-btn" data-code="${opts.escaped.replace(/"/g, "&quot;")}" data-ext="${opts.ext}" data-lang="${opts.label}" title="Download as file">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span>Download</span>
        </button>`;
}

function buildFullscreenButton(id: number): string {
  // Maximize2-style icon — visually consistent with the landing CommandRow
  // expand button (`lucide-react/Maximize2`).
  return `<button class="code-tool-btn fullscreen-code-btn" data-block-id="${id}" title="Expand to fullscreen" aria-label="Expand code block">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
        </button>`;
}

function buildHeaderLeft(opts: HeaderOpts): string {
  const lineLabel = opts.lineCount !== 1 ? "s" : "";

  return `<div class="code-lang-badge" style="--badge-color: ${opts.accentColor}">
        <span class="code-lang-dot"></span>
        <span>${opts.label}</span>
      </div>`;
}

function buildHeaderRight(opts: HeaderOpts): string {
  const lineLabel = opts.lineCount !== 1 ? "s" : "";
  const isExpandWorthwhile = opts.lineCount >= EXPAND_LINE_THRESHOLD;
  const expandSlot = isExpandWorthwhile ? buildFullscreenButton(opts.id) : "";

  return `<div class="code-header-right">
        <span class="code-line-count">${opts.lineCount} line${lineLabel}</span>
        <span class="code-selection-label" style="display:none"></span>
        ${buildFontControls(opts.id)}
        ${buildCopyButton(opts.escaped)}
        ${buildDownloadButton(opts)}
        ${expandSlot}
      </div>`;
}

function buildHeaderHtml(opts: HeaderOpts): string {
  return `<div class="code-block-header">
      ${buildHeaderLeft(opts)}
      ${buildHeaderRight(opts)}
    </div>`;
}

function buildSelectionBarHtml(): string {
  return `<div class="copy-selected-bar" style="display:none">
      <span class="copy-selected-label"></span>
      <button class="code-tool-btn copy-selected-btn" title="Copy selected lines">
        <svg class="copy-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        <svg class="check-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
        <span class="copy-label">Copy selected</span>
      </button>
      <button class="code-tool-btn clear-selected-btn" title="Clear selection">✕</button>
    </div>`;
}

interface BlockMeta {
  displayLang: string;
  label: string;
  accentColor: string;
  ext: string;
}

function resolveBlockMeta(displayLang: string): BlockMeta {
  return {
    displayLang,
    label: LANG_LABELS[displayLang] || displayLang || "Plain Text",
    accentColor: LANG_COLORS[displayLang] || DEFAULT_ACCENT_COLOR,
    ext: LANG_EXTENSIONS[displayLang] || DEFAULT_EXTENSION,
  };
}

function buildBlockBody(lineCount: number, renderedLines: string[], displayLang: string): string {
  return `<div class="code-block-body">
      <pre class="code-line-numbers" aria-hidden="true">${buildLineNumbersHtml(lineCount)}</pre>
      <pre class="code-content"><code class="hljs language-${displayLang || "text"}">${buildCodeLinesHtml(renderedLines)}</code></pre>
    </div>`;
}

export function buildCodeBlockHtml(code: string, lang: string, id: number): string {
  const trimmed = code.trimEnd();
  const displayLang = resolveDisplayLang(trimmed, lang);
  const highlighted = highlightCode(trimmed, displayLang);
  const escaped = escapeHtml(trimmed);
  const renderedLines = highlighted.split("\n");
  const lineCount = trimmed.split("\n").length;
  const meta = resolveBlockMeta(displayLang);
  const headerOpts: HeaderOpts = { label: meta.label, accentColor: meta.accentColor, lineCount, id, escaped, ext: meta.ext };

  return `<div class="code-block-wrapper my-5" style="--lang-accent: ${meta.accentColor}" data-block-id="${id}">
    ${buildHeaderHtml(headerOpts)}
    ${buildBlockBody(lineCount, renderedLines, displayLang)}
    ${buildSelectionBarHtml()}
  </div>`;
}
