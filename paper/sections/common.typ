// Facts shared by the conference and journal papers: numbers, tables, figures,
// algorithms. Prose lives in body.typ. Every number comes from numbers.json,
// which derive_numbers.py builds from the bundles.
#import "@preview/cetz:0.4.0"
#import "@preview/lovelace:0.3.0": pseudocode-list

#let N = json("../numbers.json")
#let F = N.four
#let H = N.h2
#let G = N.gru

#let rule = table.hline(stroke: 0.5pt)
#let toprule = table.hline(stroke: 0.8pt)

// ---------------------------------------------------------------------------
// Fig. 1: control architecture. The forecast arrow reaches Algorithm 2 only.
#let fig-architecture = figure(
  cetz.canvas(length: 1cm, {
    import cetz.draw: *
    set-style(stroke: 0.6pt, mark: (fill: black, scale: 0.5))
    let node(a, b, name, body, fill: white) = {
      rect(a, b, name: name, fill: fill, radius: 2pt)
      content(name, align(center, text(size: 6.5pt, body)))
    }
    let lab(pos, body, anchor: "south") = content(pos, text(size: 6pt, style: "italic", body), anchor: anchor, padding: 1.5pt)
    let arrow(..pts) = line(..pts, mark: (end: ">"))

    node((0, 4.5), (1.6, 5.3), "load", [*Load gen.* \ k6 replay])
    node((2.1, 4.5), (3.7, 5.3), "lb", [*HAProxy*], fill: luma(240))
    node((2.1, 3.0), (3.7, 3.8), "prom", [*Prometheus*])
    node((4.6, 5.1), (8.0, 5.9), "kn", [*Knative* \ 3–10 warm pods])
    node((4.6, 3.9), (8.0, 4.7), "k8s", [*Kubernetes* \ 3–10 pods])
    node((5.45, 2.5), (8.0, 3.5), "nodes", [*Node autoscaler* \ new node after 45–120 s])
    rect((0, 0), (5.6, 2.3), stroke: (dash: "dashed"), radius: 2pt)
    content((0.95, 2.22), text(size: 6pt, [control daemon, every 15 s]), anchor: "north-west")
    node((0.15, 0.15), (2.75, 1.75), "alg1", [*Algorithm 1: router* \ weights from load $x$ \ and ready pods $n$])
    node((2.95, 0.15), (5.45, 1.75), "alg2", [*Algorithm 2: scaler* \ pods $R(x)$, or \ $R(max_k hat(u)_(t+k))$ \ if larger])
    node((6.0, 0.3), (8.0, 1.1), "gru", [*GRU forecaster* \ 9 steps $times$ 15 s], fill: luma(240))

    arrow("load.east", "lb.west")
    arrow((3.7, 5.05), (4.6, 5.5))
    lab((4.15, 5.3), $w_"sls"$, anchor: "south-east")
    arrow((3.7, 4.75), (4.6, 4.3))
    lab((4.15, 4.5), $w_"k8s"$, anchor: "north-east")
    arrow("lb.south", "prom.north")
    lab((2.9, 4.15), [metrics], anchor: "west")
    arrow("prom.south", (2.9, 2.3))
    lab((2.9, 2.65), [load $x$, p99], anchor: "west")
    arrow((0.8, 1.75), (0.8, 4.1), (2.4, 4.1), (2.4, 4.5))
    lab((0.8, 3.0), [weights], anchor: "west")
    arrow((5.0, 3.9), (5.0, 2.3))
    lab((5.0, 3.1), [ready pods $n$], anchor: "east")
    arrow("nodes.north", (6.8, 3.9))
    arrow((5.45, 1.5), (8.3, 1.5), (8.3, 4.3), (8.0, 4.3))
    lab((6.9, 1.5), [replica count])
    arrow("gru.west", (5.45, 0.7))
    lab((5.72, 0.7), $hat(u)$)
  }),
  placement: auto,
  caption: [Control architecture. Only the predictive hybrid uses the forecast $hat(u)$.],
)

// A note under a table, in the last row. Captions stay titles; a remark about one cell goes here.
#let tnote(columns, body) = table.cell(
  colspan: columns,
  align: left,
  inset: (x: 3pt, top: 3pt, bottom: 0pt),
  text(size: 7pt, body),
)

// ---------------------------------------------------------------------------
// Algorithms.
#let alg-routing = figure(
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [Capacity-aware router, every 15 s],
  align(start, text(size: 8pt, pseudocode-list(booktabs: true, numbered-title: none)[
    + *input:* load $x$ (RPS), ready pods $n$
    + $C <- n dot r_"eff"$ #h(1fr) ▷ load the ready pods can serve
    + *if* $x <= C$ *then* $w_"sls" <- 0$ #h(1fr) ▷ all to Kubernetes
    + *else* $w_"sls" <- min(50, ceil(100 (x - C) \/ x))$ #h(1fr) ▷ excess share, in %
    + set HAProxy weights $(w_"k8s", w_"sls") <- (100 - w_"sls", w_"sls")$
  ])),
  placement: auto,
)

#let alg-scaling = figure(
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [ElaX-derived replica scaler, every 15 s],
  align(start, text(size: 8pt, pseudocode-list(booktabs: true, numbered-title: none)[
    + *input:* mean load $x_"obs"$ over the last 30 s, current pods $r$, p99; \ predictive hybrid also: envelope $hat(u)_(t+1), dots, hat(u)_(t+9)$
    + $R(v) := "clamp"(ceil(v \/ r_"eff"), 3, 10)$ #h(1fr) ▷ pods for load $v$
    + $T <- R(x_"obs")$ #h(1fr) ▷ observed-load target
    + *if* predictive hybrid *then*
      + *if* $R(max_k hat(u)_(t+k)) > T$ *then* $T <- R(max_k hat(u)_(t+k))$, kept for 90 s
      + *else if* a kept target is above $T$ *then* $T <-$ kept target
    + *if* $T > r$ *then* scale up to $T$
    + *else if* $T < 0.75 r$ *and* p99 $< 140$ ms *and* 120 s since the last scale-down *then* scale down to $T$
  ])),
  placement: auto,
)

// ---------------------------------------------------------------------------
// Tables.
#let tab-elax = figure(
  table(
    columns: (auto, 1fr, 1fr),
    align: (left, left, left),
    stroke: none,
    inset: (x: 3pt, y: 2pt),
    toprule,
    [], [*ElaX* @yang2019elax], [*Algorithm 2*],
    rule,
    [Predictor], [LSTM, denoised series], [GRU, one 9-step head],
    [Horizon], [60 × 1 min], [9 × 15 s (135 s)],
    [Refresh], [hourly; retrained daily], [every 15 s],
    [Decision factor#super[a]], [top point forecast], [top upper envelope],
    [Resource model], [$R = sigma y + beta$, profiled], [$R = ceil(v \/ r_"eff")$, measured],
    [Feedback], [slack controller, 2 s], [cooldowns, p99 guard],
    [Scaling], [horizontal, vertical], [horizontal, node tier],
    [Scope], [one cluster], [Kubernetes + Knative],
    toprule,
    tnote(3)[#super[a]The load value the replica count is computed from.],
  ),
  placement: auto,
  caption: [Algorithm 2 compared with ElaX],
) 

#let tab-batches = figure(
  table(
    columns: (auto, auto, auto, 1fr),
    align: (left, left, left, left),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [*Batch*], [*Size*], [*Host CPU busy*], [*Role*],
    rule,
    [Scenario], [5 runs × 3], [–], [hybrid vs. baselines#super[a]],
    [Pilot], [5 pairs], [not logged], [first paired test],
    [Loaded host], [10 pairs], [mean ≤ #H.b10a.busy_avg_max], [paired test with more power],
    [Confirmatory], [10 pairs], [mean #H.b10b.busy_avg_min–#H.b10b.busy_avg_max], [repeat on a quieter host],
    [Earlier], [5 pairs], [–], [favored the forecast; left out#super[a]],
    toprule,
    tnote(4)[#super[a]Predictive-hybrid runs left out: their records do not identify the forecaster.],
  ),
  placement: auto,
  caption: [Batches of runs],
)

#let tab-predictor = figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, right, right, right),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [*Model (same 30-sample windows)*], [*RMSE*], [*MAE*], [*Skill*],
    rule,
    [GRU, 2 × #G.hidden (3 seeds)], [#G.gru.rmse ± #G.gru.rmse_sd], [#G.gru.mae], [#G.gru.skill],
    [LSTM (3 seeds)], [#G.lstm.rmse ± #G.lstm.rmse_sd], [#G.lstm.mae], [#G.lstm.skill],
    [Linear autoregression], [#G.ols_rmse], [#G.ols_mae], [#G.ols_skill],
    [Persistence], [#G.persistence], [–], [0],
    [Linear trend], [#G.trend], [–], [#G.trend_skill],
    [Seasonal naive (one day)], [#G.seasonal], [–], [#G.seasonal_skill],
    toprule,
  ),
  caption: [Forecast error on the ClarkNet test portion],
)

// A strip plot inside a table cell: values on a fixed axis [lo, hi], a dashed reference line at ref,
// and either dots (one per run) or an interval with its mean.
#let strip(lo, hi, ref, body, w: 2.6) = box(baseline: 20%, cetz.canvas(length: 1cm, {
  import cetz.draw: *
  set-style(stroke: 0.5pt)
  let sx(v) = (v - lo) / (hi - lo) * w
  rect((0, -0.09), (w, 0.09), stroke: none)
  line((sx(ref), -0.11), (sx(ref), 0.11), stroke: (dash: "densely-dashed", paint: luma(120)))
  body(sx)
}))
#let strip-axis(lo, hi, ticks, w: 2.6) = box(cetz.canvas(length: 1cm, {
  import cetz.draw: *
  set-style(stroke: 0.5pt)
  let sx(v) = (v - lo) / (hi - lo) * w
  line((0, 0), (w, 0))
  for t in ticks {
    line((sx(t), 0), (sx(t), -0.05))
    content((sx(t), -0.07), text(size: 6pt, str(t).replace("-", "−")), anchor: "north")
  }
}))
#let runs-strip(plot) = strip(0, 300, 200, w: 3.0, sx => {
  import cetz.draw: *
  for v in plot { circle((sx(v), 0), radius: 0.045, fill: white, stroke: 0.45pt) }
})
#let ci-w = 6.0
#let ci-strip(v, bold: false) = strip(-700, 1100, 0, w: ci-w, sx => {
  import cetz.draw: *
  line((sx(v.at(1)), 0), (sx(v.at(2)), 0), stroke: 0.9pt)
  let s = if bold { 0.075 } else { 0.05 }
  rect((sx(v.at(0)) - s, -s), (sx(v.at(0)) + s, s), fill: black, stroke: none)
})

#let tab-four = figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto),
    align: (left, left, left, right, center, right, right, right, right),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [*Scenario*], [*Pod scaling*], [*Traffic*], [*p99 (ms)*], [*p99 per run*#super[a]], [*SLO viol.*#super[b]],
    [*Serverless*], [*K8s pod-s*], [*USD/mo*],
    rule,
    [HPA baseline], [HPA at 50% CPU, 1–10 pods], [Kubernetes], [#F.s1.p99 ± #F.s1.p99_sd], runs-strip(F.s1.plot),
    [#F.s1.slo], [#F.s1.share%], [#F.s1.replica_s], [#F.s1.cost],
    [Knative baseline], [Knative KPA, 3–10 pods], [Knative], [#F.s2.p99 ± #F.s2.p99_sd],
    runs-strip(F.s2.plot), [#F.s2.slo], [#F.s2.share%], [#F.s2.replica_s], [#F.s2.cost],
    [Reactive hybrid], [Alg. 2 on the observed load], [Alg. 1], [#F.s3.p99 ± #F.s3.p99_sd], runs-strip(F.s3.plot),
    [#F.s3.slo], [#F.s3.share%], [#F.s3.replica_s], [#F.s3.cost],
    [Predictive hybrid], [Alg. 2 on load + forecast], [Alg. 1],
    table.cell(colspan: 6, align: left)[paired with the reactive hybrid only (@tab:h2)],
    rule,
    [], [], [], [], strip-axis(0, 300, (0, 100, 200, 300), w: 3.0), [], [], [], [],
    tnote(9)[#super[a]One dot per run of the scenario batch; dashed line: the 200~ms SLO.
      #super[b]Requests over 200~ms per run.],
  ),
  placement: auto,
  scope: "parent",
  caption: [Scenarios, and the scenario batch: means over five runs per scenario],
)

#let h2row(label, b) = (
  label, [#b.s3], [#b.s4], [#b.diff \[#b.ci_lo, #b.ci_hi\]], ci-strip(b.plot), [#b.p], [#b.d], [#b.wins/#b.n],
)

#let tab-h2 = figure(
  table(
    columns: (auto, auto, auto, auto, 1fr, auto, auto, auto),
    align: (left, right, right, right, center, right, right, right),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [*Batch*], [*Reactive*], [*Predictive*], [*Difference \[95% CI\]*#super[a]], [*Interval*#super[b]], [*p*],
    [*d*], [*Wins*#super[c]],
    rule,
    ..h2row([Pilot], H.b5),
    ..h2row([Loaded host], H.b10a),
    ..h2row([Confirmatory], H.b10b),
    rule,
    [Pooled], [–], [–], [#H.pooled.diff \[#H.pooled.ci_lo, #H.pooled.ci_hi\]], ci-strip(H.pooled.plot, bold: true),
    [#H.pooled.p#super[d]], [#H.pooled.d], [#H.pooled.wins/#H.pooled.n],
    rule,
    [], [], [], [], strip-axis(-700, 1100, (-500, 0, 500, 1000), w: ci-w), [], [], [],
    tnote(8)[#super[a]Predictive minus reactive. #super[b]Mean and 95% interval; left of the dashed zero line favors
      the forecast. #super[c]Pairs in which the predictive hybrid was faster. #super[d]Sampled with 10,000 sign
      flips.],
  ),
  placement: auto,
  scope: "parent",
  caption: [Paired comparison of the reactive and predictive hybrids, mean p99 (ms)],
)
