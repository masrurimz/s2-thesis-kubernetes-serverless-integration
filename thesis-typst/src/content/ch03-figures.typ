// ============================================================================
// Chapter 3 figures — native Typst diagrams (cetz 0.4.0).
//
//   fig-research-flow  : six-phase methodology flow with the proposal's
//                        decision gate ("Hasil Memuaskan ?") and the dashed
//                        No-loop from Evaluation back to Method Design.
//   fig-control-loop   : C4-container module diagram of the hybrid system
//                        (split K3s / Knative backends, orthogonal lanes,
//                        zero arrow crossings).
//
// These are callable helpers; the chapter file wraps each in `#figure(...)`.
// ============================================================================
#import "@preview/cetz:0.4.0"
#import "headings.typ": cap

// Shared palette (matches the ch03 prose styling).
#let border = rgb("#5a6b80")
#let lbl    = rgb("#5f6b7a")
#let techc  = rgb("#3a4a5a")
#let flow-fill = rgb("#eef2f7")

// ---------------------------------------------------------------------------
// fig-research-flow — six-phase vertical methodology flow with iteration gate.
//
// Faithful to the proposal's "Alur penelitian tesis" (Gambar 3.1): the
// evaluation phase ends in a decision diamond ("Hasil Memuaskan ?" /
// results satisfactory?); "Yes" proceeds to conclusion, "No" loops back
// (dashed, right-hand lane) into Method Design.
// ---------------------------------------------------------------------------
#let fig-research-flow() = cetz.canvas(length: 1cm, {
  let native-polygon = polygon
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
  let tag((x, y), body) = content((x, y), text(size: 6pt, fill: lbl)[#body])

  // Phases (0.525 = half box height).
  phase((0, 10.6), cap([Literature Study], [Studi Literatur]), cap([cloud, workload prediction, elastic scaling], [_cloud_, prediksi beban kerja, penskalaan elastis]))
  phase((0, 8.9), cap([Data Collection], [Pengumpulan Data]), cap([synthetic patterns + real HTTP traces], [pola sintetis + _trace_ HTTP nyata]))
  phase((0, 7.2), cap([Method Design], [Perancangan Metode]), cap([hybrid architecture, routing + scaling algorithms], [arsitektur _hybrid_, algoritma perutean + penskalaan]))
  phase((0, 5.5), cap([Implementation], [Implementasi]), cap([GRU server, controllers, monitoring, routing layer], [server GRU, pengendali, pemantauan, lapisan perutean]))
  phase((0, 3.8), cap([Evaluation], [Evaluasi]), cap([scenarios S1–S4, paired comparison], [skenario S1–S4, perbandingan berpasangan]))
  phase((0, 0.4), cap([Conclusion], [Kesimpulan]), cap([findings and contributions], [temuan dan kontribusi]))

  // Decision gate (proposal: "Hasil Memuaskan ?" / results satisfactory?).
  line(
    (-1.35, 2.1), (0, 2.65), (1.35, 2.1), (0, 1.55),
    close: true,
    fill: flow-fill,
    stroke: 0.7pt + border,
  )
  content((0, 2.1), text(size: 6pt)[#align(center)[#cap([Results\ satisfactory?], [Hasil\ memuaskan?])]])

  // Linear spine.
  arrow((0, 10.075), (0, 9.425))
  arrow((0, 8.375), (0, 7.725))
  arrow((0, 6.675), (0, 6.025))
  arrow((0, 4.975), (0, 4.325))
  arrow((0, 3.275), (0, 2.65))
  arrow((0, 1.55), (0, 0.925))
  tag((0.5, 1.24), cap([Yes], [Ya]))

  // Feedback loop (proposal: "Tidak") — Evaluation gate back to Method Design.
  line(
    (1.28, 2.1), (4.3, 2.1), (4.3, 7.2), (3.3, 7.2),
    mark: (end: ">"),
    stroke: (paint: border, thickness: 0.8pt, dash: "dashed"),
  )
  tag((1.85, 2.42), cap([No], [Tidak]))
  tag((5.3, 4.6), cap([revise\ design], [revisi\ rancangan]))
})

// ---------------------------------------------------------------------------
// fig-control-loop — C4-container module diagram of the hybrid system.
//
// Zones: data plane on the left (Clients -> HAProxy -> Knative/K3s backends),
// control plane on the top-right (Monitoring, GRU, Routing Daemon).
// All edges are orthogonal lanes; no two arrows cross:
//   Clients -> HAProxy                      (HTTP load)
//   HAProxy -> Knative Backend              (w: knative %)
//   HAProxy -> K3s Backend                  (w: k3s %)
//   HAProxy -> Monitoring                   (stats scrape, vertical)
//   Monitoring -> Routing Daemon            (p99, violation window)
//   GRU -> Routing Daemon                   (forecast + confidence)
//   Routing Daemon -> HAProxy               (Runtime API: weights)
//   Routing Daemon -> K3s Backend           (kubectl scale)
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
  let lane(pts) = line(..pts, mark: (end: ">"), stroke: 0.8pt + border)
  let tag((x, y), body) = content((x, y), text(size: 6pt, fill: lbl)[#body])

  // Fill palette (C4-style: external / ingress / control / prediction / infra / observability).
  let c-ext   = rgb("#e8edf4")  // clients (external)
  let c-ing   = rgb("#dbe9f7")  // HAProxy (ingress)
  let c-ctl   = rgb("#e2f0e2")  // routing daemon (control)
  let c-prd   = rgb("#fbf3e0")  // GRU server (prediction)
  let c-inf   = rgb("#ece7f5")  // backends (infra)
  let c-obs   = rgb("#f0f0f0")  // monitoring

  // --- data plane (left) ---------------------------------------------------
  // (center x, center y, width, height, title, tech, description, fill)
  container((1.5, 7.2), 2.9cm, 1.5cm, cap([Clients / Load], [Klien / Beban]), cap([k6 workload generator], [pembangkit beban kerja k6]), cap([synthetic + ClarkNet traces], [_trace_ sintetis + ClarkNet]), c-ext)
  container((6.0, 7.2), 3.6cm, 1.5cm, [HAProxy], cap([ingress, weighted routing], [_ingress_, perutean berbobot]), cap([Runtime API + stats endpoint], [Runtime API + _endpoint_ statistik]), c-ing)
  // Simulated platform separation — both backends run on ONE physical k3d
  // testbed but are logically isolated and operated as independent platforms.
  // Dashed container drawn BEHIND the boxes (with a margin) so the two
  // backends sit inside one region; incoming arrows pass over the dashed
  // edge naturally, keeping the diagram planar with zero arrow crossings.
  line(
    (2.5, 1.9), (11.5, 1.9), (11.5, 4.5), (2.5, 4.5), (2.5, 1.9),
    close: true,
    stroke: (paint: lbl, thickness: 0.7pt, dash: "dashed"),
  )
  container((4.8, 3.2), 3.8cm, 1.6cm, cap([Knative Backend], [_Backend_ Knative]), [Knative + Kourier], cap([scale-to-zero serverless], [_serverless_ dengan _scale-to-zero_]), c-inf)
  container((9.2, 3.2), 3.8cm, 1.6cm, cap([K3s Backend], [_Backend_ K3s]), cap([K3s via k3d], [K3s melalui k3d]), cap([always-warm pods], [_pod_ selalu hangat]), c-inf)
  tag((7.0, 1.35), cap([simulated platform separation\
    (shared physical testbed)], [pemisahan platform tersimulasi\
    (_testbed_ fisik bersama)]))

  // --- control plane (top-right) --------------------------------------------
  container((6.0, 9.8), 3.2cm, 1.5cm, cap([Monitoring], [Pemantauan]), cap([Prometheus + SLO monitor], [Prometheus + pemantau SLO]), cap([p99, violation window], [p99, jendela pelanggaran]), c-obs)
  container((13.2, 7.2), 4.4cm, 2.4cm, cap([Routing Daemon], [Daemon Perutean]), cap([Algorithm 1 routing + Algorithm 2 scaling], [Perutean Algoritma 1 + penskalaan Algoritma 2]), cap([15 s control loop], [_control loop_ 15 s]), c-ctl)
  container((13.2, 10.6), 4.0cm, 1.5cm, cap([GRU Prediction Server], [Server Prediksi GRU]), [FastAPI :8090], cap([9-step forecast + confidence], [prakiraan 9 langkah + keyakinan]), c-prd)

  // --- data-plane edges (orthogonal lanes) ----------------------------------
  arrow((2.95, 7.2), (4.2, 7.2))
  tag((3.58, 7.5), cap([HTTP load], [beban HTTP]))

  arrow((5.0, 6.45), (5.0, 4.0))
  tag((3.35, 5.2), [w: knative %])

  arrow((7.5, 6.45), (7.5, 4.0))
  tag((8.15, 5.2), [w: k3s %])

  // --- observability edge (short + vertical) ---------------------------------
  arrow((6.0, 7.95), (6.0, 9.05))
  tag((6.85, 8.5), cap([stats scrape (1 s)], [pengambilan statistik (1 s)]))

  // --- control-plane reads ----------------------------------------------------
  lane(((7.6, 9.3), (11.7, 9.3), (11.7, 8.4)))
  tag((9.6, 9.0), cap([p99, violation window], [p99, jendela pelanggaran]))

  arrow((13.2, 9.85), (13.2, 8.4))
  tag((14.0, 9.1), cap([forecast +\ confidence], [prakiraan +\ keyakinan]))
  // --- control-plane writes ---------------------------------------------------
  arrow((11.0, 7.2), (7.8, 7.2))
  tag((9.4, 7.5), cap([Runtime API: weights], [Runtime API: bobot]))

  lane(((13.2, 6.0), (13.2, 3.2), (11.1, 3.2)))
  tag((13.95, 4.6), [kubectl scale])
})
