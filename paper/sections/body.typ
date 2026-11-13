// Paper body shared by both builds. `extended: false` is the six-page conference paper;
// `extended: true` adds the journal-only material inside `#if extended [...]` blocks.
// Numbers come from common.typ (numbers.json); never type a measured value here.
// One name per thing: pod (one running copy of the service), replica count (the number of
// pods the scaler asks for), router (Algorithm 1), replica scaler (Algorithm 2), forecast
// (the GRU output), margin (delta_k), upper envelope (forecast plus margin), provisioning
// delay, reactive hybrid (S3), predictive hybrid (S4), scenario batch, batches A to C.
// Structure: every paragraph opens with the question it answers and ends with its answer;
// the Spock contrast lives in Related work, the Knative explanation in Results C.
#import "common.typ": *

#let abstract = [
  The Kubernetes Horizontal Pod Autoscaler (HPA) adds pods only after load rises. If no node has room for
  them, requests wait one to two minutes while a new virtual machine starts. A workload forecast can add pods
  before the load arrives, and a serverless platform can absorb the overflow within seconds at a higher
  price. Hybrids already use serverless this way, so we ask whether a forecast still helps once serverless
  covers the wait. We built a hybrid of Kubernetes and the serverless platform Knative in which the forecast
  is the only difference between two versions. Every 15~s, a router sends Knative only the load the ready
  pods cannot serve, and a replica scaler adapted from the autoscaler ElaX sets the pod count. The reactive
  version sizes from the observed load, and the predictive version adds a 135~s gated recurrent unit (GRU)
  forecast plus a safety margin. On a ClarkNet trace replay, both hybrids had the projected cost of
  Kubernetes with the HPA. Knative alone had the lowest 99th-percentile latency (p99) at more than twice that
  cost. In ten confirmatory run pairs, the forecast added #H.b10b.replica_pct% more pod-seconds, but the
  p99 did not change measurably (#H.b10b.diff ms, 95% CI \[#H.b10b.ci_lo, #H.b10b.ci_hi\],
  $p = #H.b10b.p$). The test detects differences of about #H.b10b.mde ms or more. The GRU was no more
  accurate than a linear autoregression. A likely, untested explanation is that serverless already serves
  the load while new pods start, which leaves the forecast little delay to remove.
]

#let keywords = ([Kubernetes], [serverless computing], [autoscaling], [workload prediction],
  [gated recurrent unit], [traffic routing])

#let body(extended: false) = [
= Introduction
Many web services promise to answer each request within a fixed time, a service-level objective (SLO), while
their load changes from minute to minute. On Kubernetes, this promise is hardest to keep during a surge,
because capacity follows the load instead of leading it. The Horizontal Pod Autoscaler (HPA) adds pods, the
running copies of a service, only after CPU use has crossed a target @serracanta2025hpa. When no node has
room for a new pod, the cluster must first start a virtual machine, which takes one to two minutes
@hao2021vmstartup. On our testbed, where a timer stands in for this start, the first new node was ready
#H.b10b.delay_min to #H.b10b.delay_max~s after the request. Requests that arrive during this provisioning
delay wait in a queue, and they are the
requests that break the SLO.

Two remedies shorten this wait. The first predicts the load and adds capacity before it is needed. ElaX, an
autoscaler for container clusters, does this with an hourly long short-term memory (LSTM) forecast
@yang2019elax. The second sends the excess load to a serverless platform, which adds instances within
seconds @demystifying2025, although each new instance pays a start-up (cold-start) delay @golec2023cold.
Serverless suits bursts but not steady load. Public platforms charge a higher unit price plus a fee per
invocation @demystifying2025, so steady load costs several times more there than on virtual machines
@dehigama2024. Hybrid deployments therefore keep the steady base load on reserved machines and send only
the excess to serverless @dehigama2024.

In such a hybrid, the two remedies overlap. While new pods and nodes start, serverless already serves the
excess, so a forecast can remove only the part of the wait that serverless leaves. The forecast still costs
extra pods and a model to train and serve, and prior work does not say whether it pays for itself. MArk
@zhang2019mark and Spock @gunasekaran2019spock combine both remedies on virtual machines. Spock reports
fewer SLO violations with its forecast, but only in a simulator (@sec:related). We therefore ask a narrow
question. Once serverless absorbs the overflow, does a forecast still lower the tail latency of a running
deployment?

To answer it, we built a hybrid of Kubernetes and Knative, a serverless platform that runs on Kubernetes.
Every 15~s, a capacity-aware router (Algorithm 1) sends Knative the load that the ready pods cannot serve,
and a replica scaler derived from ElaX (Algorithm 2) sets the number of pods. The router never reads the
forecast. Only the predictive version of the scaler does, so back-to-back pairs of runs of the two versions
measure what the forecast changes. Our contributions are as follows.
+ A control loop that runs the router and the replica scaler together, built so that a forecast can act
  only through the pods it adds.
+ An extension of the ElaX scaling decision with a gated recurrent unit (GRU) forecast, trained without
  test data, that sizes the pods for the largest forecast value plus a margin.
+ A paired evaluation on a running testbed against Kubernetes under the HPA (S1) and Knative alone (S2).
  Between the reactive (S3) and predictive (S4) hybrids, the forecast added #H.b10b.replica_pct% more
  pod-seconds (pods times seconds running) but did not measurably change the tail latency.

= Related work <sec:related>
*Hybrid execution.* Two systems combine a forecast with a serverless overflow, the combination we test.
MArk provisions virtual machines from a forecast of the maximum request rate, and it sends the requests
that they cannot serve in time to AWS Lambda @zhang2019mark. Spock sends a request to a Lambda function when
no virtual machine has a free slot. It predicts the average request rate at the time a new machine would be
ready, with a linear regression, and it starts machines for that average @gunasekaran2019spock. In an
event-driven simulator, Spock's predictive policy caused fewer SLO violations. Our setting differs from
Spock in four ways. First, the base tier is Kubernetes, so capacity grows in two steps, pods when a node has
room and nodes only after a provisioning delay. Second, our router sets HAProxy load-balancer weights every
15~s from the ready capacity instead of placing single requests. Third, our scaler sizes for the upper end of
the forecast, so the forecast adds pods for the peak and not for the average. Fourth, we measure a running
deployment with paired runs that differ only in the forecast. Other hybrids route between two serverless
paths @pulsenet2025 or between edge and cloud tiers @laimr2026, and neither pairs a load forecast with a
serverless overflow.

*Autoscaling with forecasts.* Many autoscalers forecast the load, but each scales one platform. HyPA
combines reactive and model-based horizontal scaling, and it refits its model when the forecast error rises
@hypa2023. KAPETÁNIOS adapts HPA parameters through a digital twin of the cluster @kapetanios2022. Other
forecast-based Kubernetes scalers model CPU use @mondal2023toward or the request rate @yuan2024time. AAPA
adds archetype awareness and uncertainty estimates for serverless workloads @aapa2025. ADAPT estimates the
cold-start duration online and sets its planning horizon from it @adapt2026. A calibrated rule-based
autoscaler beat six deep reinforcement learning algorithms on cost @rayscale2026. None of these systems
measures what a forecast adds once an overflow to serverless exists.

*Serverless cost and cold starts.* Overflow is not free, which is why hybrids keep it small. New function
instances pay a start-up delay that a survey names as an autoscaling challenge @mampage2022holistic and that
benchmarks measure @yu2020characterizing @sebs2020. Billing rounds up time and memory @sebs2020, and keeping
instances warm costs CPU and memory @highcost2025. Our router therefore sends Knative only the load that
Kubernetes cannot serve, and it caps that share.

#if extended [
  *Scheduling and scaling control.* A survey of Kubernetes scheduling includes a category of
  autoscaling-enabled scheduling @senjab2023survey. Containers also pay a start-up cost when a deployment
  scales out @beni2021reducing. Forecasts have been used to start serverless functions before requests
  arrive @jegannathan2022time, and reinforcement learning has been used to decide how long to keep them
  warm @vahidinia2023mitigating. AutoScale waits before it turns off an idle server, so that it does not
  lose capacity that the load needs again @gandhi2012autoscale. STaleX adapts the scaling of each service
  to service dependencies and to workload changes over time @stalex2025.
]

= Control architecture <sec:design>
#fig-architecture <fig:arch>

The architecture must serve the load and also let an experiment isolate the forecast. @fig:arch shows how it
does both. HAProxy, a load balancer, splits all requests between a Kubernetes deployment and a Knative
service according to two weights. A control daemon runs a loop every 15~s. In each cycle, it reads the load
$x$ in requests per second (RPS) and the p99 from Prometheus, a metrics store, and the number of ready pods
$n$, the pods that pass their readiness probe, from the Kubernetes API. The daemon then runs the router,
which sets the weights, and the replica scaler, which sets the pod count. Only the scaler can read the
forecast.

== Algorithm 1: capacity-aware router
The router decides how much load the ready pods can take and sends the rest to Knative. One ready pod serves
$r_"eff" = r_"sat" dot rho = 33.3 times 0.5 = 16.65$ RPS. Here, $r_"sat"$ is the saturation throughput of
one pod, measured with three pods, and $rho$ is the target utilization. The ready pods can serve
$C = n dot r_"eff"$, and Knative receives the rest through the serverless weight, in percent:
$ w_"sls" = cases(0 & "if" x <= C, min(50, ceil(100 (x - C) \/ x)) & "otherwise.") $
The router applies the new weight at once, without smoothing (@alg:routing). The cap of 50% limits the
serverless cost when Kubernetes capacity is far below the load. Because the router reads only the ready pods,
a forecast can change the weight only through the pods that Algorithm 2 adds.

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
The replica scaler decides how many pods to run, and it is the only place where the forecast enters. Its
design follows from one asymmetry. A pod that starts too late causes SLO violations, whereas a pod that
starts too early only stays idle, so the scaler leans toward too many pods. It computes the replica count
from a load value $v$, which we call the decision factor, with the linear model
$R(v) = "clamp"(ceil(alpha v + beta), R_min, R_max)$, where $alpha = 1 \/ r_"eff"$, $beta = 0$, $R_min = 3$
and $R_max = 10$. The reactive hybrid (S3) uses $v = x_"obs"$, the mean load over the last 30~s. The
predictive hybrid (S4) sizes for the upper envelope of the GRU forecast instead of the point forecast,
$ hat(u)_(t+k) = hat(y)_(t+k) + delta_k, quad k = 1, dots, 9, $
where $hat(y)_(t+k)$ is the point forecast for step $k$. The margin $delta_k$, #G.offset_min to #G.offset_max
RPS, is the 90th percentile of the positive validation residuals at step $k$. The decision
factor of S4 is the largest envelope value, $v = max_k hat(u)_(t+k)$. Algorithm 2 uses this forecast target
only when it is larger than $R(x_"obs")$, so the observed load still sets the replica count when the GRU
predicts too low. It then keeps the target for 90~s, a period we call the hold, so that a short dip does not
remove pods that the next forecast would ask for again 15~s later (@alg:scaling). A scale-down needs three
conditions at once. The target is below 0.75 times the current replica count, 120~s have passed since the
last scale-down, and the p99 is below 140~ms.

#alg-scaling <alg:scaling>

Compared with ElaX, Algorithm 2 keeps scaling ahead of time from a forecast and sizing for the largest
predicted value. It changes the predictor, the horizon, the refresh period and the decision factor, and it
runs next to a router, which ElaX lacks (@tab:elax).

#tab-elax <tab:elax>

== Node tier
The node tier creates the delay that the forecast is meant to hide. When pods cannot be scheduled, a node
autoscaler waits for a provisioning delay of 45 to 120~s and then adds a worker with one CPU. This timer
stands in for the start of a virtual machine, and its range is close to the start-up times measured in public
clouds @hao2021vmstartup. The autoscaler removes a dynamic node when that node's CPU utilization falls below 50%, the
default scale-down threshold of the Kubernetes Cluster Autoscaler for pod requests @k8sca-faq. The 135~s
forecast horizon covers the longest delay, 120~s, plus one 15~s cycle, so S4 can ask for a node before the
load that needs it arrives.

= GRU forecaster <sec:gru>
The comparison of S3 and S4 is fair to the forecast only if the forecaster is well tuned and has never seen
the load it is tested on. We built the GRU to meet both conditions.

*Model.* A two-layer GRU @cho2014learning @chung2014empirical with #G.hidden hidden units reads the last 30
load samples, one per 15~s, and one dense output layer emits all nine future steps. The forecast server
answers in #G.latency.median ms (median; p95 #G.latency.p95 ms), so the forecast does not delay the 15~s loop.

*Leak-free protocol.* We aggregate the ClarkNet HTTP trace @clarknet, a public web-server log, into 15~s
buckets and multiply it by 33, the factor that scales the trace to our testbed in the replay. We split the
series in time order into training, validation and test portions. A gap of 38 samples, the input length plus
the horizon minus one, separates two portions, so no input window or target crosses a boundary. We fit the
input normalization on the training portion only. We select the hyperparameters and the number of epochs on
the validation portion
with the Tree-structured Parzen Estimator @bergstra2011tpe, a Bayesian search method implemented in Optuna
@optuna2019. The test portion takes no part in this selection, because a score on data that guided the
selection is biased @cawley2010overfitting. We train the selected configuration with three seeds and
evaluate each model once on the test portion. The 20-minute window that the experiments replay lies inside
the test portion, so the deployed model never saw it.

#if extended [
  The search ran #G.trials trials for each input length (#G.seq_searched samples) on the first seed. It
  selected a dropout of #G.dropout, a learning rate of #G.lr and a budget of #G.epochs epochs. The margins
  $delta_k$ come from the validation residuals of the selected model. They range from #G.offset_min to
  #G.offset_max RPS over the nine steps. On the test portion, the upper envelope covered #G.gru.coverage of
  the values that the point forecast predicted too low, against a target of 0.90.
]

*Accuracy.* @tab:predictor reports the error on the test portion at the 9-step horizon, in RPS of the
replayed series, over three seeds. Skill is the share of the error of a persistence forecast, which repeats
the last value, that a model removes. The GRU has a skill of #G.gru.skill. It is slightly more accurate than
an LSTM, the model family of ElaX, tuned in the same way, although the LSTM had more training data. It does
not beat a linear autoregression on the same inputs, and none of the #G.levers other variants that we
screened beat the linear model either. The forecaster is thus as good as we could make it on this trace,
but no better than a linear model, a fact that @sec:effect returns to.

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

The evaluation answers two questions in turn. A scenario batch first places the hybrids beside
single-platform baselines, and paired batches then test the forecast itself.

*Testbed.* The testbed is sized so that the replayed load outgrows the static capacity and new nodes must
start. Two clusters run on one host under k3d, a tool that runs Kubernetes nodes as containers. The
Kubernetes cluster has one static worker plus the dynamic nodes of @sec:design, and Docker limits each worker
to one CPU. The Knative cluster has one worker with three CPUs and keeps three to ten pods, so it never scales
to zero. Each pod requests 0.3 CPU. Each request computes the 33rd Fibonacci number (CPU work) and then waits
50~ms (simulated I/O).

*Workload and measures.* The load generator k6 replays a 20-minute ClarkNet window in 40 steps of 30~s, with
a mean of 73~RPS and a peak of 164~RPS. One run serves about #F.requests requests. We judge each run by its
99th-percentile latency (p99), the time within which 99% of the requests finish, and not by the mean. A surge
delays only the requests that arrive while capacity is short, and they are too few to move the mean. Our SLO
is a p99 of 200~ms, and each request slower than 200~ms counts as one SLO violation.

*Scenarios and batches.* @tab:scenarios lists the four scenarios. In the scenario batch, each scenario ran
five times. The paired batches then compare S4 with S3. A pair is one S3 run and one S4 run, back to back,
that start from one static worker and face the same provisioning delay, so the forecast is the only planned
difference between them. The timer cycles the delay through 60, 90, 120, 75 and 45~s from pair to pair. The
order of the two runs alternates (counterbalancing), so that a drift of the host favors neither arm.
Pairing cancels much of the run-to-run movement of the p99 that comes from load on the shared host, and the
number of pairs sets how small a difference the test can see. Three paired batches used the GRU of @sec:gru,
and each had its main measure and test level fixed before its first run. Batch A had five pairs, which reach
the 0.05 level only if S4 wins all five, so batches B and C used ten pairs each. B ran on a loaded host, so C,
the confirmatory batch, repeated it on a quieter one. We exclude an earlier five-pair batch that favored S4,
because its run records do not identify the predictor, which was trained on a synthetic trace.

*Tests and validity.* Our hypothesis is that S4 has a lower p99 than S3. We test it with a one-sided exact
paired permutation test at a level of 0.05. We also report a bootstrap 95% interval and the paired Cohen's
$d$, the mean difference divided by its spread. A run counts only if it exercised what the hypothesis
is about. A hybrid run must use the node tier, which means that a pod became unschedulable (no node had room
for it) or a dynamic node was provisioned. An S4 run must also receive every forecast it requests, use a
horizon that covers the provisioning delay, and raise the replica target from a forecast at least once.
Every run of the three paired batches passed (#H.b5.valid of #H.b5.runs runs, #H.b10a.valid of #H.b10a.runs
and #H.b10b.valid of #H.b10b.runs). Batch C received #H.b10b.delivered of #H.b10b.eligible forecasts. Batches
B and C also recorded the CPU-busy fraction of the host, the share of non-idle CPU time in `/proc/stat`, to
check whether host load moves the p99.

*Cost.* We project the cost onto AWS prices. Kubernetes maps to an EKS control plane plus t3.medium nodes,
sized from the mean Kubernetes CPU use. Knative maps to Lambda with provisioned concurrency, sized from the
serverless request rate. We scale each 20-minute run to a 30-day month. The projection charges for whole
nodes, not for pod-seconds, so it cannot show differences smaller than one node running for a month.

#if extended [
  *Run conditioning.* Before each run of the paired batches, the experiment tool sets the static worker count and
  deletes leftover dynamic nodes and their pods. It checks that both backends serve, and that the prediction server
  answers when the scenario needs it. Each run records the hash of the deployed predictor in its manifest.

  *Cost model.* The number of Kubernetes nodes is the mean CPU use divided by the allocatable CPU of one node at the
  target utilization, rounded up, plus one. Each dynamic node adds its measured lifetime. Lambda provisioned
  concurrency follows Little's law from the serverless request rate and the measured execution time.
]

= Results <sec:results>
== The hybrids cost as much as Kubernetes alone
@tab:four and @fig:runs place the hybrids beside the single-platform baselines. Knative alone (S2) gave the
lowest p99, but at #F.s2.cost USD per month it cost more than twice any scenario with Kubernetes. The
comparison also favors S2, which ran three always-warm pods on a three-CPU worker, while S1 started from one
pod on a one-CPU worker. The two hybrids had the projected cost of S1 within the resolution of the
projection, and they used #F.s3_pods_below_s1% (S3) and #F.s4_pods_below_s1% (S4) fewer Kubernetes
pod-seconds. This count excludes the Knative pods, and each hybrid kept at least three of them warm, so the
hybrids did not save pods in total. The reactive hybrid paid in latency, with a p99 of #F.s3.p99 ms against
#F.s1.p99 ms for S1, more SLO violations, and one of its five runs above the SLO. Routing the overflow kept
the cost of Kubernetes, but it did not by itself keep the tail latency of Kubernetes.

#tab-four <tab:four>
#fig-runs <fig:runs>

The S4 row of @tab:four ran an earlier GRU, before the forecaster of @sec:gru existed, and its run manifests do
not record the predictor. Its logged margin was about 10~RPS, against #G.offset_min to #G.offset_max RPS for
the GRU of @sec:gru. Its p99 of #F.s4.p99 ms, #F.s4_vs_s1.abs_pct% below S1 (two-sided Mann-Whitney rank test
$p = #F.s4_vs_s1.p$), therefore shows what the architecture can do, not what our forecaster does.

== The forecast did not measurably lower the p99
@tab:h2 and @fig:forest give the paired results. The three batches did not agree in direction. Batch A favored
S3, and batch B favored S4 but not significantly. The confirmatory batch C gave a difference of
#H.b10b.diff ms ($p = #H.b10b.p$, $d = #H.b10b.d$), and S4 was faster in #H.b10b.wins of #H.b10b.n pairs.
The data therefore do not support the hypothesis that the forecast lowers the p99.

#tab-h2 <tab:h2>
#fig-forest <fig:forest>

How large a gain could ten pairs have missed? The pair differences of batch C have a standard deviation of
#H.b10b.diff_sd ms, so the test detects a difference of about #H.b10b.mde ms or more with 80% power. The lower
end of the interval, #H.b10b.ci_lo ms, is the largest p99 reduction that the data still allow. Pooled over
#H.pooled.n pairs, the difference is #H.pooled.diff ms and the interval includes zero, but the batches ran
under different host load, so the pooled row is only descriptive.

Could load on the shared host have hidden a gain? In batch B, the peak CPU-busy fraction of the host
correlated with the p99 (Pearson correlation #H.b10a.busy_p99_r). In the #H.b10a.quiet.n pairs of batch B
where both runs peaked below 0.4, a post-hoc subset, the difference was #H.b10a.quiet.diff ms (uncorrected
$p = #H.b10a.quiet.p$). Batch C then ran on a quieter host, with a mean CPU-busy fraction between
#H.b10b.busy_avg_min and #H.b10b.busy_avg_max, and it did not reproduce that difference. A quieter host did
not reveal a gain.

#if extended [
  In batch C, the correlation fell to #H.b10b.busy_p99_r, and #H.b10b.busy_peak_over_half of 20 runs still had a host
  CPU-busy peak above 0.5. The mean SLO violations per run were #H.b10b.slo_s3 for S3 and #H.b10b.slo_s4 for S4.
]

== The forecast changed scaling, not latency <sec:effect>
If the forecast did not lower the p99, where did its effect go? Three questions trace it. First, did the
forecast change what the scaler did? It did. In batch C, S4 made #H.b10b.proactive scale-ups in which the
forecast target was above the observed-load target, and it used #H.b10b.replica_pct% more pod-seconds than
S3. The extra pods lowered the mean serverless weight from #H.b10b.share_s3% to #H.b10b.share_s4% and the
share of time with traffic to Knative from #H.b10b.active_s3% to #H.b10b.active_s4%. The projected cost of this
batch stayed the same (USD #H.b10b.cost_s3 for S3 and #H.b10b.cost_s4 for S4 per month), because both arms
used the same node tier.

Second, did the extra pods make requests faster? Not measurably (@tab:h2). The likely but untested reason is
that the router sent the excess load to Knative in both arms until the first of about #H.b10b.nodes dynamic
nodes per run was ready. The reactive arm thus already had serverless capacity during the delay that the
forecast was meant to cover. We did not record which backend served the slowest requests, so they may have
come from Knative, from pods still starting, or from the shared host.

Third, did the GRU itself cause the extra pods? Our design cannot tell. The margin alone adds #G.offset_min
to #G.offset_max RPS to a mean load of 73~RPS, which is three to four extra pods, and the hold keeps them for
90~s. Since the GRU is no more accurate than a linear autoregression (@tab:predictor), a simpler forecast with
the same margin may add the same pods. Our pairs compare a forecast with no forecast, not the GRU with a
simpler forecast.

= Discussion <sec:discussion>
In our hybrid, then, a forecast buys pods but no measurable latency. The reason proposed in @sec:effect, that
Knative already covers the provisioning delay, would also explain why Spock found a gain where we did not,
although we did not test it. Spock's forecast sizes machines for the average rate and leaves the peaks to
Lambda @gunasekaran2019spock, whereas our scaler adds pods for the peak, which Knative already serves. A
forecast is therefore more likely to help where nothing covers the delay: without an overflow backend, with
one that cannot take the whole excess, or after a scale-down that removes capacity the load soon needs again.

*Threats to validity.* All clusters share one host, so the testbed simulates two platforms, not two clouds. A
timer simulates the provisioning delay. The workload is one 20-minute window of one trace, served by one
function. Algorithm 2 ran with one parameter set, and a smaller margin or a shorter hold would change what the
forecast costs. Batch B ran on a loaded host, with a mean CPU-busy fraction up to #H.b10a.busy_avg_max, and
batch A has no host record.

= Conclusion
We asked whether a workload forecast still lowers the tail latency of Kubernetes once serverless absorbs the
overflow. Both of our hybrids had the projected cost of Kubernetes with the HPA, and the reactive one had a
higher p99. In ten pre-specified pairs, the GRU forecast added pods but gave no measurable latency gain, and
the data allow a p99 reduction of at most #H.b10b.ci_lo ms. The next experiment is a constant-margin
baseline, which keeps the margin and drops the GRU. If it matches S4, the GRU adds nothing beyond its margin.
We also plan to set the margin from the measured provisioning delay and to test the scaler without a
serverless backend.

#if extended [
  = Data availability
  The run bundles, the analysis code and the script that derives every number in this paper from the bundles are
  available from the corresponding author on request.
]
]
