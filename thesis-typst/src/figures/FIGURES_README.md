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
| fig04_1 | `fig-paired-perpair()` | Per-pair p99 (S3 vs S4), July paired H2 batch (history), n=5 | `2026-07-14_clarknet-tuned-paired-n5/paired_analysis.json` | P1–P5 S3: 235.6 / 192.2 / 151.4 / 164.0 / 199.2 ms; S4: 101.4 / 104.9 / 100.5 / 155.7 / 167.4 ms. SLO dashed at 200 ms. p=0.0312, d=−1.26 |
| fig04_2 | `fig-p99-boxplot()` | Four-scenario p99 boxplot + 20 run points, n=5 | `2026-08-09_clarknet-replay_032257/*/result.json` | S1 med 112.7, S2 med 79.0, S3 med 151.6, S4 med 93.8 ms. SLO dashed at 200 ms |
| fig04_3 | `fig-slo-violations()` | SLO violations S3 vs S4, two tiers | July batch `*/result.json` + `2026-08-09_clarknet-replay_032257/*/result.json` | Per-run mean SLO violations: July batch 656 vs 130 (−80.2%); n=5 replication 399.6 vs 18.4 (−95.4%). Five-run totals for the replication are 1998 vs 92 |
| fig04_4 | `fig-node-provisioning()` | Node CPU% timeline + full provisioning-event markers | `2026-07-14_clarknet-tuned-paired-n5/s3-hybrid-reactive_run1/{node_utilization,provision_events}.json` | Marker x = seconds from run start (`ts - t_start`, `t_start` from that run's `result.json`). pending_detected t=317.7/576.9 s (grey dotted), provision_delay t=317.7/576.9 s (orange dashed), node_created t=394.4/669.5 s (green), scale_down_detected t=762.2/1229.5 s (red), node_deleted t=763.7/1231.0 s (purple) |
| fig04_5 | `fig-cost-comparison()` | Monthly cost by scenario (n=1 diagnostic) | `results/cost_analysis/cost_analysis_20260711_112337.json` (monthly = aws_cost.total × 2,592,000 s / duration) | S1=132, S2=395, S3=147, S4=143 USD/mo |
| fig04_6 | `figures/fig04_6_replication_batches.png` (English), `figures/fig04_6_replication_batches_id.png` (Indonesian), matplotlib | H2 forest plot: S4-S3 mean p99 difference (ms) with 95% CI; the pre-registered batch on top, history batches below | `2026-09-20_h2-confirmatory-10p`, `2026-07-14_clarknet-tuned-paired-n5`, `2026-08-08_paired-h2_{195150,233726}`, `2026-09-13_h2-pair-5p`, `2026-09-13_h2-confirmatory-10p` (`paired_analysis.json`), and `2026-08-09_clarknet-replay_032257/report.md` (Welch) | Pre-registered -13.6 [-63.5, +35.6]; July -62.5 [-100.9, -26.2]; August A -4.0 [-57.8, +66.1]; August B -58.0 [-161.5, -2.8]; four-scenario -52.5 [-102.6, -11.8]; September pair +153.3; first confirmatory -104.2 |

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
