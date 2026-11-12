// Paper body shared by both builds. `extended: false` is the six-page conference paper;
// `extended: true` adds the journal-only material inside `#if extended [...]` blocks.
// Numbers come from common.typ (numbers.json); never type a measured value here.
// One name per thing: pod (one running copy of the service), replica count (the number of
// pods the scaler asks for), router (Algorithm 1), replica scaler (Algorithm 2), forecast
// (the GRU output), margin (delta_k), upper envelope (forecast plus margin), provisioning
// delay, reactive hybrid (S3), predictive hybrid (S4), scenario batch, batches A to C.
#import "common.typ": *

#let abstract = [
  A hybrid of Kubernetes and a serverless platform serves the base load on Kubernetes pods and sends the
  overflow to the serverless backend. We ask whether a load forecast still helps the Kubernetes replica
  scaler in such a hybrid, where the serverless backend already takes load while new pods and nodes
  start. Every 15 s, a router sends to Knative the load above the capacity of the ready Kubernetes
  pods, and a replica scaler derived from ElaX sizes the Kubernetes deployment. We extend the decision
  factor of the scaler with forecasts from a gated recurrent unit (GRU): the largest forecast value
  over the next 135 s plus a safety margin. Under a protocol that keeps test data out of training and
  tuning, the GRU
  reduces the error of a persistence forecast by #G.gru.skill_pct% but does not beat a linear
  autoregression. On a CPU-bounded testbed that replays the ClarkNet trace, both hybrids matched the
  projected cost of Kubernetes with the Horizontal Pod Autoscaler (HPA). The reactive hybrid had a
  higher 99th-percentile latency (p99) than the HPA, and Knative alone was the fastest at more than
  twice the cost. In ten pre-specified pairs of runs, adding the forecast to the reactive hybrid changed
  p99 by #H.b10b.diff ms (95% CI \[#H.b10b.ci_lo, #H.b10b.ci_hi\], $p = #H.b10b.p$) and used
  #H.b10b.replica_pct% more pod-seconds, in a design that detects differences above about
  #H.b10b.mde ms.
]

#let keywords = ([Kubernetes], [serverless computing], [autoscaling], [workload prediction],
  [gated recurrent unit], [traffic routing])

#let body(extended: false) = [
= Introduction
A Kubernetes deployment scales on load that it has already observed. The Horizontal Pod Autoscaler (HPA)
compares CPU use with a target and adds pods, the running copies of a service, after the target is
crossed @serracanta2025hpa. When the cluster also lacks nodes, a new virtual machine takes about one to
two minutes to start @hao2021vmstartup. Until the new pods are ready, requests queue and the
99th-percentile latency (p99) rises. Serverless platforms react faster. They add instances within
seconds @demystifying2025, but a new instance pays a cold-start delay @golec2023cold. Public serverless
platforms also charge higher unit prices plus a per-invocation fee @demystifying2025, and sustained load
is several times more expensive there than on virtual machines @dehigama2024.

A hybrid deployment uses both. Reserved machines serve the stable base load, and serverless functions
serve the excess @dehigama2024. A hybrid of Kubernetes and a serverless backend makes two decisions in
every control cycle: how many Kubernetes pods to run, and what share of the traffic to send to the
serverless backend. The two decisions interact. A pod that is added early lowers the serverless share.
A serverless backend that absorbs a burst also masks the latency cost of a pod that is added late.

ElaX @yang2019elax makes the first decision, the pod count, from a forecast for one container cluster.
Once an hour an LSTM predicts the load of the next 60 minutes. ElaX reserves resources for the largest
predicted value through a linear resource model, and a slack-based controller corrects the reservation
online. ElaX does not split traffic between backends, and its hourly horizon is long next to the
minute-scale surges of web traffic.

This paper asks whether ElaX's forecast-driven scaling decision still helps inside a hybrid, where the
serverless backend already takes load during the provisioning delay. MArk @zhang2019mark and Spock
@gunasekaran2019spock have this structure on virtual machines: a forecast sizes the machines, and
requests that the machines cannot serve go to serverless functions. We build it on Kubernetes pods and
Knative, a serverless platform that runs on Kubernetes, and we run the same router with and without the
forecast. The contributions are the following.
+ A control architecture in which one 15 s loop runs a capacity-aware router (Algorithm 1) and a replica
  scaler (Algorithm 2) for Kubernetes and Knative, under a service-level objective (SLO) of 200 ms for
  p99.
+ An extension of ElaX's scaling decision with multi-step GRU forecasts. A GRU replaces the LSTM,
  forecasts nine 15 s steps and refreshes in every cycle. The scaler sizes for the largest value of the
  forecast plus a margin (the upper envelope) over 135 s. The router does not read the forecast. We
  train and test the GRU under a leak-free protocol: no test data, and no data that overlaps a split
  boundary, enters training or tuning.
+ An evaluation in two parts. A scenario batch compares the reactive hybrid (S3) and the predictive
  hybrid (S4) with Kubernetes under the HPA (S1) and with Knative alone (S2). Paired batches then
  compare S4 with S3, with validity checks on every run.

The GRU does not beat a linear autoregression. Both hybrids matched the projected cost of S1, but the
reactive hybrid had a higher p99 than S1. In ten pre-specified pairs, the forecast used
#H.b10b.replica_pct% more pod-seconds and gave no measurable latency gain, in a design that detects
differences above about #H.b10b.mde ms. The lower end of its 95% interval is #H.b10b.ci_lo ms, so a
larger p99 reduction is unlikely in this setup.

= Related work <sec:related>
*Hybrid execution.* The closest systems pair virtual machines with serverless functions. MArk provisions
virtual machines from a load forecast and serves on AWS Lambda the requests that the machines cannot
serve in time @zhang2019mark. Spock sizes virtual machines from a forecast, uses serverless functions
to cover their scale-out lag, and compares a reactive with a predictive scale-out policy
@gunasekaran2019spock. In both systems the forecast sizes the base tier, and the overflow rule does not
read it. Our design has the same split. It differs in the base tier, which is Kubernetes pods with a
node tier under them, and in the evaluation, which keeps one router and pairs runs with and without the
forecast. PulseNet sends a request to fast, disposable instances when no regular Knative instance is
free @pulsenet2025, so both of its tracks are serverless. LA-IMR routes inference requests across edge
and cloud tiers and scales Kubernetes replicas from a predicted latency in one controller @laimr2026.

*Autoscaling with forecasts.* HyPA combines reactive and model-based horizontal scaling and refits its
model when the forecast error rises @hypa2023. KAPETÁNIOS adapts HPA parameters through a digital twin
of the cluster @kapetanios2022. Forecast-based scalers for Kubernetes use time-series models of CPU use
@mondal2023toward or of the request rate @yuan2024time. AAPA adds archetype awareness and uncertainty
estimates for serverless workloads @aapa2025, and ADAPT estimates the cold-start duration online and
sets its planning horizon from it @adapt2026. Each of these systems scales one platform. A recent
benchmark finds that a calibrated rule-based autoscaler beats six deep reinforcement learning
algorithms on cost @rayscale2026.

*Serverless cost and cold starts.* A survey of serverless resource management names the start-up delay
of new function instances as a challenge for autoscaling @mampage2022holistic. Benchmarks measure
cold-start latency @yu2020characterizing @sebs2020, and SeBS shows that billing rounds up time and
memory, so users pay for resources that they do not use @sebs2020. Billing practices @demystifying2025
and the CPU and memory overhead of keeping instances warm @highcost2025 raise the cost further.

#if extended [
  *Scheduling and scaling control.* A survey of Kubernetes scheduling includes a category of
  autoscaling-enabled scheduling @senjab2023survey. Containers also pay a start-up cost when a
  deployment scales out @beni2021reducing. Forecasts have been used to start serverless functions before
  requests arrive @jegannathan2022time, and reinforcement learning to decide how long to keep them warm
  @vahidinia2023mitigating. AutoScale waits before it turns off an idle server, so that capacity which
  the load needs again is not lost @gandhi2012autoscale. STaleX adapts per-service scaling to service
  dependencies and to workload variation over time @stalex2025.
]

*ElaX.* @tab:elax lists what Algorithm 2 keeps from ElaX and what it changes. ElaX reserves for the
maximum predicted workload of the next hour through a fitted linear model. Algorithm 2 keeps this
forecast-then-reserve structure and the rule of sizing for the largest predicted value. It changes the
predictor, the horizon, the refresh period and the decision factor, and it runs next to a router that
splits traffic between two backends, which ElaX does not do.

#tab-elax <tab:elax>

= Control architecture <sec:design>
#fig-architecture <fig:arch>

@fig:arch shows the system. HAProxy receives all requests and splits them between a Kubernetes
deployment and a Knative service by two weights. A control daemon runs a 15 s loop. In each cycle it
reads the load $x$ in requests per second (RPS) and the p99 from Prometheus, reads the number of ready
pods $n$ from the Kubernetes API, and runs two algorithms. A pod is ready when it passes its readiness
probe and can take traffic.

== Algorithm 1: capacity-aware router
One ready pod serves $r_"eff" = r_"sat" dot u = 33.3 times 0.5 = 16.65$ RPS. Here $r_"sat"$ is the
measured saturation throughput of three pods divided by three, and $u$ is the target utilization. The
ready capacity is $C = n dot r_"eff"$. Kubernetes keeps the load up to $C$, and Knative takes the excess
through the serverless weight, in percent:
$ w_"sls" = cases(0 & "if" x <= C, min(50, ceil(100 (x - C) \/ x)) & "otherwise.") $
The weight moves to its target in one cycle (@alg:routing). The cap of 50% bounds the serverless cost
when the Kubernetes capacity falls far short of the load. The weight follows the observed load and the
ready pods. A forecast changes it only through the pods that Algorithm 2 adds. The implementation also
has a pacing term in the style of BACC @bacc2026, which can add serverless weight when SLO violations
accumulate. It counts at most one violation per cycle, so it cannot reach its threshold within one run,
and @alg:routing omits it.

#alg-routing <alg:routing>

#if extended [
  With eight ready pods, $C = 133.2$ RPS, and the cap binds only above 266 RPS. The replayed trace peaks
  at 164 RPS, so the cap never bound in the reported runs. The router starts each hybrid run at a 20%
  serverless weight, and the first decision corrects it. When it enables serverless, Algorithm 1 also
  sends one warm-up request to Knative. With three pods always running this request has no effect, and in
  the paired batches its endpoint returned HTTP 404.
]

== Algorithm 2: ElaX-derived replica scaler with a forecast
Algorithm 2 computes the replica count from a load value $v$, the decision factor, with the linear model
$R(v) = "clamp"(ceil(alpha v + beta), R_min, R_max)$, where $alpha = 1 \/ r_"eff"$, $beta = 0$,
$R_min = 3$ and $R_max = 10$. The reactive hybrid (S3) uses $v = x_"obs"$, the mean load over the last
30 s. The predictive hybrid (S4) also computes a forecast target from the upper envelope of the GRU
forecast,
$ hat(u)_(t+k) = hat(y)_(t+k) + delta_k, quad k = 1, dots, 9, $
where $hat(y)_(t+k)$ is the point forecast and the margin $delta_k$ is the 90th percentile of the
positive validation residuals at step $k$. Its decision factor is the largest envelope value,
$v = max_k hat(u)_(t+k)$. ElaX also takes the maximum over its horizon, but over point forecasts for
one hour. Algorithm 2 applies the forecast target when it exceeds $R(x_"obs")$ and then holds it for
90 s (@alg:scaling). Scale-down requires the target to fall under 0.75 of the current replica count,
120 s since the last scale-down, and a p99 under 140 ms.

#alg-scaling <alg:scaling>

Three choices separate this decision factor from a plain forecast. It uses the upper envelope and not
the point forecast, because a pod that arrives late costs SLO violations and a pod that arrives early
costs idle time. The forecast can raise the target but cannot lower it, so a forecast error cannot
remove pods that the observed load needs. The 90 s hold keeps a raised target through short dips, so
the scaler does not remove pods that the next forecast asks for again.

== Node tier
Pods that cannot be scheduled trigger a node autoscaler. A timer stands in for the start of a virtual
machine: the autoscaler waits a provisioning delay of 45 to 120 s, close to the start-up times measured
in public clouds @hao2021vmstartup, and then adds a one-CPU worker. It removes a dynamic node when the
CPU utilization of the node falls below 50%. This value is the default scale-down threshold of the
Cluster Autoscaler, which applies it to pod requests @k8sca-faq. The forecast horizon of 135 s covers
the longest delay plus one control cycle.

= GRU forecaster <sec:gru>
*Model.* A two-layer GRU @cho2014learning @chung2014empirical with #G.hidden hidden units reads the last
30 samples of the load, one sample per 15 s, and emits all nine future steps from one dense head. The
forecast server answers in #G.latency.median ms (median; p95 #G.latency.p95 ms), which is small next to
the 15 s cycle.

*Leak-free protocol.* The ClarkNet HTTP trace @clarknet is aggregated into 15 s buckets and multiplied
by 33, the factor that the replay uses. We split the series in time order into training, validation and
test portions. A gap of 38 samples (input length plus horizon minus one) at each boundary, the embargo,
ensures that no input window or target spans two portions. The input normalization is fitted on the
training portion. We select the hyperparameters and the epoch budget on the validation portion with the
Tree-structured Parzen Estimator @bergstra2011tpe of Optuna @optuna2019. The test portion stays out of
the selection, because a score from data that also guided the selection is biased
@cawley2010overfitting. We then train the selected configuration with three seeds and evaluate each
model once on the test portion. The 20-minute window that the experiments replay lies inside the test
portion, so the deployed model never saw it.

#if extended [
  The search ran #G.trials trials for each input length (#G.seq_searched samples) on the first seed and
  selected a dropout of #G.dropout, a learning rate of #G.lr and a budget of #G.epochs epochs. The margins
  $delta_k$ come from the validation residuals of the selected model and range from #G.offset_min to
  #G.offset_max RPS over the nine steps. On the test portion, the upper envelope covered #G.gru.coverage
  of the values that the point forecast under-predicted, against a target of 0.90.
]

*Accuracy.* @tab:predictor reports the error on the test portion at the 9-step horizon, in RPS of the
replayed series, with the standard deviation over three seeds. Skill is the share of the error of a
persistence forecast, which repeats the last observed value, that a model removes. The GRU has a skill
of #G.gru.skill. Its error is slightly lower than that of an LSTM, the predictor family of ElaX,
selected in the same way. The final LSTM was trained on the training plus validation portions and the
final GRU on the training portion, which favours the LSTM. The GRU does not beat a linear autoregression
on the same inputs. We also screened #G.levers variants: input transforms, a target transform, coarser
sampling intervals, a decomposed input and two other architectures. None of them beat the linear model
on the folds that we used for selection.

#tab-predictor <tab:predictor>

#if extended [
  The error grows with the horizon at the same rate for both models: the GRU RMSE rises from #G.gru_h1 at
  the first step to #G.gru_h9 at the ninth, and the linear model from #G.ols_h1 to #G.ols_h9. The input
  transforms were differencing, exponential and rolling statistics, robust and quantile scaling, and
  reversible instance normalization, and the two other architectures were N-BEATS and a linear network.
  Each variant was screened against the same linear baseline. The GRU kept one advantage over the LSTM
  outside the ClarkNet test portion: on a synthetic spike archetype its RMSE was #G.gru.spike against
  #G.lstm.spike. On a synthetic trace, the same protocol gives a normalized RMSE of #G.synthetic_nrmse%,
  against #G.gru.nrmse% on the real trace, which shows that the protocol itself can fit a forecastable
  series. The comparison that matters for scaling is not RMSE alone. The scaler acts on the largest value
  of the envelope, so a forecaster that is accurate on average but late on a rising edge still provisions
  late.
]

= Experimental setup <sec:setup>
#tab-scenarios <tab:scenarios>

*Testbed.* Two clusters run on one host under k3d, which runs Kubernetes nodes as containers. The
Kubernetes cluster has one static worker plus the dynamic nodes of @sec:design, and Docker limits each
of these workers to one CPU. The Knative cluster has one three-CPU worker, and its autoscaler keeps
three to ten pods, so Knative never scales to zero. Each pod requests 0.3 CPU. Every request computes
the 33rd Fibonacci number and then waits 50 ms to simulate I/O.

*Workload.* The load generator k6 replays a 20-minute ClarkNet window (40 steps of 30 s) at a mean of
73 RPS and a peak of 164 RPS. The SLO is a p99 of 200 ms, and a request slower than 200 ms counts as one
SLO violation.

*Scenarios and batches.* @tab:scenarios lists the four scenarios. In the scenario batch, S1, S2, S3 and
S4 ran five times each. The comparison of S4 with S3 then ran in pairs. The two runs of a pair start
from one static worker and use the same provisioning delay, which cycles through 60, 90, 120, 75 and
45 s from pair to pair. The order of S3 and S4 alternates between pairs (counterbalancing), so drift of
the host does not favour one arm. Three paired batches used the leak-free GRU of @sec:gru: A (5 pairs),
B (10 pairs) and C (10 pairs). Each batch recorded its primary endpoint and its test level in the run
profile before the first run. B and C ran the same ten-pair profile. B ran while other processes loaded
the host, so C repeated it on a quieter host, and we treat C as the confirmatory batch. An earlier batch
of five pairs showed a significant advantage for S4. Its run manifests do not identify the predictor,
and the predictor of that period was trained on a synthetic trace, so we do not count it as evidence for
the leak-free GRU.

*Tests and validity.* The primary endpoint is the per-run p99, the 99th percentile of all request
latencies in one run. For the paired batches we use a one-sided exact paired permutation test
(alternative: S4 is faster) at a level of 0.05, a bootstrap 95% interval and the paired Cohen's $d$. A
run counts when it passes validity checks. A hybrid run must engage the node tier: a pod must become
unschedulable or a dynamic node must be provisioned. An S4 run must also receive every eligible
forecast, have a horizon that covers the provisioning delay, and change the replica target through a
forecast at least once. Every run of the three paired batches passed (#H.b5.valid of #H.b5.runs,
#H.b10a.valid of #H.b10a.runs and #H.b10b.valid of #H.b10b.runs), and batch C received #H.b10b.delivered
of #H.b10b.eligible forecasts. Batches B and C also record the CPU-busy fraction of the host, the share
of non-idle CPU time sampled from `/proc/stat` during a run.

*Cost.* We project the cost onto AWS prices. Kubernetes maps to an EKS control plane plus t3.medium
nodes sized from the mean Kubernetes CPU use, and Knative maps to Lambda with provisioned concurrency
sized from the serverless request rate. We scale a 20-minute run to a 30-day month. The projection
charges nodes, not pod-seconds, so it does not resolve differences smaller than about one node-month.

#if extended [
  *Run conditioning.* The harness that ran the paired batches sets the static worker count, deletes
  leftover dynamic nodes and their pods, and checks that both backends serve and that the prediction
  server answers when the scenario needs it. Each run records the hash of the deployed predictor in its
  manifest.

  *Cost model.* Kubernetes nodes are counted as the mean CPU use divided by the allocatable CPU of one
  node at the target utilization, rounded up, plus one, and each dynamic node adds its measured lifetime.
  Lambda provisioned concurrency follows Little's law from the serverless request rate and the measured
  execution time.
]

= Results <sec:results>
== The hybrid against single-platform baselines
@tab:four and @fig:runs compare the four scenarios. The table gives p99 with its standard deviation,
the SLO violations in a run of about #F.requests requests, the time average of the serverless weight,
the Kubernetes pod-seconds per run and the projected monthly cost. S2 gave the lowest p99, at #F.s2.cost USD per month,
more than twice the projected cost of any scenario with Kubernetes. The comparison with S2 is uneven:
S2 ran three always-warm pods on a three-CPU worker, and S1 started from one pod on a one-CPU worker.
The two hybrids had the same projected cost as S1 within the resolution of the projection. They used
#F.s3_pods_below_s1% (S3) and #F.s4_pods_below_s1% (S4) fewer Kubernetes pod-seconds than S1. This count
excludes Knative pods, and each hybrid also kept at least three Knative pods warm, so it is not a saving
in total pods. The reactive hybrid did not improve latency over the HPA. Its p99 was #F.s3.p99 ms
against #F.s1.p99 ms for S1, with more SLO violations, and one of its five runs exceeded the SLO.

#tab-four <tab:four>
#fig-runs <fig:runs>

The S4 results need a caveat. This batch ran before the leak-free GRU of @sec:gru existed. Its run
manifests do not record the predictor, and its logged envelope lay about 10 RPS above the point
forecast, against #G.offset_min to #G.offset_max RPS for the leak-free GRU. S4 held p99 at #F.s4.p99 ms
in this batch, #F.s4_vs_s1.abs_pct% below S1 (two-sided Mann-Whitney $p = #F.s4_vs_s1.p$), but the row
does not measure the forecaster of @sec:gru. The paired batches do.

== Predictive against reactive control
@tab:h2 and @fig:forest give the paired results. Batch A favoured S3, batch B favoured S4 without
significance, and the confirmatory batch C gave #H.b10b.diff ms ($p = #H.b10b.p$, $d = #H.b10b.d$), with
S4 faster in #H.b10b.wins of #H.b10b.n pairs. The data do not support the hypothesis that the forecast
lowers p99 relative to reactive scaling. The pair differences of batch C have a standard deviation of
#H.b10b.diff_sd ms, so ten pairs detect, with 80% power, differences above about #H.b10b.mde ms. The
lower end of the interval, #H.b10b.ci_lo ms, bounds the gain that the data still allow. In batches A and
B the mean p99 of both arms was above the 200 ms SLO, and in batch C it was below. Pooled over
#H.pooled.n pairs the difference is #H.pooled.diff ms and the interval spans zero. The batches ran under
different host load, so the pooled row is descriptive.

#tab-h2 <tab:h2>
#fig-forest <fig:forest>

The batches differ in host load. In batch B, the peak CPU-busy fraction of the host correlated with p99
(Pearson correlation #H.b10a.busy_p99_r). A post-hoc subset of the #H.b10a.quiet.n pairs of batch B in
which both runs stayed under a peak of 0.4 gave #H.b10a.quiet.diff ms (uncorrected
$p = #H.b10a.quiet.p$). Batch C repeated the design on a quieter host, with a mean CPU-busy fraction
between #H.b10b.busy_avg_min and #H.b10b.busy_avg_max, and did not reproduce that difference.

#if extended [
  In batch C the correlation fell to #H.b10b.busy_p99_r, and #H.b10b.busy_peak_over_half of 20 runs still
  had a host CPU-busy peak above 0.5. Mean SLO violations per run were #H.b10b.slo_s3 for S3 and
  #H.b10b.slo_s4 for S4.
]

== What the forecast changed
The forecast changed the replica count. In batch C, S4 made #H.b10b.proactive scale-ups in which the
forecast target exceeded the observed-load target, and it used #H.b10b.replica_pct% more pod-seconds
than S3. The margin alone is #G.offset_min to #G.offset_max RPS on a load whose mean is 73 RPS, which is
three to four pods, and the hold keeps them for 90 s. The extra pods lowered the time average of the
serverless weight from #H.b10b.share_s3% to #H.b10b.share_s4%, and the fraction of time with any traffic
to Knative from #H.b10b.active_s3% to #H.b10b.active_s4%. The projected cost did not change (USD
#H.b10b.cost_s3 for S3 and #H.b10b.cost_s4 for S4 per month), because both arms used the same node tier.

Both arms provisioned about #H.b10b.nodes dynamic nodes per run, and the first one became ready
#H.b10b.delay_min to #H.b10b.delay_max s after the request. In that window the router moved the excess
load to Knative in both arms. We did not record which backend served the slowest requests. We therefore
cannot say whether the remaining tail comes from Knative, from Kubernetes pods that are still starting,
or from the shared host.

= Discussion <sec:discussion>
One explanation fits these results. Inside a hybrid, Knative takes the load during the provisioning
delay that the forecast was meant to cover, so the forecast adds idle pods without a latency gain. We did
not test this explanation, for example by removing the Knative backend. A forecast is more likely to
help in three cases that the paired batches did not cover: when no overflow backend exists, when the
overflow backend cannot take the whole excess, and when a scale-down removes capacity that the load
needs again soon.

*Threats to validity.* All clusters share one host, so the testbed simulates two platforms and not two
clouds. A timer simulates the provisioning delay. The workload is one 20-minute window of one trace,
served by one function, and Algorithm 2 ran with one parameter set. A smaller margin or a shorter hold
would change what the forecast costs. The cost is a projection of measured resource use onto public
prices, not a bill. The GRU is no more accurate than a linear autoregression, and its margin is large,
so a persistence or linear forecast with the same margin may reproduce S4. Batch B ran on a loaded host,
with a mean CPU-busy fraction up to #H.b10a.busy_avg_max, and batch A has no host record. The scenario
batch ran S4 with an earlier GRU, so its comparisons with S1 and S2 hold for the architecture and not
for the forecaster of @sec:gru.

= Conclusion
A capacity-aware router and an ElaX-derived replica scaler ran in one 15 s loop over Kubernetes and
Knative, and the scaler read the upper envelope of a 135 s GRU forecast. Both hybrids matched the
projected cost of Kubernetes with the HPA, and the reactive hybrid had a higher p99. In ten
pre-specified pairs, the forecast added pods and gave no measurable latency gain over reactive control,
in a design that detects differences above about #H.b10b.mde ms.
Future work will compare the GRU with a constant-margin baseline, set the margin from the measured
provisioning delay, and test the scaler without a serverless backend, where a forecast has a delay to
cover.

#if extended [
  = Data availability
  The run bundles, the analysis code and the script that derives every number in this paper from the
  bundles are available from the corresponding author on request.
]
]
