// Paper body shared by both builds. `extended: false` is the six-page conference paper;
// `extended: true` adds the journal-only material inside `#if extended [...]` blocks.
// Numbers come from common.typ (numbers.json); never type a measured value here.
#import "common.typ": *

#let abstract = [
  Kubernetes adds pods only after load has risen, and a serverless platform absorbs bursts at a higher
  cost per request. We present a control architecture for a hybrid of the two. Every 15 s, a
  capacity-aware router sends to Knative only the load that the ready Kubernetes pods cannot serve, and a
  replica scaler derived from ElaX sizes the Kubernetes deployment. We extend ElaX's scaling decision with
  multi-step forecasts from a gated recurrent unit (GRU). The scaler takes the largest upper-envelope
  value over the next 135 s and uses it only when it asks for more replicas than the observed load does.
  The routing weight depends only on observed load and ready pods. Under a leak-free chronological
  protocol, the GRU beats persistence (skill #G.gru.skill) but not a linear autoregression. On a
  CPU-bounded testbed that replays the ClarkNet trace, the two hybrids used #F.s4_pods_below_s1% to
  #F.s3_pods_below_s1% fewer pod-seconds than Kubernetes with HPA at the same projected cost, and
  serverless alone cost more than twice as much. In a pre-specified batch of ten counterbalanced pairs
  with the leak-free GRU, the forecast changed p99 by #H.b10b.diff ms (95% CI \[#H.b10b.ci_lo,
  #H.b10b.ci_hi\], $p = #H.b10b.p$) and added #H.b10b.replica_pct% more pod-seconds.
]

#let keywords = ([Kubernetes], [serverless computing], [autoscaling], [workload prediction],
  [gated recurrent unit], [traffic routing])

#let body(extended: false) = [
= Introduction
A Kubernetes deployment scales on what it has already observed. The Horizontal Pod Autoscaler (HPA)
compares CPU use with a target and adds pods after the target is crossed @serracanta2025hpa. When the
cluster also lacks nodes, a new virtual machine takes about one to two minutes to boot
@hao2021vmstartup, and the node joins only after that. In that window requests queue and the tail
latency rises. Serverless platforms such as Knative scale the other way. They add instances within
seconds, but they pay a cold-start penalty @golec2023cold and charge higher unit prices plus a
per-invocation fee @demystifying2025, so a steady load costs more there than on reserved nodes.

A hybrid deployment uses both: reserved capacity serves the base load, and serverless functions serve
the part of a burst that the reserved capacity cannot yet absorb @dehigama2024. Such a hybrid needs two
decisions every control cycle: how many Kubernetes replicas to run, and what share of traffic to send to
serverless. The decisions interact. A replica added early lowers the serverless share, and a serverless
backend that absorbs the burst hides a late replica.

ElaX @yang2019elax is a provisioning method for containerized online services that makes the first of
these decisions from a forecast. Once an hour an LSTM predicts the next 60 minutes of load, and ElaX
reserves resources for the largest predicted value through a linear resource model. A slack-based
controller corrects the reservation online. ElaX manages one container cluster. Its hourly horizon is
long compared with the minute-scale surges of web traffic, and it makes no routing decision.

This paper asks whether ElaX's forecast-driven scaling decision still helps when it runs inside a
hybrid, where a serverless backend already absorbs the provisioning gap. The contributions are the
following.
+ An integrated control architecture that coordinates Kubernetes replica scaling (Algorithm 2) and
  capacity-aware traffic distribution (Algorithm 1) between Kubernetes and Knative serverless services
  under a 200 ms p99 service-level objective (SLO).
+ An extension of ElaX's scaling decision with multi-step GRU forecasts. A GRU replaces the LSTM,
  forecasts nine 15 s steps, and refreshes every cycle. The decision factor becomes the largest
  upper-envelope forecast over 135 s, applied only when it asks for more replicas than observed load.
  The routing weight does not depend on the forecast. The GRU is trained and evaluated under a leak-free
  chronological protocol.
+ An evaluation in two parts: a four-scenario comparison of the hybrid against Kubernetes-only (HPA,
  S1) and serverless-only (Knative, S2) deployments, and a paired comparison of predictive (S4) against
  reactive (S3) hybrid control with the leak-free GRU, with validity gates on every run.

In the four-scenario batch, both hybrids cost the same as Kubernetes with HPA and used fewer pod-seconds,
and serverless alone cost more than twice as much. With the leak-free GRU, predictive control gave no
measurable latency gain over reactive control. @sec:related reviews related work. @sec:design presents
the architecture and @sec:gru the forecaster. @sec:setup describes the testbed, @sec:results the
results, and @sec:discussion their limits.

= Related work <sec:related>
*Reactive and predictive autoscaling.* Surveys of serverless resource management describe the lag
between a surge and the capacity that answers it @mampage2022holistic, and surveys of Kubernetes
scheduling cover autoscaling-aware placement @senjab2023survey. HyPA combines reactive and model-based
horizontal scaling and updates its model online @hypa2023, and KAPETÁNIOS adapts Kubernetes through a
digital twin @kapetanios2022. Forecast-based scalers for Kubernetes use time-series models of resource
use or request rate @mondal2023toward @yuan2024time. AAPA adds archetype awareness and uncertainty
estimates for serverless workloads @aapa2025, and ADAPT is a proactive autoscaler that calibrates itself
online @adapt2026. These systems scale one platform. A recent benchmark asks when deep reinforcement
learning beats calibrated baselines at all @rayscale2026.

*Hybrid and serverless execution.* Serverless benchmarks quantify cold starts and billing granularity
@yu2020characterizing @sebs2020, and cost studies show how serverless billing and autoscaling overhead
raise cost @demystifying2025 @highcost2025. MArk provisions virtual machines from a load forecast and
serves bursts on AWS Lambda @zhang2019mark, and Spock uses serverless functions to cover the scale-out lag
of virtual machines @gunasekaran2019spock. PulseNet sends a request to fast, disposable instances when no
regular Knative instance is free @pulsenet2025, so both of its tracks are serverless. LA-IMR routes
latency-sensitive requests and scales proactively in one system @laimr2026. Our design differs in two
ways. The router moves to serverless only the load above the capacity of ready Kubernetes pods, and the
forecast enters only the replica decision, which lets us measure the effect of the forecast alone.

#if extended [
  *Cold starts and scaling control.* Containers also pay a start-up cost when a deployment scales out
  @beni2021reducing. Forecasts have been used to start serverless functions before requests arrive
  @jegannathan2022time, and reinforcement learning to decide how long to keep them warm
  @vahidinia2023mitigating. BACC paces horizontal autoscaling against an error budget @bacc2026, and the
  pacing term of Algorithm 1 follows that idea. AutoScale waits before it turns off an idle server, so that
  capacity which the load needs again is not lost @gandhi2012autoscale. STaleX adapts microservice
  scaling to spatial and temporal load features @stalex2025.
]

*ElaX.* @tab:elax lists what Algorithm 2 keeps from ElaX and what it changes. It keeps the
forecast-then-reserve structure, the linear resource model and the rule of reserving for the largest
predicted value. It changes the predictor, the horizon, the refresh period and the decision factor, and
it places the scaler next to a router that ElaX does not have.

#tab-elax <tab:elax>

= Control architecture <sec:design>
#fig-architecture <fig:arch>

@fig:arch shows the system. HAProxy receives all requests and splits them between an always-warm
Kubernetes deployment and a Knative service by two runtime weights. A daemon runs a 15 s control loop.
In each cycle it reads the request rate $x$ and the p99 latency from Prometheus and the number of ready
pods $n$ from the Kubernetes API, and then runs two algorithms.

== Algorithm 1: capacity-aware traffic distribution
One ready pod serves $r_"eff" = r_"sat" dot u = 33.3 times 0.5 = 16.65$ RPS, where $r_"sat"$ is the
measured saturation throughput of three pods divided by three and $u$ the target utilization. The ready
capacity is $C = n dot r_"eff"$. Kubernetes keeps the load up to $C$, and serverless takes the excess:
$ w_"sls" = cases(0 & "if" x <= C, min(50, ceil(100 (x - C) \/ x)) & "otherwise.") $
The weight moves to its target in one cycle (@alg:routing). The 50% cap bounds the serverless cost of a
capacity failure. A proportional-integral pacing term $p_"burn" >= 0$ can add serverless weight when SLO violations use
up a budget too fast. It counts at most one violation per 15 s decision, so it does not reach its
threshold within a 20-minute run. The weight therefore follows observed load and ready capacity. A
forecast changes it only through the pods that Algorithm 2 adds.

#alg-routing <alg:routing>

#if extended [
  With eight ready pods, $C = 133.2$ RPS, and the cap binds only above 266 RPS. The replayed trace peaks
  at 164 RPS, so the cap never bound in the reported runs. The router starts each hybrid run at a 20%
  serverless weight, and the first decision corrects it. When it enables serverless, Algorithm 1 also
  sends one warm-up request to Knative. With three pods always running this request has no effect, and in
  the paired batches its endpoint returned HTTP 404.
]

== Algorithm 2: ElaX-derived scaling with a forecast
Algorithm 2 sizes the deployment with the linear model $R(v) = "clamp"(ceil(alpha v + beta), R_min, R_max)$,
with $alpha = 1 \/ r_"eff"$, $beta = 0$, $R_min = 3$ and $R_max = 10$. The reactive hybrid (S3) uses $v = x_"obs"$, the mean load
over the last 30 s. The predictive hybrid (S4) also computes a forecast target from the GRU upper
envelope
$ hat(u)_(t+k) = hat(y)_(t+k) + delta_k, quad k = 1, dots, 9, $
where $hat(y)_(t+k)$ is the point forecast and $delta_k$ the 90th percentile of the positive validation
residuals at step $k$. The decision factor is the largest value $max_k hat(u)_(t+k)$, as in ElaX, but
over 135 s instead of an hour. Algorithm 2 applies the forecast target only when it exceeds
$R(x_"obs")$, and then holds it for 90 s. A forecast can therefore add replicas early but cannot remove
replicas that observed load needs. Scale-down requires the target to fall under 0.75 of the current
count, 120 s since the last scale-down, and p99 under 140 ms.

#alg-scaling <alg:scaling>

#if extended [
  Three choices separate this decision factor from a plain forecast. First, the upper envelope rather
  than the point forecast is used, because a replica that arrives late costs an SLO violation while a
  replica that arrives early costs only idle time. Second, the forecast can only raise the target. A
  forecast that falls below observed load is ignored, so a forecast error cannot drain capacity. Third,
  the 90 s hold keeps a raised target through short dips, which stops the scaler from removing replicas
  that the next forecast asks for again.
]

== Node tier
Pods that cannot be scheduled trigger a node autoscaler. It waits a provisioning delay of 45 to 120 s,
close to the virtual-machine boot times reported in @hao2021vmstartup, and then adds a one-CPU worker.
It removes a dynamic node when its utilization falls below 50%, following the Cluster Autoscaler policy
@k8sca-faq. The forecast horizon of 135 s covers the longest delay plus one control cycle.

= GRU forecaster <sec:gru>
*Model.* A two-layer GRU @cho2014learning @chung2014empirical with #G.hidden hidden units reads the last
30 samples of the request rate at 15 s and emits all nine future steps from one dense head. A FastAPI
server answers each request in #G.latency.median ms (median, p95 #G.latency.p95 ms).

*Leak-free protocol.* The ClarkNet HTTP trace @clarknet is aggregated into 15 s buckets and multiplied
by 33, the factor the replay uses. The series is split in time order into training, validation and test
portions, with an embargo of 38 samples (input length plus horizon minus one) at each boundary. The
scaler is fitted on the training portion only. Hyperparameters and the epoch budget are selected with
the Tree-structured Parzen Estimator @bergstra2011tpe of Optuna @optuna2019 on the validation portion
only. The model is then refit on training plus validation and evaluated once on the test portion, with
three seeds. The 20-minute window that the experiments replay lies inside the test portion, so the
deployed model never saw it.

#if extended [
  The search ran #G.trials trials for each input length (#G.seq_searched samples) on the first seed and
  selected a dropout of #G.dropout, a learning rate of #G.lr and a budget of #G.epochs epochs. The offsets
  $delta_k$ come from the validation residuals of the selected model and range from #G.offset_min to
  #G.offset_max RPS over the nine steps. On the test portion, the upper envelope covered #G.gru.coverage
  of the values that the point forecast under-predicted, against a target of 0.90.
]

*Accuracy.* @tab:predictor reports the test error. The GRU reduces the persistence error by
#G.gru.skill_pct%. Its mean error is slightly lower than that of an LSTM, the predictor family of ElaX,
trained under the same protocol. It does not beat a linear autoregression on the same inputs, and none
of the #G.levers variants that we screened beat the linear model on the selection folds either
@cawley2010overfitting.

#tab-predictor <tab:predictor>

#if extended [
  The error grows with the horizon at the same rate for both models: the GRU RMSE rises from #G.gru_h1 at
  the first step to #G.gru_h9 at the ninth, and the linear model from #G.ols_h1 to #G.ols_h9. The
  variants covered input transforms (differencing, exponential and rolling statistics, robust and
  quantile scaling, reversible instance normalization), a target transform, coarser sampling intervals, a
  decomposed input, and two other architectures (N-BEATS and a linear network). Each was screened on the
  selection folds against the same linear baseline. The GRU kept one advantage over the LSTM outside the
  ClarkNet test region: on a synthetic spike archetype its RMSE was #G.gru.spike against #G.lstm.spike.
  On a synthetic trace, the same protocol gives a normalized RMSE of #G.synthetic_nrmse%, against
  #G.gru.nrmse% on the real trace, which shows that the protocol itself can fit a forecastable series.
  The comparison that matters for scaling is not RMSE alone. The scaler acts on the largest value of the
  envelope, so a forecaster that is accurate on average but late on a rising edge still provisions late.
]

= Experimental setup <sec:setup>
*Testbed.* Two k3d clusters run on one host. The Kubernetes cluster has one static worker plus the
dynamic node tier, and each Kubernetes worker is limited to one CPU with Docker. The Knative cluster has
one three-CPU worker, and its autoscaler keeps three to ten pods, so Knative never scales to zero. Every
request computes the 33rd Fibonacci number and then waits 50 ms to simulate I/O.

*Workload.* k6 replays a 20-minute ClarkNet window (40 steps of 30 s) at a mean of 73 RPS and a peak of
164 RPS. The SLO is a p99 latency of 200 ms. A request over 200 ms counts as one SLO violation.

*Scenarios and design.* @tab:scenarios lists the four scenarios. In one batch, S1, S2, S3 and S4 ran
five times each. The S3 against S4 comparison then ran in counterbalanced pairs, each pair starting from
one static worker and both runs of a pair using the same provisioning delay. Three paired batches used
the ClarkNet-trained GRU of @sec:gru: A (5 pairs), B (10 pairs) and C (10 pairs, with the test fixed in
advance). The primary endpoint is the per-run p99. We use a one-sided exact paired permutation test, a
bootstrap 95% interval and the paired Cohen's $d$. A run counts only if it passes validity gates. In S4
these require that every eligible forecast arrives, that the horizon covers the provisioning delay, and
that at least one forecast changes the replica target. All #H.b10b.valid of #H.b10b.runs runs of batch
C passed, with #H.b10b.delivered of #H.b10b.eligible forecasts delivered. Runs in batches B and C also
record the host's CPU-busy fraction.

*Cost.* Costs are projected onto AWS prices. Kubernetes maps to an EKS control plane plus t3.medium
nodes sized from mean Kubernetes CPU use, and Knative maps to Lambda with provisioned concurrency sized
from the serverless request rate. A 20-minute run is scaled to a 30-day month. The projection charges
nodes, not pod-seconds, so it does not resolve differences smaller than about one node-month.

#tab-scenarios <tab:scenarios>

#if extended [
  *Run conditioning.* The harness that ran the paired batches sets the static worker count, deletes
  leftover dynamic nodes and their pods, and checks that both backends serve and that the prediction
  server answers when the scenario needs it. Each run records the hash of the deployed predictor in its
  manifest. A hybrid run must also engage the node tier: a pod must become unschedulable or a dynamic
  node must be provisioned. The paired runs cycle the provisioning delay through 60, 90, 120, 75 and
  45 s, one value per pair, so the pair difference carries no boot-time confound. The host CPU-busy
  fraction is sampled from `/proc/stat` through the run.

  *Cost model.* Kubernetes nodes are counted as the mean CPU use divided by the allocatable CPU of one
  node at the target utilization, rounded up, plus one, and each dynamic node adds its measured lifetime.
  Lambda provisioned concurrency follows Little's law from the serverless request rate and the measured
  execution time.
]

= Results <sec:results>
== The hybrid against single-platform baselines
@tab:four compares the four scenarios. Serverless alone gave the lowest tail latency, at
#F.s2.cost USD per month, more than twice the projected cost of any scenario with Kubernetes. The two
hybrids cost the same as Kubernetes with HPA and used #F.s4_pods_below_s1% (S4) and
#F.s3_pods_below_s1% (S3) fewer pod-seconds. S4 held p99 at #F.s4.p99 ms, #F.s4_vs_s1.abs_pct% lower
than S1 (two-sided Mann-Whitney $p = #F.s4_vs_s1.p$, five runs per arm). S3 had the highest mean and
spread in this batch. This batch ran before the leak-free GRU of @sec:gru existed. Its S4 arm used an
earlier GRU whose envelope lay about 10 RPS above the point forecast, against #G.offset_min to
#G.offset_max RPS for the leak-free model, so its S4 row does not measure the forecaster of @sec:gru.
Only the paired batches below do.

#tab-four <tab:four>

#if extended [
  #fig-boxplot <fig:boxplot>

  @fig:boxplot shows the runs behind @tab:four. Every S1, S2 and S4 run stayed under the SLO, and one S3
  run did not. The comparison with S2 is not even: S2 ran on three always-warm pods on a three-CPU node,
  while S1 started from one one-CPU worker. Part of the latency advantage of S2 therefore comes from more
  initial capacity and from the absence of cold starts.
]

== Predictive against reactive control
@tab:h2 and @fig:forest give the paired results. Batch A favoured S3, batch B favoured S4 without
significance, and batch C gave #H.b10b.diff ms ($p = #H.b10b.p$, $d = #H.b10b.d$), with S4 winning
#H.b10b.wins of #H.b10b.n pairs. The hypothesis that predictive scaling lowers p99 relative to reactive
scaling is not supported. Pooled over #H.pooled.n pairs, the difference is #H.pooled.diff ms and the
interval spans zero. The pooled estimate is not stratified across batches that ran under different host
load, so we report it as descriptive.

#tab-h2 <tab:h2>
#fig-forest <fig:forest>

Host load is associated with part of the spread between batches. In batch B, peak host CPU-busy
correlated with p99 at $r = #H.b10a.busy_p99_r$. A post-hoc subset of the #H.b10a.quiet.n pairs of batch
B in which both runs stayed under 0.4 peak CPU-busy gave #H.b10a.quiet.diff ms (uncorrected
$p = #H.b10a.quiet.p$). Batch C, run on a quieter host with mean CPU-busy between #H.b10b.busy_avg_min
and #H.b10b.busy_avg_max, did not reproduce it.

#if extended [
  In batch C the correlation fell to $r = #H.b10b.busy_p99_r$, and #H.b10b.busy_peak_over_half of 20
  runs still had a host CPU-busy peak above 0.5. Mean SLO violations per run were #H.b10b.slo_s3 for S3
  and #H.b10b.slo_s4 for S4. An earlier five-pair batch reported a significant S4 advantage. Its run
  manifests do not identify the deployed predictor, and the predictor of that period was trained on a
  synthetic trace, so we do not count it as evidence for the ClarkNet-trained GRU.
]

== Why the forecast did not help
The forecast changed the replica count. S4 made #H.b10b.proactive proactive scale-ups over the ten runs
of batch C and used #H.b10b.replica_pct% more pod-seconds than S3. The extra pods lowered the serverless
share of the HAProxy weight-time product only from #H.b10b.share_s3% to #H.b10b.share_s4%, and the
fraction of time with any traffic to Knative from #H.b10b.active_s3% to #H.b10b.active_s4%. This is
consistent with the router having already sent the excess to Knative while pods and nodes started. The
projected cost did not change (USD #H.b10b.cost_s3 against #H.b10b.cost_s4 per month), because both arms
used the same node tier. The upper envelope adds #G.offset_min to #G.offset_max RPS to a load whose mean
is 73 RPS, so S4 asked for near-peak capacity early and kept it for the 90 s hold.

#if extended [
  Both arms provisioned about #H.b10b.nodes dynamic nodes per run, and the first dynamic node became
  ready #H.b10b.delay_min to #H.b10b.delay_max s after it was requested. During that window the router
  moved the excess load to Knative in both arms. We did not record which backend served the slowest
  requests, so we cannot yet say whether the remaining tail comes from Knative, from Kubernetes pods
  that are still starting, or from the shared host.
]

= Discussion <sec:discussion>
Our results are consistent with the following explanation. Inside a hybrid, the serverless backend
absorbs the provisioning gap that the forecast was meant to close, so the forecast adds idle replicas
without lowering latency. We did not test this directly, for example by removing the serverless
backend. A forecast is more likely to help where no overflow backend exists, where the serverless
backend cannot absorb the whole gap, or where a scale-down would drain capacity that the load needs
again soon. The paired batches tested none of these cases.

*Threats to validity.* All clusters share one host, so the testbed simulates two platforms rather than
two clouds. The cost is a projection of measured resource use onto public prices, not a bill. In batch C
the pair differences have an sd of #H.b10b.diff_sd ms, so ten pairs detect, with 80% power, only effects
larger than about #H.b10b.mde ms. The GRU is no more accurate than a linear autoregression, and its upper
envelope adds #G.offset_min to #G.offset_max RPS. A persistence or linear forecast with the same margin
may therefore reproduce S4, and we did not test it. The four-scenario batch ran S4 with an earlier GRU,
so the S1 and S2 comparisons hold for the architecture, not for the forecaster of @sec:gru.

#if extended [
  The workload is one 20-minute window of one trace, served by one function. The provisioning delay is
  simulated by a timer, not measured from a cloud provider. Batch B ran while other processes loaded the
  host, with mean CPU-busy up to #H.b10a.busy_avg_max, and batch A has no host record. The scenarios ran
  with one parameter set for Algorithm 2. A smaller envelope offset or a shorter hold would change what
  the forecast costs, and we did not test them.
]

= Conclusion
We built a hybrid control architecture in which a capacity-aware router and an ElaX-derived replica
scaler run in one 15 s loop, and we extended the scaler's decision factor with a 135 s GRU upper
envelope. In the four-scenario batch the hybrid cost the same as Kubernetes with HPA and used fewer
pod-seconds. In a pre-specified batch of ten pairs, the forecast added replicas but no measurable
latency gain over reactive control. Future work will compare the GRU with a constant-margin baseline, set
the margin from the measured provisioning delay, and test the scaler without a serverless backend, where
a forecast has a gap to close.

#if extended [
  = Data availability
  The run bundles, the analysis code and the script that derives every number in this paper from the
  bundles are available from the corresponding author on request.
]
]
