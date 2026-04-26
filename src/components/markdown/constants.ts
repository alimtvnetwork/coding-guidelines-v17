/**
 * Language-related constant maps for code block rendering.
 * Extracted from MarkdownRenderer to keep file sizes manageable.
 */

export const LANG_LABELS: Record<string, string> = {
  ts: "TypeScript",
  tsx: "TypeScript (JSX)",
  typescript: "TypeScript",
  js: "JavaScript",
  javascript: "JavaScript",
  go: "Go",
  golang: "Go",
  php: "PHP",
  css: "CSS",
  json: "JSON",
  bash: "Bash",
  sh: "Shell",
  shell: "Shell",
  sql: "SQL",
  rust: "Rust",
  html: "HTML",
  xml: "XML",
  yaml: "YAML",
  yml: "YAML",
  md: "Markdown",
  markdown: "Markdown",
  tree: "Structure",
  text: "Plain Text",
  "": "Plain Text",
};

export const LANG_COLORS: Record<string, string> = {
  typescript: "99 83% 62%",
  ts: "99 83% 62%",
  tsx: "99 83% 62%",
  javascript: "53 93% 54%",
  js: "53 93% 54%",
  go: "194 66% 55%",
  golang: "194 66% 55%",
  php: "234 45% 60%",
  css: "264 55% 58%",
  json: "38 92% 50%",
  bash: "120 40% 55%",
  sh: "120 40% 55%",
  shell: "120 40% 55%",
  sql: "200 70% 55%",
  rust: "25 85% 55%",
  html: "12 80% 55%",
  xml: "12 80% 55%",
  yaml: "0 75% 55%",
  yml: "0 75% 55%",
  md: "252 85% 60%",
  markdown: "252 85% 60%",
  tree: "252 85% 60%",
};

export const LANG_EXTENSIONS: Record<string, string> = {
  typescript: "ts",
  ts: "ts",
  tsx: "tsx",
  javascript: "js",
  js: "js",
  go: "go",
  golang: "go",
  php: "php",
  css: "css",
  json: "json",
  bash: "sh",
  sh: "sh",
  shell: "sh",
  sql: "sql",
  rust: "rs",
  html: "html",
  xml: "xml",
  yaml: "yaml",
  yml: "yml",
  md: "md",
  markdown: "md",
  tree: "txt",
  text: "txt",
  "": "txt",
};

export const TYPESCRIPT_LANGS = ["typescript", "ts", "tsx"];
export const JAVASCRIPT_LANGS = ["javascript", "js"];
export const GO_LANGS = ["go", "golang"];
export const PLAINTEXT_LANGS = ["text", "plaintext", "plain", "tree"];

export const ALL_SUPPORTED_LANGS = [
  "php", "css", "json", "bash", "sh", "shell",
  "sql", "rust", "html", "xml", "yaml", "yml",
  "markdown", "md",
];

export const DEFAULT_ACCENT_COLOR = "220 10% 50%";
export const DEFAULT_EXTENSION = "txt";
export const DEFAULT_FONT_SIZE = 18;
export const MIN_FONT_SIZE = 12;
export const MAX_FONT_SIZE = 32;
export const FONT_SIZE_STEP = 2;
export const COPY_FEEDBACK_DELAY = 2000;

/**
 * Threshold for showing the fullscreen "expand" affordance on docs-viewer
 * code blocks. Mirrors the landing-page CommandRow rule: only show when the
 * block is large enough that an enlarged view actually helps.
 */
export const EXPAND_LINE_THRESHOLD = 12;
