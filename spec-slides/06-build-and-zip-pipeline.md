# Build & ZIP Pipeline

**Version:** 1.0.0

---

## Goal

A trainer downloads `dist.zip`, unzips it anywhere on their machine,
double-clicks `index.html`, and the deck runs in their default browser with
zero internet, zero install, zero server.

## Build commands

```bash
cd slides-app
bun install                  # one-time
bun run build                # → slides-app/dist/
bun run package              # → slides-app/dist.zip
```

Or combined:

```bash
bun run build && bun run package
```

## `package.json` scripts (slides-app)

```json
{
  "scripts": {
    "dev":     "vite",
    "build":   "tsc -b && vite build",
    "preview": "vite preview",
    "package": "node scripts/package-zip.mjs",
    "render-gifs": "node scripts/render-gifs.mjs"
  }
}
```

## Build output contract

`slides-app/dist/` after `bun run build` must contain:

```
dist/
├── index.html                    ← entry, opens in any modern browser
├── assets/
│   ├── index-<hash>.js          ← bundled React + slides
│   ├── index-<hash>.css
│   └── (no other JS chunks — single bundle for offline simplicity)
├── fonts/
│   ├── Ubuntu-Regular.ttf
│   ├── Ubuntu-Bold.ttf
│   ├── UbuntuMono-Regular.ttf
│   └── UFL-1.0.txt              ← font license
└── README.txt                    ← human-readable usage instructions
```

Hard requirements verified by the package script:

1. `index.html` must use **relative paths** (`./assets/...`, `./fonts/...`).
2. **No `http://` or `https://` references** anywhere in the built JS/CSS/HTML.
3. **No `<link rel="preconnect">`** to Google Fonts or any CDN.
4. Total size **< 5 MB** (deck + fonts + Shiki-rendered code blocks).
5. Single JS chunk (set `build.rollupOptions.output.manualChunks = undefined`).

## `scripts/package-zip.mjs` (skeleton)

Pseudocode — full implementation in the next phase.

```js
import { createWriteStream, readFileSync } from 'node:fs';
import archiver from 'archiver';
import { join } from 'node:path';

const DIST = './dist';
const OUT  = './dist.zip';

// 1. Verification pass — fail loudly if offline contract is violated
verifyNoExternalUrls(DIST);
verifyRelativePaths(join(DIST, 'index.html'));
verifyTotalSize(DIST, 5 * 1024 * 1024);

// 2. Inject README.txt with usage instructions
writeReadme(join(DIST, 'README.txt'));

// 3. Zip everything in dist/ at the root level (no leading folder)
const out = createWriteStream(OUT);
const zip = archiver('zip', { zlib: { level: 9 } });
zip.pipe(out);
zip.directory(DIST, false);
await zip.finalize();

console.log(`✅ Packaged → ${OUT}`);
```

## `README.txt` shipped inside the zip

Plain text, ≤30 lines:

```
Code-Red Review Guide — Slide Deck
====================================

To open:
  1. Unzip this file anywhere.
  2. Double-click `index.html`.
  3. Use ←/→ arrows or Space to navigate.

Keyboard shortcuts:
  →  Space   Next slide
  ←          Previous slide
  F          Fullscreen
  Esc        Exit fullscreen
  G          Grid view
  P          Presenter view (notes + timer)
  Home/End   First / last slide

Built from the coding-guidelines-v15 repository.
Author: Md. Alim Ul Karim — alimkarim.com
License: see UFL-1.0.txt for the bundled Ubuntu fonts.
```

## CI / release integration (future)

When the main repo is tagged for release, a CI job calls
`cd slides-app && bun install && bun run build && bun run package` and uploads
`slides-app/dist.zip` as a GitHub Release asset alongside the main install
scripts. (Out of scope for the initial implementation — flag this as a
follow-up.)

## Cross-references

- Architecture & Vite config (`base: './'`): [01-architecture.md](./01-architecture.md)
- Offline guarantees verification: [08-quality-and-offline.md](./08-quality-and-offline.md)
