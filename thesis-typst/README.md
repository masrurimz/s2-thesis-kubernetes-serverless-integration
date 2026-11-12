# ITS Thesis (Typst)

Canonical thesis book source. Two editions build from it: English (`build/thesis.pdf`) and Indonesian (`build/thesis-id.pdf`). Both carry the dual abstracts and the Indonesian ITS front matter.

## Build

```bash
make            # or make master: English edition, build/thesis.pdf
make master-id  # Indonesian edition, build/thesis-id.pdf
make check-id   # compare each Indonesian chapter with its English source
make watch      # live preview (typst watch)
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
- Each chapter and the appendices exist twice: `src/content/<name>.typ` (English, the source of truth) and `src/content/<name>.id.typ` (Indonesian). `src/thesis.typ` includes one or the other by edition.
- Change the English file first, then carry the change into the `.id.typ` file. `make check-id` fails when the Indonesian file lacks a citation, label, heading key, figure, table, code block or number that the English file has. Numbers compare by digits, so `0.307` matches `0,307`.
- Indonesian text follows `.agents/skills/bahasa-indonesia-plain/SKILL.md`: short active sentences, decimal comma, English technical terms kept in italics.
- Headings come from `src/content/headings.typ`, one dictionary per edition. Figure files are shared; a label that differs by edition uses `cap(en, id)`.
- Abstracts are always both (ID + EN). Cover, approval pages, KATA PENGANTAR and the biography are always Indonesian.

## Reproduction
From repo root:
```bash
cd thesis-typst && make
```

See also root AGENTS.md and docs/thesis/ for evidence links.
