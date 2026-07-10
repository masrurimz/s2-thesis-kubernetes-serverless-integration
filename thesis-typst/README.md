# ITS Thesis (Typst)

Canonical thesis book source (English-first body + dual abstracts + Indonesian ITS front matter).

## Build

```bash
make          # or make master
# produces build/thesis.pdf
make watch    # live preview (typst watch)
make clean
```

Requires `typst` (via mise).

## Preview / Access Strategy (updated)

### 1. CLI continuous
```bash
cd thesis-typst
make watch
# or
typst watch src/thesis.typ build/thesis.pdf
```

### 2. VS Code Remote SSH + Tinymist (recommended rich editing)
- Install extension: `myriad-dreamin.tinymist`
- Open `src/thesis.typ`
- Cmd: "Typst Preview" (Ctrl+K V)
- Recommended workspace settings (`thesis-typst/.vscode/settings.json`):
  ```json
  {
    "tinymist.exportPdf": "onSave",
    "tinymist.outputPath": "$root/build/thesis.pdf",
    "tinymist.rootPath": "."
  }
  ```

### 3. Headless / no X11 fallback
Serve PDF:
```bash
python3 -m http.server 8899 --directory build
```
Open from client browser.

Do **not** use LaTeX Workshop as default.

## Fonts
Uses Liberation Serif/Sans (available on system) with fallbacks for Times/Trebuchet. Warnings expected but PDF renders.

## Packages (Deferred)
- cetz / cetz-plot (native charts) — temporarily disabled; see commented imports in ch04-results.typ
- lovelace (pseudocode) — temporarily disabled; see commented imports in ch04-results.typ
Charts currently use data tables; CeTZ plots to be re-enabled after package version pinning.

## Language
- Body: English first
- Abstracts: ID + EN (both)
- Structural labels (BAB, DAFTAR ISI, Gambar, Tabel): Indonesian (ITS requirement)
- Later ID body translation if required for submission.

## Reproduction
From repo root:
```bash
cd thesis-typst && make
```

See also root AGENTS.md and docs/thesis/ for evidence links.
