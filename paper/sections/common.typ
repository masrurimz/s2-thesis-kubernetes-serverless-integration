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
  cetz.canvas(length: 0.98cm, {
    import cetz.draw: *
    set-style(stroke: 0.6pt, mark: (fill: black, scale: 0.6))
    let node(a, b, name, body, fill: white) = {
      rect(a, b, name: name, fill: fill, radius: 2pt)
      content(name, align(center, text(size: 7pt, body)))
    }
    let arrow(..pts, label: none, anchor: "south", pos: none) = {
      line(..pts, mark: (end: ">"))
      if label != none and pos != none {
        content(pos, text(size: 6.5pt, style: "italic", label), anchor: anchor, padding: 2pt)
      }
    }
    let weight(sub) = text(size: 8.5pt, style: "normal", $w_sub$)

    node((0, 2), (2.4, 3.2), "load", [*Load generator* \ k6, ClarkNet replay])
    node((3.4, 2), (5.8, 3.2), "lb", [*HAProxy* \ weighted ingress], fill: luma(240))
    node((3.4, 4.4), (5.8, 5.6), "prom", [*Prometheus* \ load $x$, p99])
    node((7, 3.4), (10, 4.6), "k8s", [*Kubernetes backend* \ 3–10 pods])
    node((7, 0.6), (10, 1.8), "kn", [*Knative backend* \ 3–10 warm pods])
    node((6.6, 5.4), (10.4, 6.4), "nodes", [*Node autoscaler* \ new node after 45–120 s])
    node((13, 5.5), (17.4, 6.5), "gru", [*GRU forecaster* \ 9 steps $times$ 15 s], fill: luma(240))

    rect((11.4, 0.2), (17.4, 4.9), name: "daemon", stroke: (dash: "dashed"), radius: 2pt)
    content((11.55, 4.75), text(size: 6.5pt, [control daemon, every 15 s]), anchor: "north-west")
    node((11.7, 2.7), (17.1, 4.2), "alg2", [*Algorithm 2: replica scaler* \ replica count $R(v)$ from observed load. \ S4 raises it to $R(max_k hat(u)_(t+k))$])
    node((11.7, 0.5), (17.1, 2.0), "alg1", [*Algorithm 1: capacity-aware router* \ serverless weight from $x$ and ready pods $n$])

    arrow("load.east", "lb.west", label: [HTTP], pos: (2.9, 2.6))
    arrow((5.8, 2.9), (7, 4.0), label: weight("k8s"), pos: (6.3, 3.55), anchor: "south-east")
    arrow((5.8, 2.3), (7, 1.2), label: weight("sls"), pos: (6.3, 1.65), anchor: "north-east")
    arrow("lb.north", "prom.south", label: [metrics], pos: (4.6, 3.8), anchor: "west")
    arrow("prom.north", (4.6, 7.1), (12.2, 7.1), (12.2, 4.9), label: [load $x$, p99], pos: (8.4, 7.1))
    arrow("gru.south", (15.2, 4.2), label: [upper envelope $hat(u)$ (S4 only)], pos: (15.05, 5.2), anchor: "east")
    arrow("alg2.west", "k8s.east", label: [replica count], pos: (10.65, 3.6), anchor: "north")
    arrow((9.8, 3.4), (9.8, 2.4), (11.0, 2.4), (11.0, 1.25), "alg1.west", label: [ready pods $n$], pos: (10.9, 2.3), anchor: "north-east")
    arrow("alg1.south", (14.4, -0.5), (4.6, -0.5), "lb.south", label: [weights $w_"k8s", w_"sls"$], pos: (9.5, -0.5))
    arrow("nodes.south", "k8s.north")
  }),
  placement: auto,
  scope: "parent",
  caption: [Control architecture.],
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
    + *input:* load $x$ (RPS), ready pods $n$, current serverless weight $w$
    + $C <- n dot r_"eff"$ #h(1fr) ▷ capacity of ready pods
    + *if* $x <= C$ *then* $w' <- 0$
    + *else* $w' <- min(50, ceil(100 (x - C) \/ x))$ #h(1fr) ▷ excess share, capped
    + *if* $w' != w$ *then* set HAProxy weights $(w_"k8s", w_"sls") <- (100 - w', w')$
  ])),
)

#let alg-scaling = figure(
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [ElaX-derived replica scaler with the forecast decision factor, every 15 s],
  align(start, text(size: 8pt, pseudocode-list(booktabs: true, numbered-title: none)[
    + *input:* load samples, upper envelope $hat(u)_(t+1..t+9)$ (S4), current replica count $r$, p99
    + $R(v) := "clamp"(ceil(alpha v + beta), R_min, R_max)$
    + $x_"obs" <-$ mean load over the last 30 s; $T <- R(x_"obs")$ #h(1fr) ▷ observed-load target
    + *if* scenario is S4 *then*
      + $T_p <- R(max_k hat(u)_(t+k))$ #h(1fr) ▷ forecast target
      + *if* $T_p > T$ *then* $T <- T_p$; hold $(T_p, t + 90 "s")$
      + *else if* a hold is active *and* its target $> T$ *then* $T <-$ held target
    + *if* $T > r$ *and* 15 s since last scale-up *then* scale to $T$
    + *else if* $T < 0.75 r$ *and* 120 s since last scale-down *and* p99 $< 140$ ms *then* scale to $T$
  ])),
)

// ---------------------------------------------------------------------------
// Tables.
#let tab-elax = figure(
  table(
    columns: (auto, 1fr, 1fr),
    align: (left, left, left),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [], [*ElaX* @yang2019elax], [*This work (Algorithm 2)*],
    rule,
    [Predictor], [LSTM on a denoised series], [GRU with one 9-step output head],
    [Horizon], [60 one-minute points], [9 steps of 15 s (135 s)],
    [Refresh], [forecast and reservation every hour, model retrained every day], [every 15 s control cycle],
    [Decision factor $v$#super[a]], [largest point forecast of the next hour], [largest upper-envelope value of the next 135 s, used when it needs more pods than the observed load],
    [Resource model], [$R = sigma y + beta$, fitted by profiling], [$R = ceil(alpha v + beta)$ with $alpha = 1 \/ r_"eff"$, $beta = 0$],
    [Feedback], [slack-based online controller, every 2 s], [cooldowns and a p99 guard on scale-down],
    [Scaling], [horizontal and vertical], [horizontal, with a separate node tier],
    [Scope], [one container cluster], [Kubernetes and Knative behind one router (Algorithm 1)],
    toprule,
    tnote(3)[#super[a]Our term: the load value from which the scaler computes the replica count.],
  ),
  placement: auto,
  caption: [Algorithm 2 compared with ElaX],
) 

#let tab-scenarios = figure(
  table(
    columns: (auto, 1fr, 1fr, auto),
    align: (left, left, left, center),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [], [*Pod scaling*], [*Traffic*], [*GRU forecast*],
    rule,
    [S1], [HPA (50% CPU), 1–10 pods], [100% Kubernetes], [no],
    [S2], [Knative autoscaler, 3–10 pods], [100% Knative], [no],
    [S3], [Algorithm 2, observed load], [Algorithm 1], [no],
    [S4], [Algorithm 2, observed load and forecast], [Algorithm 1], [yes],
    toprule,
  ),
  caption: [Deployment scenarios],
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

#let tab-four = figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [], [*p99 (ms)*], [*SLO viol.*], [*Serverless*], [*K8s pod-s*], [*USD/mo*],
    rule,
    [S1], [#F.s1.p99 ± #F.s1.p99_sd], [#F.s1.slo], [#F.s1.share%], [#F.s1.replica_s], [#F.s1.cost],
    [S2], [#F.s2.p99 ± #F.s2.p99_sd], [#F.s2.slo], [#F.s2.share%], [#F.s2.replica_s], [#F.s2.cost],
    [S3], [#F.s3.p99 ± #F.s3.p99_sd], [#F.s3.slo], [#F.s3.share%], [#F.s3.replica_s], [#F.s3.cost],
    [S4#super[a]], [#F.s4.p99 ± #F.s4.p99_sd], [#F.s4.slo], [#F.s4.share%], [#F.s4.replica_s], [#F.s4.cost],
    toprule,
    tnote(6)[#super[a]S4 ran an earlier GRU, not the model of @sec:gru.],
  ),
  caption: [Scenario batch, means over five runs per scenario],
)

#let h2row(label, b) = (
  label, [#b.s3], [#b.s4], [#b.diff \[#b.ci_lo, #b.ci_hi\]], [#b.p], [#b.d], [#b.wins/#b.n],
)

#let tab-h2 = figure(
  table(
    columns: (auto, auto, auto, 1fr, auto, auto, auto),
    align: (left, right, right, center, right, right, right),
    stroke: none,
    inset: (x: 2.5pt, y: 2.2pt),
    toprule,
    [*Batch*], [*S3*], [*S4*], [*S4 − S3 \[95% CI\]*], [*p*], [*d*], [*S4 faster*],
    rule,
    ..h2row([A], H.b5),
    ..h2row([B], H.b10a),
    ..h2row([C], H.b10b),
    rule,
    [Pooled], [–], [–], [#H.pooled.diff \[#H.pooled.ci_lo, #H.pooled.ci_hi\]], [#H.pooled.p#super[a]],
    [#H.pooled.d], [#H.pooled.wins/#H.pooled.n],
    toprule,
    tnote(7)[#super[a]Sampled with 10,000 sign flips.],
  ),
  caption: [Paired comparison of S3 and S4, mean p99 (ms)],
)

// ---------------------------------------------------------------------------
// Fig.: p99 of every run of the scenario batch.
#let fig-runs = {
  let cols = (([S1 \ HPA], F.s1), ([S2 \ Knative], F.s2), ([S3 \ reactive], F.s3), ([S4 \ predictive], F.s4))
  let sy(v) = v / 72
  let right = 7.7
  figure(
    cetz.canvas(length: 1cm, {
      import cetz.draw: *
      set-style(stroke: 0.5pt)
      line((0, 0), (0, sy(262)))
      line((0, 0), (right, 0))
      for t in (0, 100, 200) {
        line((0, sy(t)), (-0.08, sy(t)))
        content((-0.14, sy(t)), text(size: 6.5pt, str(t)), anchor: "east")
      }
      content((-0.78, sy(130)), angle: 90deg, text(size: 6.5pt, [p99 per run (ms)]))
      line((0, sy(200)), (right, sy(200)), stroke: (dash: "dashed", paint: luma(120)))
      content((right, sy(200) + 0.04), text(size: 6.5pt, [SLO 200 ms]), anchor: "south-east")
      for (i, (label, s)) in cols.enumerate() {
        let x = 1.0 + i * 1.9
        content((x, -0.1), align(center, text(size: 6.5pt, label)), anchor: "north")
        let m = s.plot.sum() / s.plot.len()
        line((x - 0.55, sy(m)), (x + 0.55, sy(m)), stroke: 0.9pt)
        for (j, v) in s.plot.enumerate() {
          circle((x + (j - 2) * 0.17, sy(v)), radius: 0.055, fill: white)
        }
      }
    }),
    caption: [p99 of every run of the scenario batch, with the mean as a bar.],
  )
}

// ---------------------------------------------------------------------------
// Fig.: forest plot of the paired p99 difference per batch.
#let fig-forest = {
  let rows = (([A (5 pairs)], H.b5.plot), ([B (10 pairs)], H.b10a.plot), ([C (10 pairs)], H.b10b.plot), ([Pooled (25 pairs)], H.pooled.plot))
  let sx(v) = v / 260
  figure(
    cetz.canvas(length: 1cm, {
      import cetz.draw: *
      set-style(stroke: 0.5pt)
      let top = rows.len() * 0.6
      line((sx(0), -0.2), (sx(0), top), stroke: (dash: "dashed", paint: luma(120)))
      for t in (-500, 0, 500, 1000) {
        line((sx(t), -0.2), (sx(t), -0.28))
        content((sx(t), -0.32), text(size: 6.5pt, str(t).replace("-", "−")), anchor: "north")
      }
      line((sx(-700), -0.2), (sx(1100), -0.2))
      content((sx(200), -0.75), text(size: 6.5pt, [S4 − S3 p99 (ms); left of 0 favors S4]), anchor: "north")
      for (i, (label, v)) in rows.enumerate() {
        let y = top - 0.3 - i * 0.6
        content((sx(-720), y), text(size: 7pt, label), anchor: "east")
        line((sx(v.at(1)), y), (sx(v.at(2)), y), stroke: 0.9pt)
        let s = if i == rows.len() - 1 { 0.11 } else { 0.07 }
        rect((sx(v.at(0)) - s, y - s), (sx(v.at(0)) + s, y + s), fill: black)
      }
    }),
    caption: [Mean paired p99 difference with its 95% bootstrap interval, per batch and pooled.],
  )
}
