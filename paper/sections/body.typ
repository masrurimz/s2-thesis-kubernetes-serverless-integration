// Paper body shared by both builds. `extended: false` is the six-page conference paper;
// `extended: true` adds the journal-only material inside `#if extended [...]` blocks.
// Numbers come from common.typ (numbers.json); never type a measured value here.
// One name per thing, and names instead of codes: HPA baseline (S1), Knative baseline (S2),
// reactive hybrid (S3), predictive hybrid (S4); pilot batch (b5), loaded-host batch (b10a),
// confirmatory batch (b10b). Pod, replica count, router (Algorithm 1), replica scaler
// (Algorithm 2), forecast, margin, upper envelope, hold, provisioning delay.
// Structure: every paragraph opens with the question it answers and ends with its answer;
// each sentence starts from what the previous one ended on. Keep the conference text's
// concept count low: a side thread goes into an `#if extended` block, not into the six pages.
#import "common.typ": *

#let abstract = [
  Kubernetes serves steady load cheaply but adds capacity late, and when no node has room, a new virtual machine
  takes one to two minutes to start. Serverless platforms scale within seconds but cost more for steady load.
  We propose a hybrid that keeps the base load on Kubernetes, sends the excess to the serverless platform
  Knative, and extends the ElaX autoscaler with a gated recurrent unit (GRU) workload forecast so that pods are
  added before the load arrives. We compare the hybrid with Kubernetes alone and Knative alone, and we test
  whether the forecast improves tail latency and cost. A reactive
  version of the scaler uses only the current load, while the predictive version also uses the GRU forecast of
  the next 135~s with a safety margin. The reactive hybrid cost about as much as Kubernetes alone and less than
  half as much as Knative alone, but it had a higher tail latency than Kubernetes alone. Over ten
  pairs of back-to-back runs of the two versions, the predictive version used #H.b10b.replica_pct% more pods,
  which fit on the same nodes, so the projected cost stayed the same, yet its 99th-percentile latency did not
  improve measurably. The difference was #H.b10b.diff ms (95% CI \[#H.b10b.ci_lo, #H.b10b.ci_hi\],
  $p = #H.b10b.p$), and the test could have detected a change of about #H.b10b.mde ms. This suggests that, because Knative already
  serves the excess while new pods start, a forecast has little left to improve. The GRU was also no more
  accurate than a linear model.
]

#let keywords = ([Kubernetes], [serverless computing], [autoscaling], [workload prediction],
  [gated recurrent unit], [traffic routing])

#let body(extended: false) = [
= Introduction
Web services often promise that 99% of requests finish within a fixed time. This promise is a service-level
objective (SLO) on the 99th-percentile latency (p99), and it must hold even when the load changes from minute to
minute. On Kubernetes, this promise is hardest to keep during a surge, because capacity follows the load instead
of leading it. The Horizontal Pod Autoscaler (HPA) adds pods, the running copies of a service, only after their CPU
use has crossed a target @serracanta2025hpa. When no node has room for the new pods, the cluster must first start
a virtual machine, which takes one to two minutes @hao2021vmstartup, and the requests that arrive during this
provisioning delay wait in a queue and break the SLO.

There are two ways to close this delay. A workload forecast can hide it by adding capacity before the load
arrives, as ElaX, an autoscaler for container clusters, does with an hourly long short-term memory (LSTM)
forecast @yang2019elax. A serverless platform can absorb it instead, because it adds instances within seconds
@demystifying2025, although each new instance pays a short start-up (cold-start) delay @golec2023cold.
Serverless is expensive for steady load, however, and can cost several times more than virtual machines
@demystifying2025 @dehigama2024, so hybrid deployments keep the base load on their own machines and send only
the excess to serverless @dehigama2024.

We propose a hybrid that uses both ways. It keeps the base load on a Kubernetes deployment and sends the
excess to Knative, an open-source serverless platform. A capacity-aware router decides how much of the load
goes to Knative, and a replica scaler derived from ElaX decides how many pods to run, using a gated recurrent
unit (GRU) forecast so that pods are added before the load arrives. Because serverless already covers part of
the provisioning delay, the forecast may have less left to improve than it would on Kubernetes alone, so we also
test what it adds. We run the scaler in two versions, a reactive one that uses only the current load and a
predictive one that also uses the forecast, and compare them in back-to-back pairs of runs. Our contributions
are as follows.
+ A control loop that decides every 15~s how much load goes to Knative and how many pods Kubernetes runs. The
  forecast changes only the pod count, never the routing, so its effect can be measured alone (@sec:design).
+ An extension of ElaX that replaces its LSTM with a GRU forecast of the next 135~s and adds pods for the
  highest forecast value plus a safety margin (@sec:gru).
+ An evaluation on a running testbed against Kubernetes alone and Knative alone, with the two scaler versions
  compared in back-to-back pairs (@sec:setup, @sec:results). The forecast used #H.b10b.replica_pct% more pods
  but did not measurably lower the tail latency. Because the GRU was no more accurate than a linear model, the
  extra pods may come from the safety margin rather than from the GRU itself.

= Related work <sec:related>
*Hybrid execution.* Four published systems run the base load on virtual machines and send whatever the machines
cannot serve to serverless, but they disagree on whether a forecast is needed. Three of them use a forecast to
decide how many machines to run. MArk forecasts the
peak request rate @zhang2019mark, while LIBRA uses a moving average of the load plus a multiple of its deviation
@libra2021, and both were compared with other provisioning schemes on AWS. Spock uses linear regression to
predict the average rate at the time new machines will be ready @gunasekaran2019spock. It compared a reactive
with a predictive policy and found the predictive one best, but only in an event-driven simulator. The fourth
system, Spandana, uses no forecast at all @spandana2026. It argues that forecasts act over minutes, which is too
coarse for short bursts, and instead steers each request to serverless when its machine cannot meet the SLO. As
far as we found, none of these systems switched its forecast off on a running deployment to measure what it adds. Our work is
closest to Spock but differs in three ways that matter for the result. First, our base tier is Kubernetes, so
capacity grows in two steps, pods when a node has room and nodes only after the provisioning delay. Second,
Spock's forecast sizes the machines for the average rate and leaves the peaks to Lambda, so it avoids extra
machines, whereas ours adds pods early for the predicted peak. Third, we measure a running deployment in paired
runs and test the difference statistically.

*Autoscaling with forecasts.* Many autoscalers forecast the load, but each scales a single platform. Some scale
Kubernetes pods from a forecast of CPU use or of the request rate @mondal2023toward @yuan2024time, refit the
model when its error grows @hypa2023, or tune the HPA through a digital twin of the cluster @kapetanios2022.
Others forecast for serverless functions, either with uncertainty estimates @aapa2025 or with a planning horizon
set from the cold-start time @adapt2026. Since none of them overflows to serverless, none can show how much of a
forecast's benefit remains once such an overflow exists.

*Serverless cost and cold starts.* Serverless overflow has costs of its own. New function instances pay a
start-up delay, which a survey lists as an autoscaling challenge @mampage2022holistic and benchmarks have
measured @yu2020characterizing @sebs2020. Billing also rounds up time and memory @sebs2020, and keeping
instances warm costs CPU and memory @highcost2025. For these reasons our router sends Knative only the load that
Kubernetes cannot serve, and it caps that share.

#if extended [
  *Other hybrids.* Other hybrids route between two serverless paths @pulsenet2025 or between edge and cloud
  tiers @laimr2026, and neither pairs a load forecast with a serverless overflow.

  *Scheduling and scaling control.* A survey of Kubernetes scheduling includes a category of
  autoscaling-enabled scheduling @senjab2023survey. Containers also pay a start-up cost when a deployment
  scales out @beni2021reducing. Forecasts have been used to start serverless functions before requests
  arrive @jegannathan2022time, and reinforcement learning has been used to decide how long to keep them
  warm @vahidinia2023mitigating. AutoScale waits before it turns off an idle server, so that it does not
  lose capacity that the load needs again @gandhi2012autoscale. STaleX adapts the scaling of each service
  to service dependencies and to workload changes over time @stalex2025. A calibrated rule-based autoscaler
  beat six deep reinforcement learning algorithms on cost @rayscale2026.
]

= Control architecture <sec:design>
#fig-architecture <fig:arch>

The architecture has two jobs. It has to serve the load, and it has to let an experiment change the forecast
while everything else stays the same. @fig:arch shows how it does both. A load balancer, HAProxy, splits the
requests between a Kubernetes deployment and a Knative service according to two weights. Every 15~s, a control
daemon collects the load $x$ in requests per second (RPS) and the p99 from the metrics store Prometheus, together
with the number $n$ of ready pods, those that pass their readiness probe, from Kubernetes. It then runs the
router, which sets the weights, and the replica scaler, which sets the pod count. Only the scaler has access to
the forecast.

== Algorithm 1: capacity-aware router
The router works out how much of the load the ready pods can take and sends the rest to Knative. In calibration,
one pod saturated at 33.3 RPS. The router plans each pod at a target utilization of 0.5, so one pod serves
$r_"eff" = 16.65$ RPS and the ready pods together serve $C = n dot r_"eff"$. The serverless weight, in percent, is
$ w_"sls" = cases(0 & "if" x <= C, min(50, ceil(100 (x - C) \/ x)) & "otherwise,") $
and the router applies it at once, without smoothing (@alg:routing). The cap of 50% bounds the serverless cost
when Kubernetes capacity is far below the load. Because the router looks only at ready pods, the forecast can
change the weight only through the pods that the scaler adds.

#alg-routing <alg:routing>

#if extended [
  A pacing term in the code, borrowed from the budget-aware autoscaler BACC @bacc2026, adds serverless weight
  when SLO violations accumulate. It cannot reach its threshold within one run, so @alg:routing omits it.
  The pacing term counts at most one violation per cycle. With eight ready pods, $C = 133.2$ RPS, and the
  cap applies only above 266~RPS. The replayed trace peaks at 164~RPS, so the cap never applied in the
  reported runs. The router starts each hybrid run at a serverless weight of 20%, and the first decision
  corrects it. When Algorithm 1 enables serverless, it also sends one warm-up request to Knative. With
  three pods always running, this request changes nothing. In the paired batches, its endpoint returned
  HTTP 404.
]

== Algorithm 2: ElaX-derived replica scaler with a forecast
The replica scaler decides how many pods to run, and it is the only component that sees the forecast. Its
design rests on an asymmetry. A pod that starts too late causes SLO violations, while a pod that starts too
early only stands idle, so the scaler errs toward too many pods. It turns a load value $v$, which we call the
decision factor, into a replica count $R(v) = ceil(v \/ r_"eff")$, clamped to 3 to 10 pods. The reactive hybrid
uses the observed load $x_"obs"$, the mean over the last 30~s. The predictive hybrid also forms the upper
envelope of the GRU forecast,
$ hat(u)_(t+k) = hat(y)_(t+k) + delta_k, quad k = 1, dots, 9, $
where $hat(y)_(t+k)$ is the forecast for step $k$ and the margin $delta_k$, #G.offset_min to #G.offset_max RPS,
is the 90th percentile of the forecast's underestimates at that step on the validation data. Its decision
factor is the largest envelope value. This forecast target replaces the observed-load target only when it asks
for more pods, so a forecast that is too low never removes pods. Once raised, the target holds for 90~s, so that
a brief dip does not remove pods that the next forecast would ask for again (@alg:scaling). Pods are removed
only when the target falls below 0.75 times the current count, at least 120~s after the last removal, and while
the p99 is below 140~ms.

#alg-scaling <alg:scaling>

Algorithm 2 keeps two ideas from ElaX, scaling ahead of time from a forecast and sizing for the largest
predicted value. It changes the predictor, the horizon, the refresh period and the decision factor, and it works
alongside a router, which ElaX does not have (@tab:elax).

#tab-elax <tab:elax>

== Node tier
The node tier produces the delay that the forecast is meant to hide. When pods cannot be scheduled, a node
autoscaler waits a set provisioning delay of 45 to 120~s, close to the virtual machine start-up times measured
in public clouds @hao2021vmstartup, and then adds a one-CPU worker. In our runs, the first new node arrived
#H.b10b.delay_min to #H.b10b.delay_max~s after the first pod could not be scheduled, slightly longer than the set delay. A node is
removed when its CPU utilization falls below 50%, the default of the Kubernetes Cluster Autoscaler @k8sca-faq.
The forecast horizon of 135~s equals the longest set delay plus one 15~s cycle, so the predictive hybrid can ask
for a pod before the load that needs it arrives.

= GRU forecaster <sec:gru>
A fair test of the forecast needs a forecaster that is well tuned and has never seen the load it is tested on.
Ours meets both conditions, yet it is still no more accurate than a linear model.

*Model and training.* A two-layer GRU @cho2014learning @chung2014empirical with #G.hidden hidden units takes
the last 30 load samples, one every 15~s, and outputs all nine future steps at once. Its server answers in
#G.latency.median ms (median; p95 #G.latency.p95 ms), well within the 15~s cycle. We train it on the ClarkNet
web-server trace @clarknet, aggregated to 15~s and multiplied by 33, the same factor the experiments use when they
replay the trace. The trace is split in time
order into training, validation and test portions, with gaps of 38 samples between them so that no input window
or target crosses a boundary. We fit the input normalization on the training portion only, and a Bayesian
search @bergstra2011tpe @optuna2019 selects the hyperparameters on the validation portion only, because a score
on data that guided the selection is biased @cawley2010overfitting. The 20-minute window that the experiments
replay lies in the test portion, so the deployed model never saw it.

#if extended [
  The search used the Tree-structured Parzen Estimator in Optuna and ran #G.trials trials for each input length
  (#G.seq_searched samples) on the first seed. It selected a dropout of #G.dropout, a learning rate of #G.lr
  and a budget of #G.epochs epochs. The margins $delta_k$ come from the validation residuals of the selected
  model. They range from #G.offset_min to #G.offset_max RPS over the nine steps. On the test portion, the upper
  envelope covered #G.gru.coverage of the values that the point forecast predicted too low, against a target
  of 0.90.
]

*Accuracy.* @tab:predictor reports the test error at the ninth step, with each model trained on three seeds.
Persistence, the simplest forecast, repeats the last value, and we define a model's skill as the share of
persistence's error that it removes. The GRU removes #G.gru.skill of that error. It is also slightly more accurate
than an LSTM, the model family of ElaX, even though the LSTM was tuned the same way and given more data. A linear
autoregression, however, is as accurate as the GRU, and none of the #G.levers other variants we screened beat
the linear model.

#tab-predictor <tab:predictor>

#if extended [
  The variants were input transforms, a target transform, coarser sampling intervals, a decomposed input and
  two other architectures. The error grows with the horizon at the same rate for both models. The GRU RMSE rises
  from #G.gru_h1 at the first step to #G.gru_h9 at the ninth, and the linear model's RMSE rises from #G.ols_h1
  to #G.ols_h9. The input transforms were differencing, exponential and rolling statistics, robust and quantile
  scaling, and reversible instance normalization. The two other architectures were N-BEATS and a linear network.
  Outside the ClarkNet test portion, the GRU kept one advantage over the LSTM. On a synthetic spike archetype,
  its RMSE was #G.gru.spike against #G.lstm.spike. On a synthetic trace, the same protocol gives a normalized RMSE
  of #G.synthetic_nrmse%, against #G.gru.nrmse% on the real trace, so the protocol can fit a forecastable series.
  For scaling, RMSE alone is not the right measure. The scaler acts on the largest value of the envelope, so a
  forecaster that is accurate on average but late on a rising edge still adds pods late.
]

= Experimental setup <sec:setup>
#tab-scenarios <tab:scenarios>

The experiment answers two questions (@tab:batches). The first is what the hybrid delivers without a forecast,
which a scenario batch answers by running the reactive hybrid beside two single-platform baselines. The second
is what the forecast adds, which the paired batches answer, and it is the main question of this paper.

*Testbed.* We sized the testbed so that the replayed load outgrows the static capacity and new nodes must start.
Two clusters run on one host under k3d, a tool that runs Kubernetes nodes as containers. The Kubernetes cluster
has one static worker plus the dynamic nodes of @sec:design, each limited to one CPU. The Knative cluster has
one three-CPU worker and keeps three to ten pods, so it never scales to zero. Each pod requests 0.3 CPU, and
each request computes the 33rd Fibonacci number and then waits 50~ms to simulate I/O.

*Workload and measure.* The load generator k6 replays a 20-minute ClarkNet window in 40 steps of 30~s, with a
mean of 73~RPS, a peak of 164~RPS, and about #F.requests requests per run. We judge each run by its p99 rather
than its mean, because a surge delays only the requests that arrive while capacity is short, and these are too
few to move the mean. The SLO is a p99 of 200~ms, and every request slower than 200~ms counts as one SLO
violation.

*Scenarios and batches.* @tab:scenarios lists the four scenarios. In the scenario batch, the HPA baseline, the
Knative baseline and the reactive hybrid each ran five times. The paired batches compare the predictive hybrid
with the reactive one. A pair is one run of each, back to back, both starting from one static worker and facing
the same provisioning delay, so the forecast is the only planned difference between them. The set delay cycles
through 60, 90, 120, 75 and 45~s from pair to pair, and the order of the two runs alternates, so a slow drift of
the host favors neither hybrid. Pairing also cancels much of the run-to-run noise that load on the shared host
adds to the p99. Before each paired batch started, we fixed the measure it would report and the test it would use.
A pilot of five pairs could reach significance only if the forecast won all five, so the next two batches used ten
pairs. Two earlier sets of predictive runs are not used, because their records do not show which forecaster was
deployed. @tab:batches lists both.

#tab-four <tab:four>
#tab-batches <tab:batches>

*Tests and validity.* Our hypothesis is that the forecast lowers the p99. We test it with a one-sided exact
paired permutation test at the 0.05 level, and we report a bootstrap 95% interval and the paired Cohen's $d$,
the mean difference divided by its spread. A run counts only if it exercised the mechanism under test. A hybrid
run must have used the node tier, and a predictive run must also have received every forecast it asked for,
covered its provisioning delay with the forecast horizon, and raised its replica target from a forecast at least
once. Every run of the paired batches passed: #H.b5.valid of #H.b5.runs in the pilot, #H.b10a.valid of
#H.b10a.runs in the loaded-host batch and #H.b10b.valid of #H.b10b.runs in the confirmatory batch, which also
received #H.b10b.delivered of #H.b10b.eligible forecasts. Because all clusters share one host whose load can
move the p99, the last two batches also logged the host's CPU-busy fraction, the share of non-idle CPU time in
`/proc/stat`.

*Cost.* Because the forecast adds pods, it can also add cost, so we project each run's resource use onto AWS
prices. Kubernetes maps to EKS nodes sized from the mean CPU use, Knative maps to Lambda with provisioned
concurrency sized from the serverless request rate, and each 20-minute run is scaled up to a 30-day month. The
projection charges whole nodes, so it cannot show a difference smaller than one node running for a month.

#if extended [
  *Run conditioning.* Before each run of the paired batches, the experiment tool sets the static worker count and
  deletes leftover dynamic nodes and their pods. It checks that both backends serve, and that the prediction server
  answers when the scenario needs it. Each run records the hash of the deployed predictor in its manifest.

  *Cost model.* The nodes are t3.medium instances behind an EKS control plane. Their number is the mean CPU use
  divided by the allocatable CPU of one node at the target utilization, rounded up, plus one. Each dynamic node
  adds its measured lifetime. Lambda provisioned concurrency follows Little's law from the serverless request
  rate and the measured execution time.
]

= Results <sec:results>
== Routing the overflow kept the cost of Kubernetes, not its latency
Before testing the forecast, we look at what the hybrid delivers without it (@tab:four, @fig:runs). The Knative
baseline was the fastest, but at #F.s2.cost USD per month it cost more than twice as much as the HPA baseline.
The comparison also favors it, since it ran three always-warm pods on a three-CPU worker, while the HPA baseline
started from one pod on a one-CPU worker. The reactive hybrid had about the same projected cost as the HPA
baseline and ran #F.s3_pods_below_s1% fewer pod-seconds (pods times seconds running) on Kubernetes, but it also kept at
least three Knative pods warm, so it ran no fewer pods in total. It paid in latency instead, with a p99 of #F.s3.p99 ms
against #F.s1.p99 ms, more SLO violations, and one of its five runs above the SLO. Routing the overflow
therefore kept the cost of Kubernetes but not its tail latency, which leaves room for a forecast to help.

#fig-runs <fig:runs>

== The forecast did not measurably lower the p99
@tab:h2 and @fig:forest compare the predictive hybrid with the reactive one, pair by pair. In the confirmatory
batch, the forecast changed the p99 by
#H.b10b.diff ms ($p = #H.b10b.p$, $d = #H.b10b.d$), and the predictive hybrid was faster in #H.b10b.wins of
#H.b10b.n pairs, so the data do not support the hypothesis that the forecast lowers the p99. The two earlier
batches pointed in opposite directions, the pilot toward the reactive hybrid and the loaded-host batch toward
the predictive one, and neither difference was significant.

#tab-h2 <tab:h2>

Host load is the likely reason the loaded-host batch looked different. Its pair differences had a standard
deviation of #H.b10a.diff_sd ms, against #H.b10b.diff_sd ms in the confirmatory batch, and its peak CPU-busy
fraction correlated with the p99 (Pearson correlation #H.b10a.busy_p99_r). The confirmatory batch ran on a
quieter host, with mean CPU-busy fractions of #H.b10b.busy_avg_min to #H.b10b.busy_avg_max, and it still showed
no gain.

#if extended [
  In the #H.b10a.quiet.n pairs of the loaded-host batch where both runs peaked below 0.4, a post-hoc subset, the
  difference was #H.b10a.quiet.diff ms (uncorrected $p = #H.b10a.quiet.p$); the confirmatory batch did not
  reproduce it. There, the correlation fell to #H.b10b.busy_p99_r, and #H.b10b.busy_peak_over_half of 20 runs
  still had a host CPU-busy peak above 0.5. The mean SLO violations per run were #H.b10b.slo_s3 for the reactive
  and #H.b10b.slo_s4 for the predictive hybrid.
]

Ten pairs could still miss a small gain. With the confirmatory spread of #H.b10b.diff_sd ms, the test detects a
difference of about #H.b10b.mde ms or more with 80% power. The 95% interval reaches down to #H.b10b.ci_lo ms, so
a reduction beyond that bound is unlikely, although a smaller one is not ruled out. Pooled over #H.pooled.n pairs, the
difference is #H.pooled.diff ms and the interval includes zero, but the batches ran under different host load,
so we treat the pooled row as descriptive only.

#fig-forest <fig:forest>

== The forecast changed scaling, not latency <sec:effect>
If the forecast did not lower the p99, its effect went elsewhere, and we trace it in three steps. First, the
forecast did change what the scaler did. In the confirmatory batch, the predictive hybrid made
#H.b10b.proactive scale-ups in which the forecast asked for more pods than the observed load, and it used
#H.b10b.replica_pct% more pod-seconds than the reactive hybrid. These extra pods took over part of the overflow.
The mean serverless weight fell from #H.b10b.share_s3% to #H.b10b.share_s4%, and the share of time with any
traffic to Knative fell from #H.b10b.active_s3% to #H.b10b.active_s4%. The projected cost of the batch stayed
the same (USD #H.b10b.cost_s3 and #H.b10b.cost_s4 per month), because both hybrids used the same node tier.

Second, the extra pods did not make requests measurably faster (@tab:h2). A likely reason, which we did not
test, is that until the first new node of a run was ready (each run added about #H.b10b.nodes), the router sent the excess
to Knative in both hybrids. The reactive hybrid therefore already had serverless capacity during the
provisioning delay that the forecast was meant to cover, so the forecast's pods replaced that capacity rather
than adding capacity where there was none. We did not record which backend served the slowest requests, so these
may have come from Knative, from pods still starting, or from the shared host.

Third, as the introduction noted, our design cannot tell whether the GRU itself caused the extra pods. The
margin alone adds #G.offset_min to #G.offset_max RPS to a mean load of 73~RPS, which is three to four extra pods,
and the hold keeps them for 90~s. Since the GRU is no more accurate than a linear autoregression
(@tab:predictor), a simpler forecast with the same margin may well add the same pods. Our pairs compare a
forecast with no forecast, not the GRU with a simpler forecast.

= Discussion <sec:discussion>
Spock reported a gain where we found none, and the purpose of each forecast may explain why, although
we did not test it. Spock's forecast adds base capacity for the average rate, whereas ours adds pods for a peak
that Knative already serves. Spandana points the same way, since it meets its SLO with per-request offload and
no forecast @spandana2026. The same reading predicts that a forecast should help in three cases: without an
overflow backend, with one that cannot take the whole excess, or after a scale-down that removes capacity the
load soon needs again. Recording which backend serves the slowest requests would test this directly.

*Threats to validity.* All clusters share one host, so the testbed simulates two platforms rather than two
clouds, and a timer simulates the provisioning delay. The workload is one 20-minute window of one trace, served
by one function. Algorithm 2 ran with one parameter set, and a smaller margin or a shorter hold would change what
the forecast costs. Finally, the loaded-host batch ran with a mean CPU-busy fraction of up to
#H.b10a.busy_avg_max, and the pilot batch has no host record.

= Conclusion
We proposed a hybrid that keeps the base load on Kubernetes, sends the excess to Knative, and scales pods with
an ElaX-derived scaler extended with a GRU forecast. Without the forecast, the hybrid cost about as much as
Kubernetes alone but had a higher tail latency. In ten confirmatory pairs, the forecast added
#H.b10b.replica_pct% more pod-seconds without a measurable change in the p99, and the 95% interval of its effect
reaches down to #H.b10b.ci_lo ms. A deployment that already routes its overflow to serverless should therefore
measure what a forecast buys before adopting one. Our next experiments are a constant-margin baseline, which
keeps the margin but drops the GRU, and a run without a serverless backend, where the forecast has a delay to
remove.

#if extended [
  = Data availability
  The run bundles, the analysis code and the script that derives every number in this paper from the bundles are
  available from the corresponding author on request.
]
]
