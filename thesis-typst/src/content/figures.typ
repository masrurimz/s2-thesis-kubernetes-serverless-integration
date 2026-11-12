// ============================================================================
// Chapter 4 figures — native Typst charts (primaviz 0.9.1).
//
// Five figures are rendered natively here so they re-render at compile time.
// One figure — the H2 effect-size forest plot — has no primaviz primitive and
// is generated as a matplotlib PNG in ``../figures/`` (see
// ``apps/analysis/analysis_cli/thesis_figures.py``).
//
// Single charting system: primaviz (zero deps, native primitives). Import:
//   #import "@preview/primaviz:0.9.1": *
//
// primaviz functions used here (exact names):
//   bar-chart            — single-series vertical bars + h-line annotation
//   grouped-bar-chart    — multi-series side-by-side bars (legend)
//   line-chart           — single-series line + v-line annotation
//   box-plot             — five-number box + native `outliers` field + point/h-line annotations
// Annotation descriptor shapes used:
//   (type: "h-line", value: <y>, dash: "dashed", color: <c>, label: [..])
//   (type: "v-line", value: <x>, dash: "dashed", color: <c>, label: [..])
//   (type: "point", x: <x>, y: <y>, radius: <len>, fill: <c>)
//
// Every number below is read from the real experiment bundles — do not edit
// without re-sourcing:
//   - Cost (n=1):       results/claims/FINAL_NUMBERS.md
//   - Paired per-pair:  results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/paired_analysis.json
//   - SLO violations:   2026-08-09_clarknet-replay_032257/*/result.json (mean per run, n=5 per scenario)
//   - Node timeline:    2026-07-14_clarknet-tuned-paired-n5/s3-hybrid-reactive_run1/{node_utilization,provision_events}.json
//   - p99 boxplot:      2026-08-09_clarknet-replay_032257/*/result.json (n=5)
// ============================================================================
#import "@preview/primaviz:0.9.1": *
#import "headings.typ": cap

// Scenario palette (matches shared.scenarios SCENARIO_COLORS).
#let s1 = rgb("#4C72B0")
#let s2 = rgb("#DD8452")
#let s3 = rgb("#55A868")
#let s4 = rgb("#C44E52")
#let slo = rgb("#d62728")
#let evt-up = rgb("#2ca02c")

// ---------------------------------------------------------------------------
// fig04_5 — Monthly cost comparison (n=1 directional diagnostic).
// Bars S1/S2/S3/S4.
// ---------------------------------------------------------------------------
#let fig-cost-comparison() = bar-chart(
  ((cap("S1: K8s Only", "S1: hanya K8s"), 132), (cap("S2: Serverless Only", "S2: hanya serverless"), 395), (cap("S3: Hybrid Reactive", "S3: hybrid reaktif"), 147), (cap("S4: Hybrid Predictive", "S4: hybrid prediktif"), 143)),
  width: 420pt,
  height: 260pt,
  bar-width: 0.62,
  title: cap([Monthly cost by scenario], [Biaya bulanan per skenario]),
  subtitle: cap([Directional diagnostic estimate (n=1)], [Perkiraan diagnostik arah (n=1)]),
  x-label: cap([Scenario], [Skenario]),
  theme: (palette: (s1, s2, s3, s4)),
)

// ---------------------------------------------------------------------------
// fig04_1 — Per-pair p99 for the July paired H2 batch (n=5, history).
// Clustered bars S3 vs S4 for the 5 pairs; dashed SLO line at 200 ms.
// ---------------------------------------------------------------------------
#let fig-paired-perpair() = grouped-bar-chart(
  (
    labels: ("P1", "P2", "P3", "P4", "P5"),
    series: (
      (name: cap("S3 Reactive", "S3 Reaktif"), values: (235.6, 192.2, 151.4, 164.0, 199.2)),
      (name: cap("S4 Predictive", "S4 Prediktif"), values: (101.4, 104.9, 100.5, 155.7, 167.4)),
    ),
  ),
  width: 440pt,
  height: 280pt,
  x-label: cap([Pair], [Pasangan]),
  y-label: cap([p99 latency (ms)], [Latensi p99 (ms)]),
  theme: (palette: (s3, s4)),
  annotations: (
    (type: "h-line", value: 200, dash: "dashed", color: slo, label: [SLO 200 ms]),
  ),
)

// ---------------------------------------------------------------------------
// fig04_3 — Mean SLO violations per run for the four scenarios of the
// four-scenario replication (n=5 runs each): 50.6, 0.4, 399.6, 18.4.
// ---------------------------------------------------------------------------
#let fig-slo-violations() = bar-chart(
  ((cap("S1: K8s Only", "S1: hanya K8s"), 50.6), (cap("S2: Serverless Only", "S2: hanya serverless"), 0.4), (cap("S3: Hybrid Reactive", "S3: hybrid reaktif"), 399.6), (cap("S4: Hybrid Predictive", "S4: hybrid prediktif"), 18.4)),
  width: 420pt,
  height: 260pt,
  bar-width: 0.62,
  x-label: cap([Scenario], [Skenario]),
  y-label: cap([SLO violations per run (mean)], [Pelanggaran SLO per run (rata-rata)]),
  theme: (palette: (s1, s2, s3, s4)),
)

// ---------------------------------------------------------------------------
// fig04_4 — Node provisioning timeline (July paired S3 run 1).
// Total node CPU% over time (13 sample points, ~104 s apart) with vertical
// markers for every autoscaler lifecycle event. Two provisioning cycles:
//   pending_detected -> provision_delay_started -> node_created (x2), then
//   scale_down_detected -> node_deleted (x2) as load falls.
// ---------------------------------------------------------------------------
#let fig-node-provisioning() = line-chart(
  ((0, 6.0), (104, 59.4), (209, 63.3), (314, 125.8), (418, 100.7), (522, 115.4),
   (627, 177.1), (732, 115.2), (836, 71.3), (940, 108.1), (1045, 68.7), (1150, 67.6), (1254, 6.0)),
  width: 460pt,
  height: 280pt,
  show-points: true,
  show-values: false,
  x-label: cap([Time (s)], [Waktu (s)]),
  y-label: cap([Total node CPU (%)], [Total CPU node (%)]),
  theme: (palette: (s3,)),
  annotations: (
    // Cycle 1: pending -> delay -> node_created (t = ts - t_start, t_start = 1783967907.923196)
    (type: "v-line", value: 317.7, dash: "dotted", color: rgb("#7f7f7f"), label: [pending_detected]),
    (type: "v-line", value: 317.7, dash: "dashed", color: rgb("#ff7f0e")),
    (type: "v-line", value: 394.4, dash: "dashed", color: evt-up, label: [node_created]),
    // Cycle 2: pending -> delay -> node_created
    (type: "v-line", value: 576.9, dash: "dotted", color: rgb("#7f7f7f")),
    (type: "v-line", value: 576.9, dash: "dashed", color: rgb("#ff7f0e")),
    (type: "v-line", value: 669.5, dash: "dashed", color: evt-up),
    // Scale-down: detected -> deleted
    (type: "v-line", value: 762.2, dash: "dash-dotted", color: slo, label: [scale_down_detected]),
    (type: "v-line", value: 763.7, dash: "dotted", color: rgb("#9467bd"), label: [node_deleted]),
    (type: "v-line", value: 1229.5, dash: "dash-dotted", color: slo),
    (type: "v-line", value: 1231.0, dash: "dotted", color: rgb("#9467bd")),
  ),
)

// ---------------------------------------------------------------------------
// fig04_2 — Per-scenario p99 boxplot (n=5 four-scenario replication).
// Tukey five-number summary + native outlier dots + all 20 run points + SLO.
// ---------------------------------------------------------------------------
#let fig-p99-boxplot() = box-plot(
  (
    labels: (cap("S1: K8s Only", "S1: hanya K8s"), cap("S2: Serverless Only", "S2: hanya serverless"), cap("S3: Hybrid Reactive", "S3: hybrid reaktif"), cap("S4: Hybrid Predictive", "S4: hybrid prediktif")),
    boxes: (
      (min: 98.76, q1: 107.47, median: 112.69, q3: 115.18, max: 117.47),
      (min: 77.98, q1: 78.75, median: 79.02, q3: 79.41, max: 79.41, outliers: (83.42,)),
      (min: 103.45, q1: 109.47, median: 151.62, q3: 153.92, max: 153.92, outliers: (239.43,)),
      (min: 88.17, q1: 88.90, median: 93.76, q3: 94.39, max: 94.39, outliers: (130.17,)),
    ),
  ),
  width: 460pt,
  height: 300pt,
  x-label: cap([Scenario], [Skenario]),
  y-label: cap([p99 latency (ms)], [Latensi p99 (ms)]),
  box-width: 0.5,
  theme: (palette: (s1, s2, s3, s4)),
  annotations: (
    (type: "h-line", value: 200, dash: "dashed", color: slo, label: [SLO 200 ms]),
    // S1 run points (x = 0, jittered)
    (type: "point", x: -0.16, y: 117.47, radius: 2.5pt, fill: s1),
    (type: "point", x: -0.08, y: 98.76, radius: 2.5pt, fill: s1),
    (type: "point", x: 0.00, y: 115.18, radius: 2.5pt, fill: s1),
    (type: "point", x: 0.08, y: 107.47, radius: 2.5pt, fill: s1),
    (type: "point", x: 0.16, y: 112.69, radius: 2.5pt, fill: s1),
    // S2 run points (x = 1)
    (type: "point", x: 0.84, y: 77.98, radius: 2.5pt, fill: s2),
    (type: "point", x: 0.92, y: 78.75, radius: 2.5pt, fill: s2),
    (type: "point", x: 1.00, y: 83.42, radius: 2.5pt, fill: s2),
    (type: "point", x: 1.08, y: 79.02, radius: 2.5pt, fill: s2),
    (type: "point", x: 1.16, y: 79.41, radius: 2.5pt, fill: s2),
    // S3 run points (x = 2)
    (type: "point", x: 1.84, y: 239.43, radius: 2.5pt, fill: s3),
    (type: "point", x: 1.92, y: 151.62, radius: 2.5pt, fill: s3),
    (type: "point", x: 2.00, y: 103.45, radius: 2.5pt, fill: s3),
    (type: "point", x: 2.08, y: 153.92, radius: 2.5pt, fill: s3),
    (type: "point", x: 2.16, y: 109.47, radius: 2.5pt, fill: s3),
    // S4 run points (x = 3)
    (type: "point", x: 2.84, y: 88.90, radius: 2.5pt, fill: s4),
    (type: "point", x: 2.92, y: 130.17, radius: 2.5pt, fill: s4),
    (type: "point", x: 3.00, y: 88.17, radius: 2.5pt, fill: s4),
    (type: "point", x: 3.08, y: 94.39, radius: 2.5pt, fill: s4),
    (type: "point", x: 3.16, y: 93.76, radius: 2.5pt, fill: s4),
  ),
)
