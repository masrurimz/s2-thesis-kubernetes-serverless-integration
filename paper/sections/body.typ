// Paper body shared by both builds. `extended: false` is the six-page conference paper;
// `extended: true` adds the journal-only material inside `#if extended [...]` blocks.
// Numbers come from common.typ (numbers.json); never type a measured value here.
// One name per thing: pod (one running copy of the service), replica count (the number of
// pods the scaler asks for), router (Algorithm 1), replica scaler (Algorithm 2), forecast
// (the GRU output), margin (delta_k), upper envelope (forecast plus margin), provisioning
// delay, reactive hybrid (S3), predictive hybrid (S4), scenario batch, batches A to C.
#import "common.typ": *

#let abstract = [
  The Kubernetes Horizontal Pod Autoscaler (HPA) adds pods only after load rises, and if nodes are full, a
  new virtual machine takes one to two minutes to start while requests wait. A forecast can add pods early.
  A serverless platform can absorb the extra load within seconds at a higher price, so hybrids keep the
  base load on Kubernetes and send only the overflow to serverless. We test whether a forecast still helps
  once serverless covers this delay, in a hybrid of Kubernetes and the serverless platform Knative. Every
  15~s, a router sends Knative only the load the ready pods cannot serve, and a scaler adapted from the
  forecast-based autoscaler ElaX sets the pod count. The reactive hybrid uses only the observed load, and
  the predictive one adds a 135~s gated recurrent unit (GRU) forecast plus a safety margin. On a ClarkNet
  trace replay, both hybrids had the projected cost of Kubernetes with the HPA, while Knative alone had the
  lowest 99th-percentile latency (p99) at over twice that cost. In ten confirmatory pairs of runs that
  differed only in the forecast, the forecast added #H.b10b.replica_pct% more pod-seconds, but the p99 did
  not change measurably (#H.b10b.diff ms, 95% CI \[#H.b10b.ci_lo, #H.b10b.ci_hi\], $p = #H.b10b.p$). The
  test detects differences of about #H.b10b.mde ms or more. The GRU was no more accurate than a linear
  autoregression. A likely, untested explanation is that the serverless platform already serves the load
  while new pods start, leaving the forecast little delay to remove.
]

#let keywords = ([Kubernetes], [serverless computing], [autoscaling], [workload prediction],
  [gated recurrent unit], [traffic routing])

#let body(extended: false) = [
= Introduction
Many web services promise to answer each request within a fixed time, a service-level objective (SLO),
even though their load changes from minute to minute. On Kubernetes this promise is hardest to keep during
a surge, because capacity follows the load instead of leading it. The Horizontal Pod Autoscaler (HPA) adds
pods, the running copies of a service, only after the CPU use has crossed a target @serracanta2025hpa. If
no node has room for the new pods, the cluster must first start a virtual machine, which takes one to two
minutes @hao2021vmstartup. On our testbed, the first new node was ready #H.b10b.delay_min to
#H.b10b.delay_max s after the scale-up request. Requests that arrive in this gap wait in a queue. Spare
machines would avoid the wait, but idle machines cost money.

Two remedies attack this delay from different sides. The first predicts the load and adds capacity before
the load arrives, as ElaX does for a container cluster with an hourly long short-term memory (LSTM)
forecast @yang2019elax. The second sends the excess load to a serverless platform, which adds instances
within seconds @demystifying2025, although each new instance still pays a start-up (cold-start) delay
@golec2023cold. Serverless is expensive for steady load, because public platforms charge a higher unit
price plus a fee per invocation @demystifying2025, and steady load costs several times more there than on
virtual machines @dehigama2024. Hybrid deployments therefore keep the stable base load on reserved
machines and send only the excess to serverless functions @dehigama2024.

Once a deployment is hybrid, the two remedies overlap. While new pods and nodes start, the serverless
platform already serves the excess load, so a forecast can only remove the part of the delay that
serverless leaves. In return, it adds pods that cost money and a forecaster that must be trained and
served, so an operator needs to know whether it still pays for itself. Prior work does not say. MArk
@zhang2019mark and Spock @gunasekaran2019spock combine both
remedies on virtual machines. Spock reports fewer SLO violations with its forecast, but only in a
simulator, with machines sized for the average request rate (@sec:related). We ask the same question on a
running deployment.

Our hybrid runs on Kubernetes and Knative, a serverless platform that runs on Kubernetes. Every 15~s, a
capacity-aware router (Algorithm 1) sends Knative the load that the ready pods cannot serve, and a replica
scaler derived from ElaX (Algorithm 2) sets the number of pods. Only the predictive version of the scaler
reads a forecast, so comparing the two versions shows what the forecast changes. The contributions are as
follows.
+ A control loop that runs the router and the replica scaler together, with a router that uses only the
  observed load and the ready pods.
+ An extension of the ElaX scaling decision with a gated recurrent unit (GRU) forecast. The GRU predicts
  nine steps of 15~s and refreshes every cycle, and the scaler sizes for the largest forecast value plus a
  margin. Training and tuning use no test data and no window that crosses a split boundary.
+ An evaluation on a running testbed against Kubernetes under the HPA (S1) and Knative alone (S2),
  followed by matched pairs of the reactive (S3) and predictive (S4) hybrids in which every run must pass
  validity checks.

A surge delays only the requests that arrive while capacity is short. These requests are a small share of
the total, so the mean latency hides them, and we judge each run instead by its 99th-percentile latency
(p99), the time within which 99% of the requests finish. Our SLO is a p99 of 200~ms. In ten confirmatory
pairs, each running S3 and S4 back to back from the same starting state, the forecast added
#H.b10b.replica_pct% more pod-seconds (pods times seconds running) but did not measurably change the
p99.

= Related work <sec:related>
*Hybrid execution.* The closest systems pair virtual machines with serverless functions. MArk provisions
virtual machines from a forecast of the maximum request rate and sends the requests that they cannot
serve in time to AWS Lambda @zhang2019mark. Spock sends a request to a Lambda function when no virtual
machine has a free slot @gunasekaran2019spock. A linear regression predicts the average request rate at
the time a new machine would be ready, and Spock starts machines for that average. In an event-driven
simulator, Spock reports fewer SLO violations for its predictive policy. Our work differs from Spock in
four ways. First, the base tier is Kubernetes, so capacity grows in two steps. Pods start when a node
has room, and new nodes arrive only after a provisioning delay. Second, our router does not place single
requests. It sets the HAProxy weights every 15~s from the ready capacity. Third, our scaler sizes for the
upper end of the forecast, so the forecast adds pods for the peak, not for the average. Fourth, we
measure on a running deployment with paired runs that differ only in the forecast, and we test the
difference statistically.
PulseNet sends a request to fast, disposable instances when no regular Knative instance is free, so both
of its paths are serverless @pulsenet2025. LA-IMR routes inference requests between edge and cloud tiers
and scales Kubernetes replicas from a predicted latency @laimr2026.

*Autoscaling with forecasts.* HyPA combines reactive and model-based horizontal scaling and refits its
model when the forecast error rises @hypa2023. KAPETÁNIOS adapts HPA parameters through a digital twin
of the cluster @kapetanios2022. Forecast-based scalers for Kubernetes use time-series models of CPU use
@mondal2023toward or of the request rate @yuan2024time. AAPA adds archetype awareness and uncertainty
estimates for serverless workloads @aapa2025. ADAPT sets its planning horizon from an online estimate of
the cold-start duration @adapt2026. A calibrated rule-based autoscaler beat six deep reinforcement
learning algorithms on cost @rayscale2026. Each of these systems scales one platform only, and none
sends overflow to serverless.

*Serverless cost and cold starts.* A survey of serverless resource management names the start-up delay
of new function instances as a challenge for autoscaling @mampage2022holistic. Benchmarks measure this
cold-start latency @yu2020characterizing @sebs2020. SeBS also shows that billing rounds up time and
memory, so users pay for resources that they do not use @sebs2020. Billing practices @demystifying2025
and the CPU and memory needed to keep instances warm @highcost2025 add to that bill.

#if extended [
  *Scheduling and scaling control.* A survey of Kubernetes scheduling includes a category of
  autoscaling-enabled scheduling @senjab2023survey. Containers also pay a start-up cost when a
  deployment scales out @beni2021reducing. Forecasts have been used to start serverless functions before
  requests arrive @jegannathan2022time, and reinforcement learning has been used to decide how long to
  keep them warm @vahidinia2023mitigating. AutoScale waits before it turns off an idle server, so that it
  does not lose capacity that the load needs again @gandhi2012autoscale. STaleX adapts the scaling of
  each service to service dependencies and to workload changes over time @stalex2025.
]

*ElaX.* @tab:elax compares Algorithm 2 with ElaX. Algorithm 2 keeps two parts of ElaX. It adds capacity
ahead of time from a forecast, and it sizes for the largest predicted value. It changes the predictor,
the horizon, the refresh period and the decision factor. It also runs next to a router, which ElaX does
not have.

#tab-elax <tab:elax>

= Control architecture <sec:design>
#fig-architecture <fig:arch>

@fig:arch shows the system. HAProxy receives all requests and splits them between a Kubernetes
deployment and a Knative service according to two weights. A control daemon runs a loop every 15~s. In
each cycle, it reads the load $x$ in requests per second (RPS) and the p99 from Prometheus. It reads the
number of ready pods $n$ from the Kubernetes API. Then it runs the two algorithms. A pod is ready when it
passes its readiness probe and can receive traffic.

== Algorithm 1: capacity-aware router
One ready pod serves $r_"eff" = r_"sat" dot rho = 33.3 times 0.5 = 16.65$ RPS. Here, $r_"sat"$ is the
saturation throughput of one pod, measured with three pods, and $rho$ is the target utilization. The
ready capacity is $C = n dot r_"eff"$. Kubernetes serves the load up to $C$. Knative receives the rest
through the serverless weight, in percent:
$ w_"sls" = cases(0 & "if" x <= C, min(50, ceil(100 (x - C) \/ x)) & "otherwise.") $
The router applies the new weight at once, without smoothing (@alg:routing). The cap of 50% limits the
serverless cost when the Kubernetes capacity is far below the load. A forecast can change the weight only
through the pods that Algorithm 2 adds. The code also has a pacing term in the style of BACC @bacc2026.
This term cannot reach its threshold within one run, so @alg:routing omits it.

#alg-routing <alg:routing>

#if extended [
  The pacing term adds serverless weight when SLO violations accumulate, but it counts at most one
  violation per cycle. With eight ready pods, $C = 133.2$ RPS, and the cap applies only above 266~RPS.
  The replayed trace peaks at 164~RPS, so the cap never applied in the reported runs. The router starts
  each hybrid run at a serverless weight of 20%, and the first decision corrects it. When Algorithm 1
  enables serverless, it also sends one warm-up request to Knative. With three pods always running, this
  request has no effect. In the paired batches, its endpoint returned HTTP 404.
]

== Algorithm 2: ElaX-derived replica scaler with a forecast
Algorithm 2 computes the replica count from a load value $v$, which we call the decision factor. It uses
the linear model $R(v) = "clamp"(ceil(alpha v + beta), R_min, R_max)$, where $alpha = 1 \/ r_"eff"$,
$beta = 0$, $R_min = 3$ and $R_max = 10$. The reactive hybrid (S3) uses $v = x_"obs"$, the mean load
over the last 30~s. The predictive hybrid (S4) also computes a forecast target from the upper envelope
of the GRU forecast,
$ hat(u)_(t+k) = hat(y)_(t+k) + delta_k, quad k = 1, dots, 9. $
Here, $hat(y)_(t+k)$ is the point forecast for step $k$. The margin $delta_k$ is the 90th percentile of
the positive validation residuals at step $k$. The decision factor of S4 is the largest envelope value,
$v = max_k hat(u)_(t+k)$. Algorithm 2 applies the forecast target when it is larger than $R(x_"obs")$,
and then holds it for 90~s (@alg:scaling). A scale-down needs three conditions. The target is below 0.75
times the current replica count, 120~s have passed since the last scale-down, and the p99 is below 140~ms.

#alg-scaling <alg:scaling>

We size for the upper envelope, and not for the point forecast, because a forecast that is too low
costs more than one that is too high. A pod that arrives late causes SLO violations. A pod that arrives
early only stays idle. The
forecast can only raise the target. If the GRU predicts too low, the observed load still sets the replica
count. The scaler holds a raised target for 90~s. Without the hold, a short dip in the load would remove
pods, and the next forecast would ask for them again 15~s later.

== Node tier
Pods that cannot be scheduled trigger a node autoscaler. A timer stands in for the start of a virtual
machine. The autoscaler waits for a provisioning delay of 45 to 120~s, which is close to the start-up
times measured in public clouds @hao2021vmstartup. It then adds a worker with one CPU. It removes a
dynamic node when the CPU utilization of that node falls below 50%, the default scale-down threshold of
the Cluster Autoscaler for pod requests @k8sca-faq. The forecast horizon of 135~s covers the longest
delay plus one control cycle.

= GRU forecaster <sec:gru>
*Model.* A two-layer GRU @cho2014learning @chung2014empirical with #G.hidden hidden units reads the last
30 load samples, one sample per 15~s. One dense output layer emits all nine future steps. The forecast
server answers in #G.latency.median ms (median; p95 #G.latency.p95 ms), so the forecast does not delay
the 15~s control loop.

*Leak-free protocol.* We aggregate the ClarkNet HTTP trace @clarknet into 15~s buckets and multiply it
by 33, the factor that the replay uses. We split the series in time order into training, validation and
test portions. Between two portions, we leave a gap of 38 samples, the input length plus the horizon
minus one, so no input window or target crosses into another portion. We fit the input normalization on
the training portion only. We select the hyperparameters and the number of epochs on the validation
portion with the Tree-structured Parzen Estimator @bergstra2011tpe of Optuna @optuna2019. The test
portion takes no part in the selection, because a score on data that guided the selection is biased
@cawley2010overfitting. We train the selected configuration with three seeds and evaluate each model
once on the test portion. The 20-minute window that the experiments replay lies inside the test portion,
so the deployed model never saw it.

#if extended [
  The search ran #G.trials trials for each input length (#G.seq_searched samples) on the first seed. It
  selected a dropout of #G.dropout, a learning rate of #G.lr and a budget of #G.epochs epochs. The margins
  $delta_k$ come from the validation residuals of the selected model. They range from #G.offset_min to
  #G.offset_max RPS over the nine steps. On the test portion, the upper envelope covered #G.gru.coverage
  of the values that the point forecast predicted too low, against a target of 0.90.
]

*Accuracy.* @tab:predictor reports the error on the test portion at the 9-step horizon, in RPS of the
replayed series, over three seeds. A persistence forecast repeats the last value. Skill is the share of
its error that a model removes. The GRU has a skill of #G.gru.skill. It is slightly more accurate than
an LSTM, the model family of ElaX, tuned in the same way, although the LSTM had more training data. The
GRU does not beat a linear autoregression on the same inputs, and none of the #G.levers other variants
that we screened beat the linear model either.

#tab-predictor <tab:predictor>

#if extended [
  The variants were input transforms, a target transform, coarser sampling intervals, a decomposed input
  and two other architectures. The error grows with the horizon at the same rate for both models. The GRU
  RMSE rises from #G.gru_h1 at the first step to #G.gru_h9 at the ninth, and the RMSE of the linear model
  rises from #G.ols_h1 to #G.ols_h9. The input transforms were differencing, exponential and rolling
  statistics, robust and quantile scaling, and reversible instance normalization. The two other
  architectures were N-BEATS and a linear network. Outside the ClarkNet test portion, the GRU kept one
  advantage over the LSTM. On a synthetic spike archetype, its RMSE was #G.gru.spike against
  #G.lstm.spike. On a synthetic trace, the same protocol gives a normalized RMSE of #G.synthetic_nrmse%,
  against #G.gru.nrmse% on the real trace. The protocol can therefore fit a series that is forecastable.
  For scaling, RMSE alone is not the right measure. The scaler acts on the largest value of the envelope,
  so a forecaster that is accurate on average but late on a rising edge still adds pods late.
]

= Experimental setup <sec:setup>
#tab-scenarios <tab:scenarios>

*Testbed.* Two clusters run on one host under k3d, a tool that runs Kubernetes nodes as containers. The
Kubernetes cluster has one static worker plus the dynamic nodes of @sec:design. Docker limits each of
these workers to one CPU. The Knative cluster has one worker with three CPUs. Its autoscaler keeps three
to ten pods, so Knative never scales to zero. Each pod requests 0.3 CPU. Each request computes the 33rd
Fibonacci number (CPU work) and then waits 50~ms (simulated I/O).

*Workload.* The load generator k6 replays a 20-minute ClarkNet window in 40 steps of 30~s, with a mean of
73~RPS and a peak of 164~RPS. Each request slower than the 200~ms SLO counts as one SLO violation, and
one run serves about #F.requests requests.

*Scenarios and batches.* @tab:scenarios lists the four scenarios. Each scenario ran five times in the
scenario batch. S4 and S3 were then compared in pairs of back-to-back runs. Both runs of a pair start from
one static worker and face the same provisioning delay, which the timer cycles through 60, 90, 120, 75
and 45~s from pair to pair, and their order alternates between pairs (counterbalancing) so that a drift
of the host favors neither arm. Pairing cancels much of the run-to-run movement of the p99 that comes
from load on the shared host, and the number of pairs sets how small a difference the test can see. Three
paired batches used the leak-free GRU of @sec:gru, each with its main measure and test level fixed before
the first run. Batch A had five pairs, which reach the 0.05 level only if S4 wins all five, so batches B
and C used ten. B ran on a loaded host, so C, the confirmatory batch, repeated it on a quieter one. We
exclude an earlier five-pair batch that favored S4, because its run records do not identify the
predictor, which was trained on a synthetic trace.

*Tests and validity.* The main measure is the p99 of each run, the 99th percentile of all request
latencies in that run. Our hypothesis is that S4 has a lower p99 than S3. For the paired batches, we
therefore use a one-sided exact paired permutation test at a level of 0.05. We also report a bootstrap
95% interval, the range of mean differences that fits the data, and the paired Cohen's $d$, an effect
size. A run counts only when it passes validity checks. A hybrid run must use the node tier. That is, a
pod must become unschedulable or a dynamic node must be provisioned. An S4 run must also receive every
forecast it requests, use a horizon that covers the provisioning delay, and raise the replica target
from a forecast at least once. Every run of the three paired batches passed (#H.b5.valid of #H.b5.runs,
#H.b10a.valid of #H.b10a.runs and #H.b10b.valid of #H.b10b.runs). Batch C received #H.b10b.delivered of
#H.b10b.eligible forecasts. Batches B and C also recorded the CPU-busy fraction of the host, the share of
non-idle CPU time, sampled from `/proc/stat` during a run.

*Cost.* We project the cost onto AWS prices. Kubernetes maps to an EKS control plane plus t3.medium
nodes, sized from the mean Kubernetes CPU use. Knative maps to Lambda with provisioned concurrency, sized
from the serverless request rate. We scale each 20-minute run to a 30-day month. The projection charges
nodes, not pod-seconds, so it cannot resolve differences smaller than one node running for a month.

#if extended [
  *Run conditioning.* Before each run of the paired batches, the experiment tool sets the static worker
  count and deletes leftover dynamic nodes and their pods. It checks that both backends serve, and that
  the prediction server answers when the scenario needs it. Each run records the hash of the deployed
  predictor in its manifest.

  *Cost model.* The number of Kubernetes nodes is the mean CPU use divided by the allocatable CPU of one
  node at the target utilization, rounded up, plus one. Each dynamic node adds its measured lifetime.
  Lambda provisioned concurrency follows Little's law from the serverless request rate and the measured
  execution time.
]

= Results <sec:results>
== Hybrids compared with single-platform baselines
@tab:four and @fig:runs compare the four scenarios. S2 gave
the lowest p99, but its cost of #F.s2.cost USD per month is more than twice that of any scenario with
Kubernetes. The comparison with S2 is not fair, because S2 ran three always-warm pods on a three-CPU
worker, while S1 started from one pod on a one-CPU worker. The two hybrids had the same
projected cost as S1 within the resolution of the projection. They used #F.s3_pods_below_s1% (S3) and
#F.s4_pods_below_s1% (S4) fewer Kubernetes pod-seconds than S1. This count excludes the Knative pods,
and each hybrid also kept at least three Knative pods warm, so the hybrids did not save pods in total.
The reactive hybrid did not improve latency over the HPA. Its p99 was #F.s3.p99 ms against #F.s1.p99 ms
for S1, with more SLO violations, and one of its five runs exceeded the SLO.

#tab-four <tab:four>
#fig-runs <fig:runs>

The S4 row needs a caveat. This batch ran before the leak-free GRU of @sec:gru existed. Its run
manifests do not record the predictor. Its logged margin was about 10~RPS, against #G.offset_min to
#G.offset_max RPS for the leak-free GRU. In this batch, S4 held the p99
at #F.s4.p99 ms, #F.s4_vs_s1.abs_pct% below S1 (two-sided Mann-Whitney $p = #F.s4_vs_s1.p$). This row
does not measure the forecaster of @sec:gru. The paired batches do.

== Predictive compared with reactive scaling
@tab:h2 and @fig:forest give the paired results. Batch A favored S3. Batch B favored S4, but not
significantly. The confirmatory batch C gave a difference of #H.b10b.diff ms ($p = #H.b10b.p$,
$d = #H.b10b.d$), and S4 was faster in #H.b10b.wins of #H.b10b.n pairs. The data therefore do not
support the hypothesis that the forecast lowers the p99. The pair differences of batch C have a standard
deviation of #H.b10b.diff_sd ms, so ten pairs can detect a difference of about #H.b10b.mde ms or more with
80% power. The lower end of the interval, #H.b10b.ci_lo ms, is the largest p99 reduction that the data
still allow. In batches A and B, the mean p99 of both arms was above the 200~ms SLO. In batch C, it was
below. Pooled over #H.pooled.n pairs, the difference is #H.pooled.diff ms, and the interval includes
zero. The batches ran under different host load, so the pooled row is only descriptive.

#tab-h2 <tab:h2>
#fig-forest <fig:forest>

In batch B, the peak CPU-busy fraction of the host correlated with p99 (Pearson correlation
#H.b10a.busy_p99_r). In the #H.b10a.quiet.n pairs of batch B where both runs peaked below 0.4 (a post-hoc
subset), the difference was #H.b10a.quiet.diff ms (uncorrected
$p = #H.b10a.quiet.p$). Batch C ran on a quieter host, with a mean CPU-busy fraction between
#H.b10b.busy_avg_min and #H.b10b.busy_avg_max, and did not reproduce that difference.

#if extended [
  In batch C, the correlation fell to #H.b10b.busy_p99_r, and #H.b10b.busy_peak_over_half of 20 runs still
  had a host CPU-busy peak above 0.5. The mean SLO violations per run were #H.b10b.slo_s3 for S3 and
  #H.b10b.slo_s4 for S4.
]

== Effect of the GRU forecast
The effect of the GRU splits into three questions. First, did the forecast change what the scaler did? It
did. In batch C, S4 made #H.b10b.proactive scale-ups in which the forecast target was above the
observed-load target, and it used #H.b10b.replica_pct% more pod-seconds than S3. The extra pods lowered
the mean serverless weight from #H.b10b.share_s3% to #H.b10b.share_s4% and cut the share of time with
traffic to Knative from #H.b10b.active_s3% to #H.b10b.active_s4%. The projected cost stayed the same
(USD #H.b10b.cost_s3 for S3 and #H.b10b.cost_s4 for S4 per month), because both arms used the same node
tier.

Second, did the extra pods make requests faster? Not measurably (@tab:h2). The likely but untested
reason is that, until the first of about #H.b10b.nodes dynamic nodes per run was ready, the router sent
the excess load to Knative in both arms. The reactive arm thus already had serverless capacity during the
delay that the forecast was meant to cover. We did not record which backend served the slowest requests,
so they may have come from Knative, from pods still starting, or from the shared host.

Third, did the GRU itself cause the extra pods? Our design cannot tell. The margin alone adds
#G.offset_min to #G.offset_max RPS, or three to four pods, to a mean load of 73~RPS, and the hold keeps
these pods for 90~s. The GRU is also no more accurate than a linear autoregression (@tab:predictor), so a
simpler forecast with the same margin may add the same pods. Our pairs compare a forecast with no
forecast, not the GRU with a simpler forecast.

= Discussion <sec:discussion>
The reason given in @sec:results for the missing latency gain also explains why our result differs from
Spock's. We did not test it, for example by removing the Knative backend. Spock found a gain for its
predictive policy in simulation @gunasekaran2019spock, but its forecast sizes machines for the average
rate and leaves the peaks to Lambda. Our scaler adds pods for the peak, which Knative already serves. A
forecast is more likely to help where no backend covers the delay: in a deployment without an overflow
backend, with one that cannot take the whole excess, or after a scale-down that removes capacity the
load soon needs again.

*Threats to validity.* All clusters share one host, so the testbed simulates two platforms, not two
clouds. A timer simulates the provisioning delay. The workload is one 20-minute window of one trace,
served by one function. Algorithm 2 ran with one parameter set, and a smaller margin or a shorter hold
would change what the forecast costs. The cost is a projection of measured resource use onto public
prices, not a bill. Batch B ran on a loaded host, with a mean CPU-busy fraction up to
#H.b10a.busy_avg_max, and batch A has no host record.

= Conclusion
We ran a capacity-aware router and an ElaX-derived replica scaler in one 15~s loop over Kubernetes and
Knative. Both hybrids had the same projected cost as Kubernetes with the HPA, and the reactive hybrid had
a higher p99. In ten pre-specified pairs, the GRU forecast added pods but gave no measurable latency
gain. The next experiment is a constant-margin baseline. If it matches S4, the GRU adds nothing beyond
its margin. We also plan to set the margin from the measured provisioning delay, and to test the scaler
without a serverless backend, where a forecast has a delay to cover.

#if extended [
  = Data availability
  The run bundles, the analysis code and the script that derives every number in this paper from the
  bundles are available from the corresponding author on request.
]
]
