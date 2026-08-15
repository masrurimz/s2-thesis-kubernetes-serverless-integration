# Chapter 4 Figures — Manifest

Five figures are **native Typst** (primaviz 0.9.1, single charting system), one
is a **matplotlib PNG** (H2 forest plot — no primaviz primitive exists).

Import the native charts from `content/figures.typ`:

```typst
#import "figures.typ": fig-cost-comparison, fig-paired-perpair, fig-slo-violations, fig-node-provisioning, fig-p99-boxplot
```

primaviz import: `#import "@preview/primaviz:0.9.1": *` (cached at
`~/.cache/typst/packages/preview/primaviz/0.9.1/`, verified on Typst 0.15.0).

| Figure | Function | Shows | Source bundle(s) | Key numbers |
|---|---|---|---|---|
| fig04_1 | `fig-paired-perpair()` | Per-pair p99 (S3 vs S4), definitive paired H2, n=5 | `2026-07-14_clarknet-tuned-paired-n5/paired_analysis.json` | P1–P5 S3: 235.6 / 192.2 / 151.4 / 164.0 / 199.2 ms; S4: 101.4 / 104.9 / 100.5 / 155.7 / 167.4 ms. SLO dashed at 200 ms. p=0.030, d=−1.26 |
| fig04_2 | `fig-p99-boxplot()` | Four-scenario p99 boxplot + 20 run points, n=5 | `2026-08-09_clarknet-replay_032257/*/result.json` | S1 med 112.7, S2 med 79.0, S3 med 151.6, S4 med 93.8 ms. SLO dashed at 200 ms |
| fig04_3 | `fig-slo-violations()` | SLO violations S3 vs S4, two tiers | definitive `*/result.json` + `2026-08-09_clarknet-replay_032257/report.md` | Definitive 656 vs 130 (−80.2%); n=5 1998 vs 92 (−95.4%) |
| fig04_4 | `fig-node-provisioning()` | Node CPU% timeline + full provisioning-event markers | `2026-07-14_clarknet-tuned-paired-n5/s3-hybrid-reactive_run1/{node_utilization,provision_events}.json` | pending_detected t≈317/577 s (grey), node_created t≈394/669 s (green), scale_down_detected t≈762/1229 s (red), node_deleted t≈764/1231 s (purple) |
| fig04_5 | `fig-cost-comparison()` | Monthly cost by scenario (n=1 diagnostic) | `results/claims/FINAL_NUMBERS.md` | S1=132, S2=394, S3=147, S4=142 USD/mo; definitive paired S3=S4=163 (dashed) |
| fig04_6 | `figures/fig04_6_replication_batches.png` (matplotlib) | H2 forest plot — S4−S3 mean diff (ms) with 95% CI whiskers | definitive + `2026-08-08_paired-h2_{195150,233726}/paired_analysis.json` + `2026-08-09_clarknet-replay_032257/report.md` | Definitive −62.5 [−100.9, −26.2] d=−1.26 p=0.030; RUN1 −4.0 [−57.8, +66.1] d=−0.05 p=0.436; RUN2 −58.0 [−161.5, −2.8] d=−0.51 p=0.062; RUN3 −52.5 [−102.6, −11.8] d=−1.30 MW p=0.032 |

## primaviz function names + annotation shapes (for text workers)

- `bar-chart(data)` — data is `(("label", value), ...)`; `theme: (palette: (colors...))` sets bar colors.
- `grouped-bar-chart(data)` — data is `(labels: ("l1","l2",...), series: ((name: "S3", values: (...)), (name: "S4", values: (...))))`.
- `line-chart(data)` — data is `((x, y), ...)`.
- `box-plot(data)` — data is `(labels: (...), boxes: ((min:, q1:, median:, q3:, max:, outliers: (...)), ...))`.

Annotation descriptors (passed via `annotations:`):
- `(type: "h-line", value: <y>, dash: "dashed", color: <c>, label: [..])` — SLO threshold.
- `(type: "v-line", value: <x>, dash: "dashed"|"dotted", color: <c>, label: [..])` — timeline event.
- `(type: "point", x: <x>, y: <y>, radius: <len>, fill: <c>)` — run-point overlay.

## Notes

- **No log scale** in primaviz (linear axes only). The SLO chart (92→1998) is
  drawn linear; the 656-vs-130 tier is still legible.
- **Regenerate the forest PNG**: `uv run python -m analysis_cli.thesis_figures`
  from the repo root.
- All numbers are read verbatim from the real bundles. If a bundle changes,
  re-source the values into `figures.typ` and `thesis_figures.py`.
