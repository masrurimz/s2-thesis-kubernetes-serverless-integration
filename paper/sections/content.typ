// Shared paper content. Each section is a function taking `extended`:
//   extended: false -> tight 6-page conference version (TIME-E)
//   extended: true  -> extended journal version
// Figures resolve relative to this file's location under paper/.

#let figdir = "../../thesis-typst/src/figures/paper/"

// ---------------------------------------------------------------------------
#let abstract(extended: false) = [
  Hybrid cloud architectures route traffic between always-warm container
  clusters and scale-to-zero serverless backends. The routing decision is only
  as good as the controller's knowledge of near-term demand. We present a
  hybrid Kubernetes--serverless architecture that couples SLO-aware traffic
  routing with a GRU workload predictor, extending the ElaX
  elastic-provisioning algorithm with a confidence-gated forecast that drives
  replica scaling. We evaluate the system on a CPU-bounded multi-node testbed
  that replays the ClarkNet HTTP trace, and we compare four deployment
  scenarios under a counterbalanced paired design with treatment-fidelity
  gates. Hybrid routing cuts p99 latency by up to 95% relative to a saturated
  pure-Kubernetes baseline. The benefit of prediction over a reactive
  controller is conditional: across ten ClarkNet-attributable pairs the
  predictive controller lowers mean p99 by 104 ms but does not reach
  significance on the pre-specified test ($p = 0.168$). A per-run host-load
  series we add shows that host CPU contention correlates with p99 at
  $r = 0.69$; restricting to the eight pairs measured on a quiet host yields a
  significant $-101$ ms advantage ($p = 0.039$, $d = -0.74$). Predictive
  autoscaling is therefore a measurement-hygiene problem as much as a
  modelling one.
]

#let index-terms() = (
  [Cloud computing], [serverless computing], [Kubernetes], [autoscaling],
  [workload prediction], [gated recurrent unit], [traffic routing],
)

// ---------------------------------------------------------------------------
#let introduction(extended: false) = [
  = Introduction
  Cloud-native deployment has split into two paradigms with complementary
  trade-offs. Kubernetes runs always-warm pods that deliver consistent low
  latency, but its Horizontal Pod Autoscaler (HPA) reacts to observed CPU or
  memory thresholds. A surge that arrives faster than pods can be scheduled
  produces a window of Service-Level-Objective (SLO) violations
  @serracanta2025hpa. Serverless platforms such as Knative and AWS Lambda
  scale to zero and absorb bursts almost instantly, but they pay a cold-start
  penalty and a per-invocation cost that grows with sustained load
  @golec2023cold @yu2020characterizing.

  A hybrid architecture routes each request to the backend that serves it
  best. Kubernetes carries the baseline at low cost and latency; serverless
  absorbs the peaks that would otherwise queue behind provisioning pods. The
  open question is the controller. A reactive router shifts traffic only
  after latency has already degraded; a predictive router can pre-position
  capacity before a forecast surge arrives. Whether that anticipation yields
  a measurable tail-latency advantage is the question this paper answers.

  We build on the ElaX elastic-provisioning algorithm @yang2019elax, which
  couples a workload predictor, a linear resource model $R = alpha x + beta$,
  and an online controller. We extend it in two directions: a GRU forecaster
  trained under a leak-free chronological protocol, and an SLO-aware routing
  layer that splits traffic by observed load, ready-replica capacity, and a
  200 ms p99 objective. The forecast is confidence-gated and feeds only the
  slower replica-scaling path; the fast routing path stays reactive, so a
  wrong forecast can delay scaling but cannot misroute traffic.

  Our evaluation is adversarial toward our own hypothesis. We replay the
  ClarkNet trace on a CPU-bounded k3d testbed, run a counterbalanced paired
  comparison of the reactive and predictive controllers, and gate every run
  on treatment fidelity: a predictive run that did not receive its forecasts
  is discarded, not averaged in. We also record a per-run host CPU-busy
  series, which lets us separate the controller's effect from measurement
  noise on a shared testbed.

  The contributions are:
  + a hybrid Kubernetes--serverless architecture with an SLO-aware routing
    controller and a confidence-gated GRU forecaster driving replica scaling;
  + a paired, validity-gated evaluation showing hybrid routing cuts p99 by up
    to 95% over a saturated Kubernetes baseline, while the predictive
    advantage over reactive control is conditional on host contention;
  + evidence that per-run host-load instrumentation is needed to attribute
    tail-latency effects on a shared testbed, turning a non-significant
    headline into a significant clean-host result.
]

// ---------------------------------------------------------------------------
#let related(extended: false) = [
  = Related Work
  *Autoscaling.* Kubernetes HPA and the Knative Pod Autoscaler are reactive:
  they scale on observed metrics. Stability analyses of the HPA control loop
  @serracanta2025hpa and surveys of scheduling and autoscaling
  @senjab2023survey @mampage2022holistic document the lag between surge onset
  and capacity. Predictive autoscalers add a forecast: HyPA @hypa2023 and
  KAPETÁNIOS @kapetanios2022 update scaling models online, AAPA @aapa2025
  adds uncertainty quantification for serverless workloads, and ADAPT
  @adapt2026 self-calibrates its horizon. We differ by routing across two
  heterogeneous backends rather than scaling one, and by gating the forecast
  on measured fidelity rather than trusting it.

  *Hybrid and serverless cost.* Serverless benchmarks
  @yu2020characterizing @sebs2020 @letstrace2022 quantify cold-start and
  billing granularity; cost studies @demystifying2025 @skyrise2025
  @highcost2025 show warm-pool overhead and break-even behaviour that make a
  hybrid split attractive. ElaX @yang2019elax is the closest ancestor; we
  keep its predictor-plus-linear-model structure but replace single-tier
  scaling with cross-backend routing and a three-tier mechanism.

  *Forecasting.* GRUs @cho2014learning @chung2014empirical offer a good
  accuracy-to-cost ratio for workload series. We adopt GRU but report that
  under a leak-free protocol it matches, not beats, a linear autoregression
  at 15 s resolution. This aligns with cautions about overfitting in
  autoscaler model selection @cawley2010overfitting.
]

// ---------------------------------------------------------------------------
#let design(extended: false) = [
  = System Design
  #figure(
    image(figdir + "fig01-control-loop.svg", width: 100%),
    placement: auto,
    scope: "parent",
    caption: [Control loop. HAProxy splits traffic between the K3s and Knative
      backends; the routing daemon adjusts weights every 15 s and the GRU
      server supplies a confidence-gated forecast to the scaling path.],
  ) <fig:arch>

  @fig:arch shows the architecture. Clients generate load; HAProxy
  ingress splits it between an always-warm K3s backend and a scale-to-zero
  Knative backend by a runtime-adjustable weight. A routing daemon runs a
  15 s control loop over two algorithms. *Algorithm 1 (routing)* sets the
  HAProxy weight from observed load, ready-replica capacity, and SLO status
  under the priority order SCALE_OUT $>$ PREDICTIVE $>$ OPTIMIZE_COST $>$
  MAINTAIN; each step shifts the split by ten percentage points.
  *Algorithm 2 (cluster scaling)* plans Kubernetes replicas with the ElaX
  linear model $R = alpha x + beta$, where in predictive mode $x$ is the
  confidence-gated GRU upper forecast rather than the observed load. A third
  tier, a node autoscaler, provisions workload nodes when pods pend and
  consolidates them when utilization falls below 50%.

  *Predictor.* A two-layer GRU (256 hidden units, 30-sample input window at
  15 s, 9-step / 135 s horizon) is served over HTTP at ~40 ms inference. It
  trains on the ClarkNet series resampled to the replay amplitude under a
  chronological split with an embargo, so the replayed window is never
  trained on. The forecast reaches the controller as an upper envelope gated
  by a confidence score derived from validation error; when confidence is low
  the controller falls back to observed load, so prediction can only help,
  not misroute.

  #if extended [
    *Why the split matters.* Routing reacts in milliseconds and must never
    wait on a forecast; replica scaling takes tens of seconds and is where a
    forecast earns its lead time. Separating the two paths keeps the fast
    loop reactive and reserves prediction for the slow loop, which is also
    where a wrong forecast is cheapest: an over-predicted replica is idle
    capacity, whereas a misrouted request is a user-visible latency.
  ]
]

// ---------------------------------------------------------------------------
#let methodology(extended: false) = [
  = Methodology
  *Testbed.* A multi-node k3d cluster with two CPU-bounded workload nodes
  (Docker `--cpus=1.0`), K3s for the container backend, Knative + Kourier for
  serverless, HAProxy for weighted ingress, and Prometheus for SLO
  monitoring. The SLO is a 200 ms p99 over a sliding window.

  *Workload.* The ClarkNet HTTP trace @clarknet replayed at a mean of 73 RPS
  (peak 164 RPS) over 1,200 s, giving realistic ramps and surges rather than
  a synthetic constant load.

  *Scenarios.* S1 is pure Kubernetes with HPA; S2 is serverless-only; S3 is
  the hybrid with reactive routing; S4 is the hybrid with predictive routing.
  H1 compares S4 to S1; H2 compares S4 to S3.

  *Paired design and validity.* H2 is tested with counterbalanced S3/S4 pairs
  that share a warmed testbed and alternate order to cancel drift. Every run
  passes a treatment-fidelity gate: an S4 run counts only if the forecast
  horizon covers the measured provisioning delay and 100% of eligible
  predictions are delivered. The primary endpoint is the paired p99
  difference under an exact permutation test; we report Cohen's $d$ and a
  95% paired interval.

  *Host-load instrumentation.* Each run records a `host_load` series, the
  host CPU-busy fraction sampled at every control cycle, so that contention
  on the shared testbed is measured rather than assumed away.

  #if extended [
    *Calibration.* The scaling model uses $alpha = 1 / r_"effective"$ with
    $r_"effective" = r_"saturation" times "target_cpu_util" = 33.3 times 0.5
    = 16.65$ RPS per replica and buffer 1.0. An earlier calibration
    double-counted the safety margin and collapsed the predictive and
    reactive targets; correcting it is what separated the two controllers.
    The node autoscaler mirrors the Kubernetes Cluster Autoscaler's
    `WhenEmptyOrUnderutilized` policy @k8sca-faq: a node is drained and
    removed when CPU-request utilization stays under 50% for 90 s with a
    120 s cooldown.
  ]
]

// ---------------------------------------------------------------------------
#let results(extended: false) = [
  = Results
  == Predictor accuracy
  Under the leak-free protocol the GRU reaches a held-out RMSE of
  $29.635 plus.minus 0.016$ and skill 0.216 against persistence at the served
  amplitude. It meets its pre-registered accuracy target on the synthetic arm
  (RMSE 5.2% of mean load) but not on the held-out region of the real trace
  (39.6%), where it matches a linear autoregression on the same window
  (29.465). A twelve-lever representation search found no variant that beats
  the linear model on the selection folds. We therefore deploy the forecast
  as an upper-envelope signal rather than a point estimate and disclose the
  linear parity as a limitation.

  == Hybrid versus pure Kubernetes (H1)
  With node CPU limits enforced and replicas capped at schedulable capacity,
  the pure-Kubernetes baseline saturates under the ClarkNet load. The hybrid
  predictive scenario cuts p99 from 2,421.3 ms to 118.2 ms ($-95.1%$) and SLO
  violations from 6,717 to 104 ($-98.5%$) in the bounded diagnostic. H1 is
  directionally supported: hybrid routing provides a large, unambiguous
  benefit when Kubernetes alone cannot absorb the peaks.

  #figure(
    table(
      columns: (auto, auto, auto, auto, auto),
      [Scenario], [p99 (ms)], [SLO viol.], [SLO rate], [Serverless %],
      [S1 K8s+HPA], [2,421.3], [6,717], [7.66%], [0.0%],
      [S2 Serverless], [77.7], [19], [0.02%], [100.0%],
      [S3 Reactive], [98.8], [3], [0.00%], [31.8%],
      [S4 Predictive], [118.2], [104], [0.12%], [24.7%],
    ),
    caption: [Per-scenario summary under the bounded diagnostic. The hybrid
      scenarios keep p99 under the 200 ms SLO while pure Kubernetes
      saturates.],
  ) <tab:scenarios>

  #figure(
    image(figdir + "fig04-p99-boxplot.svg", width: 100%),
    caption: [Per-scenario p99 latency over the n = 5 four-scenario
      replication. With ten-replica headroom the pure-Kubernetes baseline no
      longer saturates, so the hybrid advantage narrows; the bounded case in
      Table I is where routing earns its keep.],
  ) <fig:boxplot>

  == Predictive versus reactive (H2)
  The ClarkNet-attributable paired experiment (ten counterbalanced pairs, all
  passing fidelity gates) gives a mean p99 difference of $-104.2$ ms in S4's
  favour, but the pre-specified permutation test is not significant
  ($p = 0.168$, $d = -0.33$). On the headline test, H2 is not supported.

  #figure(
    image(figdir + "fig02-paired-p99.svg", width: 100%),
    caption: [Per-pair p99 for the reactive and predictive controllers. The
      predictive arm wins most pairs, but the spread across pairs is what
      keeps the pre-specified test from significance.],
  ) <fig:paired>
  #figure(
    image(figdir + "fig07-replication-forest.svg", width: 100%),
    caption: [Paired S4$-$S3 p99 difference across batches; negative favours
      the predictive controller. The effect direction is consistent but the
      pre-specified test is significant only on quiet-host subsets.],
  ) <fig:forest>

  *Host-contention sensitivity.* The per-run host-load series explains the
  variance. Peak host CPU-busy correlates with p99 at $r = 0.69$, and the
  three slowest runs all coincided with a settling host (peak 66--100% busy).
  Restricting to the eight pairs where both arms stayed under 40% host busy
  yields a significant $-101.3$ ms advantage ($p = 0.039$, $d = -0.74$, S4
  wins 6 of 8). This is a post-hoc sensitivity analysis, not the
  pre-specified test; it shows the effect the contention was masking and
  argues for a quiet-host design rather than overclaiming.

  == Node provisioning and consolidation
  The third tier decides when prediction pays. The node autoscaler
  provisions a workload node when pods pend and consolidates it when
  utilization falls below 50%. @fig:nodeprov shows the provisioning
  timeline: nodes arrive 51--70 s after the load that triggered them, a delay
  the serverless backend absorbs in the hybrid scenarios but that pure
  Kubernetes cannot.

  #figure(
    image(figdir + "fig05-node-provisioning.svg", width: 100%),
    caption: [Dynamic node provisioning under the high-load diagnostic. The
      51--70 s delay between a pending pod and a ready node is the window a
      forecast must cover to be useful.],
  ) <fig:nodeprov>

  Under ClarkNet variable load with consolidation enabled, the predictive
  advantage is largest: S4 held p99 at 113 ms against S3's 228 ms
  ($-50.5%$) and cut SLO violations from 1,085 to 40, at a 5% cost premium.
  The forecast predicts returning load and stops the reactive controller
  from draining nodes it immediately needs again.

  == Cost
  The node-based cost model charges provisioned capacity. S3 and S4 are
  within noise of each other (USD 163/mo in the paired batch), so the
  latency difference is a controller-effect question, not a cost trade-off.
  A per-replica-second accounting would add roughly USD 2/mo to S4 for the
  warm replicas it holds.

  #figure(
    table(
      columns: (auto, auto, auto, auto, auto),
      [Scenario], [Nodes base→peak (dyn-hrs)], [Serverless reqs (PC)], [Total/mo = EKS+EC2+Lambda], [USD/1M SLO-OK],
      [S1 K8s-only], [2→2 (0)], [0 (0)], [USD 132 = 72+60+0], [0.79],
      [S2 Serverless], [0→0], [87,840 (8)], [USD 395 = 0+0+395], [2.19],
      [S3 Reactive], [2→2 (0)], [5,354 (1)], [USD 147 = 72+60+15], [0.81],
      [S4 Predictive], [2→2 (0)], [2,666 (1)], [USD 143 = 72+60+11], [0.79],
    ),
    caption: [AWS monthly cost projection (diagnostic). Nodes is base→peak with dynamic node-hours in parentheses; Total/mo decomposes into EKS+EC2+Lambda.],
  ) <tab:cost>
]

// ---------------------------------------------------------------------------
#let discussion(extended: false) = [
  = Discussion
  The evaluation supports three claims. First, hybrid routing is the
  load-bearing win: when Kubernetes saturates, offloading to serverless
  removes nearly all tail-latency violations. Second, the marginal value of
  prediction over a well-tuned reactive controller is real but conditional:
  it appears on a quiet host and under a consolidation regime, and it is
  masked by host contention on a shared testbed. Third, the instrument that
  surfaced this is the per-run host-load series; without it the same data
  reads as a flat null.

  *Threats to validity.* The testbed is a single multi-node cluster, not a
  public cloud; the cost model is a proxy, not a bill; and the clean-host
  result is a sensitivity analysis on a subset, so it carries a selection
  caveat. The GRU's parity with a linear model means the prediction benefit
  is attributable to the forecast's lead time, not to any deep-learning
  advantage at this resolution.

  #if extended [
    *Generalization.* The conditional-prediction finding fits the broader
    autoscaling literature: proactive control pays when the forecast lead
    time exceeds the provisioning delay and when the environment is quiet
    enough for the signal to survive measurement noise. Where either
    condition fails, a well-tuned reactive controller is competitive and
    simpler to operate.
  ]
]

// ---------------------------------------------------------------------------
#let conclusion(extended: false) = [
  = Conclusion
  We designed and evaluated a hybrid Kubernetes--serverless architecture that
  couples SLO-aware routing with a confidence-gated GRU forecaster. Hybrid
  routing removes up to 95% of tail-latency violations relative to a
  saturated Kubernetes baseline. The incremental benefit of prediction over
  reactive control is conditional: it is significant on a quiet host and
  under node consolidation, and it is masked by host contention on a shared
  testbed. The broader lesson is methodological: per-run host-load
  instrumentation turns an ambiguous null into an attributable result. Future
  work is a quiet-host paired replication and a forecast horizon that adapts
  to the measured provisioning delay.
]
