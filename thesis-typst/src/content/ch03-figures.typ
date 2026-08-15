// ============================================================================
// Chapter 3 figures — native Typst diagrams (cetz 0.4.0).
//
//   fig-research-flow  : six-phase methodology flow (vertical).
//   fig-control-loop   : C4-container module diagram of the hybrid system.
//
// These are callable helpers; the chapter file wraps each in `#figure(...)`.
// ============================================================================
#import "@preview/cetz:0.4.0"

// Shared palette (matches the ch03 prose styling).
#let border = rgb("#5a6b80")
#let lbl    = rgb("#5f6b7a")
#let techc  = rgb("#3a4a5a")
#let flow-fill = rgb("#eef2f7")

// ---------------------------------------------------------------------------
// fig-research-flow — six-phase vertical methodology flow.
// ---------------------------------------------------------------------------
#let fig-research-flow() = cetz.canvas(length: 1cm, {
  import cetz.draw: *

  let phase((x, y), title, sub) = content(
    (x, y),
    box(
      width: 6.6cm,
      height: 1.05cm,
      stroke: 0.7pt + border,
      fill: flow-fill,
      inset: 3pt,
      align(center + horizon, [
        *#title* \
        #text(size: 6pt, fill: lbl)[#sub]
      ]),
    ),
  )

  let arrow(a, b) = line(a, b, mark: (end: ">"), stroke: 0.8pt + border)

  phase((0, 9.4), [Literature Study], [cloud, workload prediction, elastic scaling])
  phase((0, 7.6), [Data Collection], [synthetic patterns + real HTTP traces])
  phase((0, 5.8), [Method Design], [hybrid architecture, routing + scaling algorithms])
  phase((0, 4.0), [Implementation], [GRU server, controllers, monitoring, routing layer])
  phase((0, 2.2), [Evaluation], [scenarios S1–S4, paired comparison])
  phase((0, 0.4), [Conclusion], [findings and contributions])

  // 0.525 = half box height.
  arrow((0, 8.875), (0, 8.125))
  arrow((0, 7.075), (0, 6.325))
  arrow((0, 5.275), (0, 4.525))
  arrow((0, 3.475), (0, 2.725))
  arrow((0, 1.675), (0, 0.925))
})

// ---------------------------------------------------------------------------
// fig-control-loop — C4-container module diagram of the hybrid system.
//
// Left column  = data plane:  Clients → HAProxy → K8s backend.
// Right column = control plane: GRU → Daemon ← Monitoring; Daemon → HAProxy/K8s.
// ---------------------------------------------------------------------------
#let fig-control-loop() = cetz.canvas(length: 1cm, {
  import cetz.draw: *

  let container((x, y), w, h, title, tech, desc, fill) = content(
    (x, y),
    box(
      width: w,
      height: h,
      stroke: 0.8pt + border,
      fill: fill,
      inset: 3pt,
      align(center + horizon, [
        #text(size: 7pt, weight: "bold")[#title] \
        #text(size: 5.5pt, fill: techc)[#tech] \
        #text(size: 5.5pt)[#desc]
      ]),
    ),
  )

  let arrow(a, b) = line(a, b, mark: (end: ">"), stroke: 0.8pt + border)
  let tag((x, y), body) = content((x, y), text(size: 6pt, fill: lbl)[#body])

  // Fill palette (C4-style: external / ingress / control / prediction / infra / observability).
  let c-ext   = rgb("#e8edf4")  // clients (external)
  let c-ing   = rgb("#dbe9f7")  // HAProxy (ingress)
  let c-ctl   = rgb("#e2f0e2")  // routing daemon (control)
  let c-prd   = rgb("#fbf3e0")  // GRU server (prediction)
  let c-inf   = rgb("#ece7f5")  // K8s backend (infra)
  let c-obs   = rgb("#f0f0f0")  // monitoring

  // --- containers ----------------------------------------------------------
  // (center x, center y, width, height, title, tech, description, fill)
  container((2.6, 9.0), 4.4cm, 1.7cm, [Clients / Load], [k6 workload generator], [synthetic + ClarkNet traces], c-ext)
  container((2.6, 5.6), 4.4cm, 1.7cm, [HAProxy], [ingress, weighted routing], [Runtime API + stats endpoint], c-ing)
  container((2.6, 1.0), 4.6cm, 2.3cm, [K8s Backend], [K3s + Knative (Kourier)], [always-warm pods, scale-to-zero serverless], c-inf)
  container((10.2, 8.8), 4.6cm, 1.7cm, [GRU Prediction Server], [FastAPI :8090], [9-step forecast + confidence], c-prd)
  container((10.2, 4.6), 4.8cm, 2.4cm, [Routing Daemon], [Algorithm 1 routing + Algorithm 2 scaling], [15 s control loop], c-ctl)
  container((10.2, 1.0), 4.6cm, 1.9cm, [Monitoring], [Prometheus + SLO monitor], [p99, violation window], c-obs)

  // --- data plane ----------------------------------------------------------
  arrow((2.6, 8.15), (2.6, 6.45))
  tag((3.05, 7.3), [HTTP load])

  arrow((2.6, 4.75), (2.6, 2.15))
  tag((3.0, 3.45), [weighted routing\ k3s / knative])

  // --- control plane: reads ------------------------------------------------
  arrow((10.2, 7.95), (10.2, 5.8))
  tag((10.75, 6.9), [forecast +\ confidence])

  arrow((10.2, 1.95), (10.2, 3.4))
  tag((10.75, 2.6), [p99, violation\ window])

  // --- control plane: writes -----------------------------------------------
  arrow((7.8, 5.1), (4.8, 5.6))
  tag((6.3, 5.85), [Runtime API: weights])

  arrow((8.0, 3.4), (4.6, 2.15))
  tag((7.05, 2.35), [kubectl scale])

  // --- observability: HAProxy exposes stats to Monitoring ------------------
  arrow((4.8, 5.0), (7.9, 1.7))
  tag((5.6, 3.5), [stats scrape (1 s)])
})
