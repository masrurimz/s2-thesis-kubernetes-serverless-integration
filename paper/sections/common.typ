// Facts shared by the conference and journal papers: numbers, tables, figures,
// algorithms. Prose lives in conference-body.typ and journal-body.typ. Every
// number comes from numbers.json, which derive_numbers.py builds from the bundles.
#import "@preview/cetz:0.4.0"
#import "@preview/lovelace:0.3.0": pseudocode-list

#let N = json("../numbers.json")
#let F = N.four
#let H = N.h2
#let G = N.gru
#let figdir = "../../thesis-typst/src/figures/paper/"

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

    node((0, 2), (2.4, 3.2), "load", [*Load generator* \ k6, ClarkNet replay])
    node((3.4, 2), (5.8, 3.2), "lb", [*HAProxy* \ weighted ingress], fill: luma(240))
    node((3.4, 4.4), (5.8, 5.6), "prom", [*Prometheus* \ load $x$, p99])
    node((7, 3.4), (10, 4.6), "k8s", [*Kubernetes backend* \ always-warm pods])
    node((7, 0.6), (10, 1.8), "kn", [*Knative backend* \ KPA, 3–10 warm pods])
    node((7, 5.4), (10, 6.4), "nodes", [*Node autoscaler* \ pending pod $->$ node, 45–120 s])
    node((13, 5.5), (17.4, 6.5), "gru", [*GRU forecaster* \ 9 steps $times$ 15 s], fill: luma(240))

    rect((11.4, 0.2), (17.4, 4.9), name: "daemon", stroke: (dash: "dashed"), radius: 2pt)
    content((11.55, 4.75), text(size: 6.5pt, [routing daemon, every 15 s]), anchor: "north-west")
    node((11.7, 2.7), (17.1, 4.2), "alg2", [*Algorithm 2: replica scaling* \ $R(v) = ceil(alpha v + beta)$; S4 raises \ the target to $R(max_k hat(u)_(t+k))$])
    node((11.7, 0.5), (17.1, 2.0), "alg1", [*Algorithm 1: capacity-aware routing* \ serverless share from $x$ and ready pods $n$])

    arrow("load.east", "lb.west", label: [HTTP], pos: (2.9, 2.6))
    arrow((5.8, 2.9), (7, 4.0), label: [$w_"k8s"$], pos: (6.3, 3.55), anchor: "south-east")
    arrow((5.8, 2.3), (7, 1.2), label: [$w_"sls"$], pos: (6.3, 1.65), anchor: "north-east")
    arrow("lb.north", "prom.south", label: [metrics], pos: (4.6, 3.8), anchor: "west")
    arrow("prom.north", (4.6, 7.1), (12.2, 7.1), (12.2, 4.9), label: [load $x$, p99], pos: (8.4, 7.1))
    arrow("gru.south", (15.2, 4.2), label: [upper envelope $hat(u)$ (S4 only)], pos: (15.05, 5.2), anchor: "east")
    arrow("alg2.west", "k8s.east", label: [replicas], pos: (10.65, 3.6), anchor: "north")
    arrow((9.8, 3.4), (9.8, 2.4), (11.0, 2.4), (11.0, 1.25), "alg1.west", label: [ready pods $n$], pos: (10.9, 2.3), anchor: "north-east")
    arrow("alg1.south", (14.4, -0.5), (4.6, -0.5), "lb.south", label: [weights $w_"k8s", w_"sls"$], pos: (9.5, -0.5))
    arrow("nodes.south", "k8s.north")
  }),
  placement: auto,
  scope: "parent",
  caption: [Control architecture. HAProxy splits requests between the Kubernetes and Knative backends.
    Every 15 s the routing daemon runs Algorithm 1, which sets the split from observed load and ready
    pods, and Algorithm 2, which sets the replica count. Only Algorithm 2 uses the GRU forecast, and only
    in the hybrid-predictive scenario (S4).],
) 

// ---------------------------------------------------------------------------
// Algorithms.
#let alg-routing = figure(
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [Capacity-aware traffic distribution, every 15 s],
  align(start, text(size: 8pt, pseudocode-list(booktabs: true, numbered-title: none)[
    + *input:* observed load $x$ (RPS), ready replicas $n$, current serverless weight $w$
    + $C <- n dot r_"eff"$ #h(1fr) ▷ capacity of ready pods
    + *if* $x <= C$ *then* $w' <- 0$
    + *else* $w' <- min(50, ceil(100 (x - C) \/ x))$ #h(1fr) ▷ burst share, capped
    + $w' <- "clamp"(w' + p_"burn", 0, 50)$ #h(1fr) ▷ SLO pacing term
    + *if* $w' != w$ *then* set HAProxy weights $(w_"k8s", w_"sls") <- (100 - w', w')$
  ])),
)

#let alg-scaling = figure(
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [ElaX-derived replica scaling with the forecast decision factor, every 15 s],
  align(start, text(size: 8pt, pseudocode-list(booktabs: true, numbered-title: none)[
    + *input:* load samples, upper envelope $hat(u)_(t+1..t+9)$ (S4), desired replicas $r$, p99
    + $R(v) := "clamp"(ceil(alpha v + beta), R_min, R_max)$
    + $x_"obs" <-$ mean observed load over the last 30 s; $T <- R(x_"obs")$
    + *if* scenario is S4 *then*
      + $T_p <- R(max_k hat(u)_(t+k))$ #h(1fr) ▷ decision factor
      + *if* $T_p > T$ *then* $T <- T_p$; hold $(T_p, t + 90 "s")$
      + *else if* a hold is active *and* its target $> T$ *then* $T <-$ held target
    + *if* $T > r$ *and* 15 s since last scale-up *then* scale to $T$
    + *else if* $T < 0.75 r$ *and* 120 s since last scale-down *and* p99 $< 140$ ms *then*
      + scale to $max(T, R_min)$
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
    [Predictor], [LSTM on a denoised series], [GRU, direct 9-output head],
    [Horizon], [60 one-minute points], [9 steps of 15 s (135 s)],
    [Refresh], [forecast and reservation hourly; model daily], [every 15 s control cycle],
    [Decision factor $v$], [largest point forecast in the next hour], [largest *upper-envelope* value in the next 135 s, used only if its target exceeds $R(x_"obs")$; raised target held 90 s],
    [Feedback], [slack-based online controller, every 2 s], [not reimplemented; cooldowns and a p99 guard on scale-down],
    [Dimension], [horizontal and vertical], [horizontal pods; node tier separate],
    [Scope], [one container cluster], [Kubernetes and Knative behind one router (Algorithm 1)],
    toprule,
  ),
  caption: [What Algorithm 2 keeps from ElaX and what it changes],
) 

#let tab-scenarios = figure(
  table(
    columns: (auto, 1fr, 1fr, auto),
    align: (left, left, left, center),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [], [*Pod scaling*], [*Traffic*], [*Forecast*],
    rule,
    [S1], [HPA (50% CPU), 1–10 pods], [100% Kubernetes], [no],
    [S2], [Knative KPA, 3–10 pods], [100% Knative], [no],
    [S3], [Algorithm 2, observed load], [Algorithm 1], [no],
    [S4], [Algorithm 2, observed + forecast], [Algorithm 1], [yes],
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
    [LSTM, same protocol (3 seeds)], [#G.lstm.rmse ± #G.lstm.rmse_sd], [#G.lstm.mae], [#G.lstm.skill],
    [Linear autoregression], [#G.ols_rmse], [#G.ols_mae], [–],
    [Persistence], [#G.persistence], [–], [0],
    [Linear trend], [#G.trend], [–], [–],
    [Seasonal naive (one day)], [#G.seasonal], [–], [–],
    toprule,
  ),
  caption: [Forecast error on the held-out ClarkNet test region, 9-step horizon, in RPS of the replayed
    (×33) series. Skill is $1 - "RMSE" \/ "RMSE"_"persistence"$.],
)

#let tab-four = figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right),
    stroke: none,
    inset: (x: 3pt, y: 2.2pt),
    toprule,
    [], [*p99 (ms)*], [*SLO viol.*], [*Serverless*], [*Pod-s*], [*USD/mo*],
    rule,
    [S1], [#F.s1.p99 ± #F.s1.p99_sd], [#F.s1.slo], [#F.s1.share%], [#F.s1.replica_s], [#F.s1.cost],
    [S2], [#F.s2.p99 ± #F.s2.p99_sd], [#F.s2.slo], [#F.s2.share%], [#F.s2.replica_s], [#F.s2.cost],
    [S3], [#F.s3.p99 ± #F.s3.p99_sd], [#F.s3.slo], [#F.s3.share%], [#F.s3.replica_s], [#F.s3.cost],
    [S4#super[a]], [#F.s4.p99 ± #F.s4.p99_sd], [#F.s4.slo], [#F.s4.share%], [#F.s4.replica_s], [#F.s4.cost],
    toprule,
  ),
  caption: [Four scenarios, five runs each (mean ± sd), batch of August 2026. SLO violations are requests
    over 200 ms per run. Serverless is the share of the HAProxy weight-time product. Pod-s is Kubernetes
    replica-seconds per run. #super[a]S4 ran an earlier GRU with an envelope offset near 10 RPS, not the
    model of @sec:gru.],
)

#let h2row(label, b) = (
  label, [#b.n], [#b.s3], [#b.s4], [#b.diff \[#b.ci_lo, #b.ci_hi\]], [#b.p], [#b.d], [#b.wins/#b.n],
)

#let tab-h2 = figure(
  table(
    columns: (auto, auto, auto, auto, 1fr, auto, auto, auto),
    align: (left, right, right, right, center, right, right, right),
    stroke: none,
    inset: (x: 2.5pt, y: 2.2pt),
    toprule,
    [*Batch*], [*n*], [*S3*], [*S4*], [*S4 − S3 \[95% CI\]*], [*p*], [*d*], [*Wins*],
    rule,
    ..h2row([A], H.b5),
    ..h2row([B], H.b10a),
    ..h2row([C], H.b10b),
    rule,
    [Pooled], [#H.pooled.n], [–], [–], [#H.pooled.diff \[#H.pooled.ci_lo, #H.pooled.ci_hi\]], [#H.pooled.p],
    [#H.pooled.d], [#H.pooled.wins/#H.pooled.n],
    toprule,
  ),
  caption: [Paired S3 against S4, mean p99 in ms. One-sided exact permutation p (alternative: S4 faster);
    the pooled p is sampled with 10,000 sign flips. d is the paired Cohen's d. Wins counts pairs S4 won.],
)

// ---------------------------------------------------------------------------
// Fig.: forest plot of the paired p99 difference per batch.
#let fig-forest = {
  let rows = (([A (n = 5)], H.b5.plot), ([B (n = 10)], H.b10a.plot), ([C (n = 10)], H.b10b.plot), ([Pooled (n = 25)], H.pooled.plot))
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
      content((sx(200), -0.75), text(size: 6.5pt, [S4 − S3 p99 (ms); left of 0 favours S4]), anchor: "north")
      for (i, (label, v)) in rows.enumerate() {
        let y = top - 0.3 - i * 0.6
        content((sx(-720), y), text(size: 7pt, label), anchor: "east")
        line((sx(v.at(1)), y), (sx(v.at(2)), y), stroke: 0.9pt)
        let s = if i == rows.len() - 1 { 0.11 } else { 0.07 }
        rect((sx(v.at(0)) - s, y - s), (sx(v.at(0)) + s, y + s), fill: black)
      }
    }),
    caption: [Paired p99 difference with 95% bootstrap interval for the three batches that ran the
      ClarkNet-trained predictor, and for the 25 pairs pooled.],
  )
}

#let fig-boxplot = figure(
  image(figdir + "fig04-p99-boxplot.svg", width: 100%),
  caption: [p99 per run for the four scenarios (five runs each). The dashed line is the 200 ms SLO.],
)
