# Review of `paper/conference-named.pdf` (ICAIIC 2027 build, 6 pages)

Reader model: ML/networking TPC member, not a Kubernetes specialist, about 20 minutes. Page numbers are PDF pages. Every measured value is treated as fixed. "Derived" means arithmetic on numbers already printed. Nothing below asks for a new experiment.

I checked internal arithmetic against the tables. It holds. The skill 0.216, 22%, d = −0.16, 72 ms, the pooled −16.5 ms (weighted from A, B and C), the 15/25 wins, the 135 s horizon and the 38-sample embargo all recompute. The problems are definitions, framing, naming and space, not arithmetic.

---

## 1. First-read failures

### 1a. Terms used before definition, or never defined

| Term | First use | Status | Fix |
|---|---|---|---|
| **p99** | p.1 abstract | Never defined. "Mean p99", "per-run p99" and "tail latency" are all used. | At first use: "99th-percentile latency (p99)". In §V: "The per-run p99 is the 99th percentile of all request latencies in one run; tables report its mean over runs." |
| **SLO** | p.1 contribution 1 ("200 ms p99 service-level objective (SLO)") | Defined once and late. The abstract never says what the target is. | Put "a 200 ms p99 latency target (SLO)" in the abstract, or drop the acronym there. |
| **HPA** | p.1 abstract; spelled out p.1 intro | The abstract uses it undefined. | Write "the Kubernetes Horizontal Pod Autoscaler (HPA)" in the abstract. Drop the intro expansion. |
| **KPA** | p.2 Fig. 1; p.4 Table III | Never expanded. | Write "Knative Pod Autoscaler (KPA)" in the Table III row, or delete it from Fig. 1 ("3–10 warm pods" is enough). |
| **Knative** | p.1 abstract | Never glossed. | "Knative, a serverless platform that runs on Kubernetes". |
| **pod, replica, node** | p.1 abstract | Never defined. The paper alternates "pod" and "replica" with no statement that they are the same. | One sentence at first intro use: "A pod is one running copy (replica) of the service; nodes are the machines that host pods." |
| **pod-seconds** | p.1 abstract (headline result) | Never defined. Table IV (p.4) says "Pod-s is Kubernetes replica-seconds per run". | Define at first use: "pod-seconds (the sum over time of the number of running Kubernetes pods)". Say it excludes Knative pods (see 2c). |
| **replica-seconds** | p.4 Table IV caption only | Second name for pod-seconds. | Delete, use "pod-seconds". |
| **upper envelope** | p.1 abstract | Defined only in Eq. (2) on p.3. The abstract and Fig. 1 use it cold. | Abstract: "the forecast plus a safety margin (its upper envelope)". Intro: one clause of definition. |
| **leak-free** | p.1 abstract, contribution 2, 3 | Never defined as a term. §IV describes a procedure but never says what leaked or what "leak-free" excludes. | At first use: "a leak-free protocol (no test data, and no data near the test boundary, enters training or tuning)". |
| **embargo** | p.3 §IV | The length is given ("input length plus horizon minus one"), the purpose is not. | "a gap (embargo) of 38 samples at each split boundary, so that no input window or forecast target spans two portions". |
| **skill** | p.1 abstract (0.216) | Defined only by a formula in the Table II caption on p.3. The text also says "22%" for the same quantity. | Abstract: "forecast skill 0.216 (error reduction over persistence)". Use one form, skill or %, not both. |
| **persistence** | p.1 abstract | Never defined. | "persistence (the last observed value repeated)". |
| **weight-time product** | p.4 Table IV caption; p.5 §VI.C | Undefined. It is the "Serverless" column. | Derived reading: the time-average of the serverless weight over the run, 0–100%. Say so in the caption: "Serverless: time-averaged share of requests routed to Knative." |
| **CPU-busy** | p.4 end of §V; p.5 | Fraction of what, sampled how, peak or mean? | "host CPU-busy fraction (share of non-idle CPU time on the shared host, sampled during the run)". |
| **decision factor** | p.1 contribution 2; p.2 Table I ("Decision factor v") | Never defined in prose. In Algorithm 2 line 5 the label sits next to T_p = R(max û), a replica count. In the text it is max û, a load. In Table I it is "v". These are three different objects. | Define once: "the decision factor v is the load value from which the replica count is computed". Then use v everywhere, or drop the phrase. |
| **counterbalanced** | p.1 abstract, contribution 3 | Never defined. §V says only "counterbalanced pairs, each pair starting from one static worker and both runs of a pair using the same provisioning delay". That describes pairing, not counterbalancing. | State what is balanced: "the order of S3 and S4 within a pair alternated". If the delay cycle (journal-only text) is the balancing, say that. |
| **pre-specified** | p.1 abstract; p.6 conclusion | The body says only "(10 pairs, with the test fixed in advance)". What was fixed: endpoint, test, sample size, direction? | See 2d. |
| **validity gates** | p.1 contribution 3 | Not explained until the last third of p.4, and then only for S4. | Contribution 3: "...with run-level validity checks (§V)". In §V list the gates for S3 too, or say S3 has none. |
| **S1–S4** | p.1 (inline), p.2 Fig. 1 caption | Defined inline in contribution 3, in the order S1, S2, S4, S3. Table III is on p.4. | Move Table III to just after the contributions, or put "S3 reactive, S4 predictive" in the Fig. 1 caption. Keep a fixed order S1, S2, S3, S4. |
| **batches A–C** | p.3–4 end of §V | Introduced mid-paragraph across a column break. The four-scenario batch has no label ("one batch", "this batch", "batch of August 2026"). | See 3a. |
| **provisioning delay / gap / lag / boot time** | p.1, p.2 Fig. 1, p.3 §III.C | Four names. The reader cannot tell the delay is a timer in the simulator, not measured. | One name ("node provisioning delay"). State once: "a timer of 45–120 s that stands in for VM boot time". |
| **ready pods** | p.1 abstract | "Ready" is Kubernetes jargon (passed its readiness probe). | "running pods that can take traffic (ready pods)". |
| **proactive scale-up** | p.5 §VI.C | Used as a count (26), not defined. | "a scale-up that happened because the forecast target exceeded the observed-load target". |
| **"capacity failure"** | p.3 §III.A: "The 50% cap bounds the serverless cost of a capacity failure." | Undefined. | "...if the capacity estimate r_eff is wrong". |
| **"budget"** | p.3 §III.A: "when SLO violations use up a budget too fast" | Undefined. | Cut with the pacing term (see 1c). |
| **post-hoc subset, "uncorrected p"** | p.5 | Fine for this audience, but "it" in "did not reproduce it" has no clear antecedent. | See 1c. |
| **Tool names** (k3d, k6, HAProxy, Prometheus, FastAPI, EKS, t3.medium, provisioned concurrency) | p.2–4 | No gloss. This audience will not know k3d or k6. | One parenthetical each at most ("k6, an HTTP load generator"). Cut FastAPI and the TPE/Optuna sentence; they help no one. |

### 1b. Symbol collisions that cost a re-read

- **"The scaler is fitted on the training portion only"** (p.3 §IV, Leak-free protocol). "Scaler" here means the data standardiser (z-score). Everywhere else "the scaler" is the replica scaler (abstract: "The scaler takes the largest upper-envelope value"). A reader will think the replica controller is trained. Fix: "The input normalisation is fitted on the training portion only."
- **C** is the ready capacity (Eq. 1, Alg. 1) and also **batch C**. **n** is ready pods (Alg. 1) and the number of pairs (Table V). **r** is desired replicas (Alg. 2), r_eff and r_sat (§III.A), and the Pearson correlation (p.5). **u** is target utilisation (§III.A) and Fig. 1 labels the envelope "û". **p** is the p-value, p99 and p_burn. **k** is the horizon step and k6/k3d are tools.
  Fix: rename batches (see 3a), use ρ or "corr." for the correlation, give pair count its own letter (N_pairs) or drop "n" from Table V.
- **Algorithm 2 line 1 "desired replicas r"** is used in line 8 as the *current* count ("if T > r ... scale to T"; "T < 0.75r"). Rename to "current replicas r" in the input line.
- Four unrelated 50% figures sit close together: the 50% serverless cap (§III.A), u = 0.5 (§III.A), HPA target 50% CPU (Table III), node removal below 50% utilisation (§III.C). A reader cannot tell which are the same parameter. Say "each of these is a separate setting" in one clause, or name them (w_max, u, ...).

### 1c. Sentences I read twice

Quoted, with the reason and a replacement.

1. p.1 abstract: "**The scaler takes the largest upper-envelope value over the next 135 s and uses it only when it asks for more replicas than the observed load does.**" "It asks" has two possible antecedents. "Largest upper-envelope value" of what is not said.
   → "The scaler sizes the deployment for the highest forecast load over the next 135 s, plus a safety margin, and uses that size only if it exceeds the size the observed load needs."
2. p.1 abstract: "**the two hybrids used 30% to 36% fewer pod-seconds**". "Two hybrids" is not set up: the abstract never names a reactive and a predictive variant. The reader has also just read about the leak-free GRU, so assumes the predictive hybrid uses it. It does not (see 2a).
   → "the reactive and predictive hybrids used ..." plus the caveat in 2a.
3. p.1 abstract: "**the forecast changed p99 by −13.6 ms (95% CI ..., p = 0.307) and added 45% more pod-seconds**". Changed relative to what? Reactive S3 is never named. Direction of the test and of the minus sign are not given.
   → "adding the forecast to the reactive hybrid changed p99 by −13.6 ms (negative = faster; ...)".
4. p.1 intro: "**Serverless platforms such as Knative scale the other way.**" "The other way" is unclear; the previous sentence is about latency rising.
   → "Serverless platforms such as Knative react faster."
5. p.1 intro: "**a serverless backend that absorbs the burst hides a late replica.**" Compressed to the point of riddle; it is the paper's central mechanism.
   → "...and a serverless backend that absorbs the burst masks the cost of adding a replica late."
6. p.1 intro: "**makes the first of these decisions from a forecast.**" "First" is two paragraphs back.
   → "makes the replica-count decision from a forecast."
7. p.1 intro: "**ElaX manages one container cluster. Its hourly horizon is long compared with the minute-scale surges of web traffic, and it makes no routing decision.**" Three facts, one gap-motivating claim. The reader cannot tell which is the weakness this paper addresses.
   → Split into "ElaX has no routing decision" (the gap) and "its hourly horizon is long next to minute-scale surges" (the reason the horizon changes).
8. p.3 §III.A: "**It counts at most one violation per 15 s decision, so it does not reach its threshold within a 20-minute run.**" Threshold, budget and pacing are all undefined. The sentence says a mechanism in Algorithm 1 never activates in any experiment. Cut it (see 4).
9. p.3 §IV: "**multiplied by 33, the factor the replay uses**". Why scale a trace? Reader cannot tell if the factor is a time-scale change or an amplitude change.
   → "scaled by 33 so that the peak load fills the testbed (the same factor the replay uses)". Check that this is the real reason before using it.
10. p.3 §IV Accuracy: "**none of the 12 variants that we screened beat the linear model on the selection folds either [29].**" Three problems: "selection folds" appear nowhere else (§IV says "validation portion"); the variants are not named in the conference build; [29] is a paper on model-selection bias and does not show that the 12 variants failed.
    → "None of 12 further variants (input transforms, a target transform, coarser sampling, two other architectures) beat it on the validation portion." Move [29] to a sentence about why selection was done on a separate portion. Do not leave the citation where it is.
11. p.4 §V: "**Three paired batches used the ClarkNet-trained GRU of Section IV: A (5 pairs), B (10 pairs) and C (10 pairs, with the test fixed in advance).**" Crosses a column break. Reader meets A, B, C with no purpose or order given, and "fixed in advance" has no object.
12. p.4 §VI.A: "**S4 held p99 at 99.1 ms, 10.2% lower than S1 (two-sided Mann-Whitney p = 0.151, five runs per arm).**" Reads as a result, then undone three sentences later ("its S4 row does not measure the forecaster of Section IV"). Also switches from the one-sided paired tests of §VI.B to a two-sided test with no explanation.
13. p.4 §VI.A: "**S3 had the highest mean and spread in this batch.**" Says nothing about the fact that S3 (151.6 ms, 399.6 violations) is worse than S1 (110.3 ms, 50.6) on both. See 2b.
14. p.5 §VI.B: "**Host load is associated with part of the spread between batches.**" Vague ("part of", "associated").
    → "In batch B, peak host CPU-busy correlated with p99 (r = 0.69)." and delete the lead sentence.
15. p.5 §VI.B: "**Batch C ... did not reproduce it.**" "It" is the −101.3 ms difference, not the correlation. Both are in the preceding sentences.
    → "Batch C ... showed no such effect (−13.6 ms)."
16. p.5 §VI.C: "**(USD 192 against 191 per month)**". Which arm is 192? Order is not given.
    → "(S3 USD 192, S4 USD 191 per month)" — confirm which is which in the data; the order in the text is not self-evident.
17. p.5 §VI.C: "**S4 asked for near-peak capacity early**". The envelope adds 55–60 RPS to a mean of 73 (about 130 RPS) while the peak is 164. "Near-peak" is loose.
    → "S4 asked for about 130 RPS of capacity (mean plus margin) early, against a 164 RPS peak." (derived)
18. p.5 §VI.C: "**lowered the serverless share ... only from 4.0% to 3.2%**". "Only" frames a 20% relative drop as trivial without argument. Also Table IV gives 4.2% and 2.8% for a different batch, which the reader may confuse with these.
    → "from 4.0% to 3.2% (batch C)".
19. p.4–5 §V: "**k6 replays a 20-minute ClarkNet window (40 steps of 30 s)**" against §IV "aggregated into 15 s buckets". Reader cannot tell if the GRU sees the same piecewise-constant 30 s load it was trained on. One clause ("the 15 s series is replayed at 30 s resolution") would close it.

---

## 2. Argument

### 2a. Can the reader state contributions, result and limit from abstract plus intro?

**Contributions: yes, as a list. Main result: only partly. Limit: no.**

- The abstract states six things in this order: architecture, extension, a forecast-accuracy finding, cost finding, a hybrid-vs-HPA finding, then the null result. The null result, the paper's actual headline, arrives in the last sentence and leaves out its baseline (S3), its direction convention and its limit.
- The three contributions are *artifacts* (architecture, extension, evaluation). None is a finding. The two findings that a TPC member will remember are not listed: (i) a forecast added to a reactive hybrid gave no measurable latency gain and cost 45% more pod-seconds, and (ii) the GRU does not beat a linear autoregression. A reader who stops at the intro list will think the paper delivers a better scaler.
- The research question appears only in the sixth intro paragraph ("This paper asks whether ElaX's forecast-driven scaling decision still helps when it runs inside a hybrid"). It is the best sentence in the paper and should move up, into the abstract.
- The limit (ten pairs detect effects above about 72 ms with 80% power) is on p.5 in "Threats to validity". It is the single fact that makes the null result interpretable and must be reachable from the abstract or intro.

Replacement shape for the contribution list (same content):
1. A hybrid control architecture: a capacity-aware router (Alg. 1) and an ElaX-derived replica scaler (Alg. 2) in one 15 s loop.
2. A forecast-driven decision factor for the scaler (135 s GRU upper envelope) and a leak-free protocol to train it.
3. A paired test of whether that forecast helps: no measurable gain (−13.6 ms, 95% CI [−63.5, +35.6]) at 45% more pod-seconds; ten pairs detect only effects above about 72 ms.

Title: "Scaling Kubernetes Replicas with GRU Forecasts and Routing Overflow to Serverless" promises a method that works. The finding is that the forecast did not help. A title that says so is no less honest: "Does a GRU Forecast Help a Kubernetes–Serverless Hybrid? A Paired Test of Predictive Replica Scaling".

### 2b. Undersell and oversell

**Oversold**

- **Abstract/intro/conclusion, "the two hybrids used 30% to 36% fewer pod-seconds ... at the same projected cost".** Four reasons the sentence claims more than the evidence:
  1. Pod-seconds counts Kubernetes pods only (Table IV: S2 = 0). Knative's 3–10 always-warm pods are not counted. Derived and [INFERENCE] (assumes the three Knative pods run the full 20 min, as §V "never scales to zero" and Table III imply): adding 3 × 1200 = 3600 pod-seconds to S3's 6,939 gives about 10,539, only about 3% below S1's 10,840; S4's 7,614 + 3,600 = 11,214 is above S1. The pod types and sizes differ, so this is not a clean sum, but a reviewer will do it. Say plainly that the column counts Kubernetes pods only, and soften "fewer pod-seconds" accordingly.
  2. §V says the cost projection "charges nodes, not pod-seconds, so it does not resolve differences smaller than about one node-month". "Same projected cost" (170/172/173 USD) therefore means "not resolved", and the 30–36% saving never shows up in cost. The abstract states both as if they supported each other.
  3. The abstract's S4 is not the leak-free GRU (Table IV footnote a, p.4; §VII). The abstract says nothing of this, and the preceding sentence is about the leak-free GRU. The four-scenario claim should be worded with the S3 hybrid, or state "S4 with an earlier predictor".
  4. Hybrid S3 has worse tail latency and 8 times the SLO violations of S1 (151.6 ± 54.3 ms vs 110.3 ± 7.5; 399.6 vs 50.6). The paper reports S4's 10.2% advantage over S1 (p = 0.151) and says S3 "had the highest mean and spread", but never says the reactive hybrid is worse than plain HPA. The abstract reports cost and pod-seconds only. A TPC member who reads Table IV will ask what the hybrid buys; the paper's own answer is "nothing measurable on latency, nothing resolved on cost". Say it: "the reactive hybrid did not improve latency over HPA".
- **SLO in contribution 1** ("under a 200 ms p99 service-level objective"): in Table V the mean p99 of S3 and S4 is 503/656 ms (A) and 420/316 ms (B), 2 to 3 times the SLO. Only batch C is below 200 ms. The paper never states that the hybrids missed their own SLO in two of three batches. Add one sentence in §VI.B.
- **Related work, "which lets us measure the effect of the forecast alone".** True of the routing weight design, but pods added by the forecast still change the router's weight via ready pods (§III.A last sentence). "Alone" is slightly strong; the paper itself says "A forecast changes it only through the pods that Algorithm 2 adds". Use "isolates the forecast's effect on the replica decision".
- **Section VI.C title "Why the forecast did not help"** asserts a cause; the body and §VII hedge ("consistent with", "we did not test this directly"). Retitle "A possible reason".
- **Pooled p and d in Table V** (0.448, −0.03) next to the statement that the pooled estimate is "descriptive". A p-value is not descriptive. Drop pooled p and d, or label the row "descriptive, no test".

**Undersold**

- The CI of batch C ([−63.5, +35.6]) *excludes* a reduction larger than 64 ms, about 40% of S3's mean p99 (160.4). That is a positive statement the data support and the paper does not make; it is stronger than "no measurable gain". Add: "the data rule out a p99 reduction larger than about 64 ms in this setup".
- 22% / skill 0.216 for the GRU is reported as a strength in the abstract, while Table II shows the linear autoregression is better on both RMSE (29.46 vs 29.64) and, derived, skill (0.221 vs 0.216). The abstract says "but not a linear autoregression", which is honest, but the Table II "Skill" cell for linear autoregression is blank ("–"). A reader computing 1 − 29.46/37.81 sees it is higher than the GRU's. Fill the blank (derived) for all rows: linear 0.221, trend −0.23, seasonal −0.42. Hiding the best row looks evasive.
- The paper reports the null result honestly, and §VII is the best section. It is also the one that is least findable. Its content (what was not tested, what a forecast might help) is half the paper's value and is placed after the results as an afterthought.

### 2c. What a reviewer needs to trust the null result and cannot find on the page

| Missing | Where a reviewer looks | Material the paper already has |
|---|---|---|
| What was pre-specified | abstract, §V "with the test fixed in advance" | The text names only "the test". State exactly what was fixed before batch C: endpoint (per-run p99), test (one-sided paired permutation), n (10 pairs), direction (S4 faster). If sample size and direction were not fixed, do not write "pre-specified" in the abstract and conclusion; write "a confirmatory batch of ten pairs". |
| Why A and B are not the primary result | §V | One sentence: A and B were exploratory, with n of 5 and 10, one under unrecorded host load (journal-only: "batch A has no host record"). |
| The sequence of batches | §V | A, B, C is a time order. State that C was run after A and B. |
| Whether runs were discarded | §V | "All 20 of 20 runs of batch C passed". Nothing for A, B or the four-scenario batch. State counts or "no run failed a gate". |
| An earlier batch reported a significant S4 advantage | journal-only, §VI.B extended | The conference text omits it. A TPC member aware of earlier reports (or the author's own earlier posts) will see five-pair, p-hacking-shaped selective reporting. The journal text says it was excluded because the predictor was trained on a synthetic trace and the manifests do not identify it. One sentence in the conference text covers this. |
| Power | p.5 end of §VII | Move "ten pairs detect only effects above about 72 ms (80% power)" into §V or §VI.B and the abstract. |
| Counterbalancing | §V | See 1a. The journal text says the delay cycles through 60, 90, 120, 75, 45 s per pair, which is the real balancing device. |
| That the delay is a timer | §III.C, Fig. 1 | Journal-only "The provisioning delay is simulated by a timer, not measured from a cloud provider". It is the main threat to the setting in which a forecast should matter, and is absent in the conference build. Add to Threats. |
| Single 20-minute window of one trace, one parameter set for Algorithm 2 | §VII | Both journal-only. Both belong in the conference Threats paragraph; they cost two lines. |
| Pod size and pods per node | §V | R_min = 3 pods on a 1-CPU worker implies a pod is about one third of a CPU (derived from r_sat = 100 RPS for three pods); the paper never says so. The node-tier story ("pending pod triggers a node") needs it. |
| Total requests per run | Table IV | "SLO viol." as a count (399.6) has no denominator. About 88,000 requests per run (derived: 73 RPS × 1200 s). Give a rate or the denominator. |
| The earlier-GRU leak | §VI.A, Table IV footnote | The text contrasts the "leak-free GRU" with "an earlier GRU" without saying the earlier one was not leak-free. A TPC member will infer it ([INFERENCE]). If true, say so in one sentence; do not leave the reader to infer that a reported result came from a leaky predictor. |

---

## 3. Consistency

### 3a. One thing, several names

| Thing | Names used (with location) | Pick |
|---|---|---|
| Pod-seconds | "pod-seconds" (abstract, p.1, p.5); "Pod-s" (Table IV header); "Kubernetes replica-seconds" (Table IV caption); "pods used" | "pod-seconds" |
| Replica / pod | "replica" (scaler, Alg. 2, abstract), "pod" (HPA, ready pods), "ready replicas n" (Alg. 1 input line) vs "ready pods n" (text, Fig. 1) | "pod" for the object, "replica count" for the number; fix Alg. 1 input to "ready pods n" |
| Forecast | "forecast", "prediction" (§IV title "forecaster"; Fig. 2 caption "ClarkNet-trained predictor"; "predictor family of ElaX"; Table I row "Predictor"; "predictive hybrid"; "predictive control"; "predictive scaling"; journal "prediction server") | "forecast" for the output, "forecaster" for the model; "predictive" only as the adjective for S4, and say so once |
| Replica controller | "replica scaler" (abstract), "the scaler" (abstract, §III.B), "ElaX-derived scaler", "scaling decision", "Algorithm 2", "S4's scaler"; and "scaler" = data normaliser in §IV | "replica scaler" or "Algorithm 2", pick one; rename the normaliser |
| Router | "capacity-aware router" (abstract), "router" (intro), "Algorithm 1", "capacity-aware routing" (Fig. 1), "routing daemon" (Fig. 1, which also runs Algorithm 2), "daemon" (§III), "HAProxy" (the actual splitter) | "router" for Algorithm 1; "control daemon" for the loop; "HAProxy" only for the proxy |
| Serverless | "serverless" (abstract), "Knative" (abstract, §V), "serverless backend", "overflow backend" (§VII), "Knative service", "Knative serverless services" (contribution 1), "serverless-only (Knative, S2)" | "Knative backend" once defined as the serverless backend; avoid "overflow backend" and "serverless platform" |
| Serverless share | "serverless share", "serverless weight" (w_sls), "serverless share of the HAProxy weight-time product", "fraction of time with any traffic to Knative", "Serverless" (Table IV column) | "serverless weight" for the setting, "serverless share" for the time average; define once |
| Forecast margin | "upper envelope" (û), "envelope", "envelope offset" (Table IV caption), "margin" (conclusion: "constant-margin baseline", "set the margin", §VII "same margin"), δ_k, "offset" | "upper envelope" for û; "margin" for δ_k; kill "offset" |
| The decision input | "decision factor" (contribution 2, Table I), "forecast target" T_p (Alg. 2), "forecast target" (text), "target" T | decision factor = v (a load); T = target replica count; T_p = forecast target; make Alg. 2 line 5's comment say "forecast target" |
| Provisioning lag | "provisioning gap" (intro, §VII), "provisioning delay" (§III.C, §V), "boot" (intro), "window" (intro), "lag" (related work) | "provisioning delay" |
| Hybrid variants | "hybrid-predictive scenario (S4)" (Fig. 1), "predictive hybrid (S4)" (§III.B), "predictive (S4)" (contribution 3), "S4"; "reactive hybrid (S3)", "reactive (S3)" | "reactive hybrid (S3)", "predictive hybrid (S4)" throughout |
| Baselines | "Kubernetes with HPA", "Kubernetes-only (HPA, S1)", "S1", "single-platform baselines" (§VI.A title) | "S1 (Kubernetes with HPA)", "S2 (Knative)" |
| GRUs | "the GRU", "the leak-free GRU", "the ClarkNet-trained GRU" (§V), "an earlier GRU", "the forecaster of Section IV", "the model of Section IV" | "the leak-free GRU" vs "the earlier GRU", used consistently; drop "ClarkNet-trained" |
| Batches | "one batch" (§V), "the four-scenario batch" (intro, §VII, conclusion), "this batch", "batch of August 2026" (Table IV), "A/B/C", "paired batches", "a pre-specified batch of ten counterbalanced pairs" (abstract) = "batch C" | Name them. Suggestion: "scenario batch" for S1–S4; paired batches P1, P2, P3 (so "C" does not collide with capacity C); say P3 is confirmatory |
| Test | "the test" (statistical, §V), "the test portion" (data split, §IV), "the test fixed in advance" | "the pre-specified test" vs "the held-out portion" |
| Node tier | "node tier", "dynamic node tier", "node autoscaler" (Fig. 1), "Cluster Autoscaler policy" (§III.C), "dynamic node", "static worker" | "node autoscaler"; "static worker" vs "dynamic node" |
| Latency | "tail latency", "p99", "p99 latency", "per-run p99", "mean p99" | "p99" after the first definition |
| Request rate | "load x", "request rate x", "observed load", "x_obs" (30 s mean), "traffic" | "load x (requests per second)"; say x_obs is the 30 s mean once, near Eq. (1) |
| "Weight" | "w", "w'", "w_sls", "weights (w_k8s, w_sls)", "routing weight", "weight-time product" | acceptable if w' is described as "the new weight" |

### 3b. Equations, algorithms, tables and figure against each other

- **Eq. (1) vs Algorithm 1.** Eq. (1) is the burst share alone. Algorithm 1 line 5 adds p_burn and clamps. The paragraph below Eq. (1) says the weight "therefore follows observed load and ready capacity". Eq. (1) is thus *not* what Algorithm 1 computes. The mismatch disappears when p_burn is removed (see 4); otherwise add p_burn to Eq. (1).
- **Eq. (1) "if x ≤ C"**, Algorithm 1 line 3 "if x ≤ C then w' ← 0": consistent. The ceiling and the 50 cap match.
- **Algorithm 1 inputs** "ready replicas n" vs text and Fig. 1 "ready pods n".
- **Algorithm 2 input** "desired replicas r": used as current replicas (§1b).
- **Algorithm 2 line 5** "▷ decision factor" next to T_p ← R(max û): the comment marks a replica count, but the text calls max û the decision factor and Table I writes it as "v".
- **Algorithm 2 lines 8–10**: "15 s since last scale-up" is always true in a 15 s loop (redundant); "max(T, R_min)" is redundant since R(·) already clamps. Table I and §III.B list the 90 s hold, 0.75, 120 s and 140 ms; Algorithm 2 shows them. These are consistent. The 140 ms threshold is unexplained (0.7 of the SLO?).
- **Fig. 1** box shows "R(v) = ⌈αv + β⌉" with no clamp or R_min/R_max; §III.B and Algorithm 2 show the clamp. Fig. 1 labels the envelope "û" and the text defines û_{t+k}; harmless. Fig. 1 gives the delay as "45–120 s", §III.C "45 to 120 s", intro "one to two minutes". Consistent enough.
- **Fig. 1 vs §III**: Fig. 1 labels the dashed box "routing daemon" and puts Algorithm 2 inside it, so the daemon that "routes" also scales. It shows an arrow Alg. 2 → Kubernetes backend ("replicas") but no arrow from the pending-pod event to the node autoscaler's input, and no arrow showing x and p99 feeding Algorithm 2. It shows "Node autoscaler" feeding the Kubernetes backend.
- **Table I** says "Decision factor v: largest upper-envelope value in the next 135 s, used only if its target exceeds R(x_obs)". The text defines the decision factor as the largest value of û. The condition belongs to Algorithm 2, not to the factor. Also in Table I "ElaX: Dimension: horizontal and vertical" and "This work: horizontal pods; node tier separate": the paper's own node tier is a vertical-ish extension handled elsewhere; say "horizontal only".
- **Table I "Feedback"** cell "not reimplemented; cooldowns and a p99 guard on scale-down" mixes a negative with a replacement. → "ElaX's slack-based controller is not reimplemented; scale-down uses cooldowns and a p99 guard instead."
- **Table III vs Algorithm 2.** S1 is "1–10 pods" while S3/S4 have R_min = 3 and S2 "3–10". Minimum capacity differs between S1 and the hybrids; this matters for the S1 comparison and is not mentioned in the conference text.
- **Table IV vs §VI.C numbers.** Serverless share S3 4.2%, S4 2.8% (Table IV, scenario batch) vs 4.0% and 3.2% (§VI.C, batch C). Different batches, same label. Add "batch C" in the §VI.C sentence.
- **Table IV vs abstract.** Table IV: S4 7,614 vs S1 10,840 = 29.8% (abstract "30%"). S3 6,939 = 36.0% ("36%"). Match. The cost row 170–173 and the claim "same" match. "more than twice" (391 vs 173 = 2.26) matches.
- **Table V vs text.** C: −13.6 [−63.5, +35.6], p = 0.307, d = −0.16, wins 5/10 matches p.4 text and abstract. A: S3 favoured (+153.3) matches "Batch A favoured S3". B: −104.2, "favoured S4 without significance" matches. Pooled mean −16.5 = (5·153.3 − 10·104.2 − 10·13.6)/25: matches.
- **Table II vs text.** 22% matches skill 0.216 (1 − 29.64/37.81). "Slightly lower than an LSTM" matches (29.64 vs 29.92). "Does not beat linear autoregression" matches (29.46). The GRU's MAE (22.49) is 0.03 above the linear's (22.46): nearly tied on MAE. The text says "no more accurate" which is fair. The "± 0.016" vs "± 0.159" are across seeds; the caption does not say so.
- **Power statement.** "sd of 84 ms ... 72 ms at 80% power" recomputes: (1.833 + 0.88) × 84/√10 ≈ 72. Consistent with the CI half-width ≈ 50.
- **§VI.A text vs Table IV for S2.** Text: "Serverless alone gave the lowest tail latency"; Table IV S2 = 79.7 ms. Consistent.
- **Embargo, horizon.** 30 + 9 − 1 = 38 and 9 × 15 = 135 = 120 + 15: consistent.
- **One-sided vs two-sided.** Paired tests are one-sided (S4 faster), the S4-vs-S1 Mann-Whitney is two-sided. No reason is given for the change.

---

## 4. Structure and space

### Page 6, measured on the 110 dpi render

Page 6 holds the last seven lines of the reference list ([27] tail, [28], [29]) in the *left column only*: from y = 120 to y = 262 of a 1287 px page, i.e. 142 px out of a 1,027 px column (14%). The right column is empty. Of the two-column text area of page 6, **about 93% is blank** (about 1.86 of 2 columns, roughly 0.93 of a page). Pages 1–5 are full to within 1–3% of the bottom margin. Seven lines have spilled; the paper is a 5-page paper plus a page of nothing.

### What the reader would most want in that space, using material the paper already has

In order of value:
1. **Definitions and design** (about 6 lines): the glossary sentences in §1a, and a short "What was fixed in advance" statement for batch C (§2c).
2. **A small design table** (about 6 lines): batches (scenario batch, A, B, C) × n, predictor (earlier GRU / leak-free GRU), purpose (exploratory / confirmatory), host load known (no record / loaded / quiet). All facts are in the paper (A has no host record, B ran with background load, C quiet at mean busy 0.14–0.27; those last are journal-only).
3. **Journal-only text that answers a reviewer's first questions**, restore these:
   - the "Three choices separate this decision factor from a plain forecast" paragraph (§III.B extended): it states why the envelope, why raise-only, why the 90 s hold. The reader currently gets the rule without the reason.
   - "Run conditioning" (§V extended): the delay cycle 60/90/120/75/45 s per pair is the actual counterbalancing; the gates are listed; it is how the reader learns the paired design is sound.
   - Threats: "one 20-minute window of one trace", "provisioning delay is simulated by a timer", "one parameter set for Algorithm 2" (§VII extended).
   - The sentence on the earlier five-pair batch and why it is not evidence (§VI.B extended).
   - "we did not record which backend served the slowest requests" (§VI.C extended). It makes the explanation in VII an explicit hypothesis rather than a conclusion.
   - Figure for Table IV (the boxplot of the runs behind it, journal-only, `fig:boxplot`). Tell the reader the run-to-run spread behind "± sd" with five runs. I have not seen this figure rendered; it exists in the source.
4. A sentence on the S2 comparison (journal-only): "S2 ran on three always-warm pods on a three-CPU node, while S1 started from one one-CPU worker." Needed for fairness of the S2 cost/latency comparison.

Together this is well within 1.5 columns, with the reference list unchanged.

### Paragraphs that do and do not earn their space

**Earn their space:** the intro paragraphs 2–3 (hybrid and its two interacting decisions); the research-question paragraph; Table V; §VI.B and VI.C; §VII (Discussion and Threats); the Table II comparison (the honest negative result).

**Do not earn their space, or repeat:**
- **ElaX is described three times**: intro paragraph 3 (5 lines), the "ElaX." paragraph in related work (5 lines), and Table I (13 lines). The related-work paragraph restates the table in prose. Cut the paragraph and keep a one-line pointer to Table I.
- **"Applied only when it asks for more replicas" appears six times**: abstract, contribution 2, Table I, §III.B text, Algorithm 2 lines 5–7, Fig. 1. **"The routing weight does not depend on the forecast"** appears five times: abstract, contribution 2, related work, §III.A last line, Fig. 1 caption. Keep it in §III.B and once in the abstract.
- **The intro's results paragraph and the roadmap sentence** (4–5 lines): restate the abstract. A six-page paper does not need the roadmap. Replace with the limit sentence (see 2a).
- **The pacing term** (Alg. 1 line 5; the §III.A sentences on p_burn, "budget", "threshold"; the second half of the Alg. 1 comment column). The text states it never activates in any 20-minute run. It costs an algorithm row, 4 lines and 3 undefined terms. Remove it from Algorithm 1 and Eq. (1) and add one clause in §V: "A pacing term in the router never fired and was omitted." (Check this matches the experiments before cutting.) The removal also fixes the Eq. (1) mismatch.
- **Related work**: two dense paragraphs name 14 systems with one clause each. Surveys [7], [8], and benchmark [15] ("when deep RL beats calibrated baselines at all") contribute nothing to positioning. MArk [19] and Spock [20] are the closest work (forecast-sized VMs with serverless burst absorption) and get the same one clause as the rest. The paragraph never says how the proposed router differs from MArk/Spock beyond "moves only the load above the capacity of ready pods". Give MArk, Spock and LA-IMR three lines; cite the rest in one list sentence.
- **Accuracy and protocol (§IV)**: FastAPI latency (4.0 ms, p95 5.1 ms; relevant only as "negligible against a 15 s cycle"), the TPE/Optuna sentence, and the 12-variant claim.
- **Fig. 2** repeats the Table V CI column. The axis is set by batch A's interval ([−597, +1,058]) so batch C's interval, the one that matters, is a short bar near zero. Either drop the figure and keep the table (saves about 12 lines), or keep both and let the figure carry something the table cannot (the per-pair differences). Do not draw new data; note that per-pair differences already exist in the runs.
- **Algorithm 2** has two redundant tests (see 3b) and carries every constant that Table I and §III.B also state.

### Order

- **Table III (scenarios) appears on p.4, but S1–S4 are used from p.1.** Move it to the start of §III or §V, or into the intro.
- **Table I appears on p.2, before the algorithms it compares (p.3).** Fine as an orientation but its "Decision factor v" row cannot be read until Eq. (2).
- **§VI.A reports a result from a different forecaster before §VI.B.** Fine, but §VI.A's own correction ("so its S4 row does not measure the forecaster") belongs *in front of* the S4 numbers, not after.
- **"Threats to validity" is the last paragraph of §VII and spills across the p.5 column break.** Give it a run-in head of its own (it is) and move the power sentence up.

---

## 5. Figures and tables as printed

- **Fig. 1 (p.2).** Full-width, about a quarter of the page. Box labels are 7 pt and edge labels 6.5 pt; at print size the subscripts of w_k8s and w_sls are about 4–5 pt and are the only labels that identify the two HAProxy outputs. The label "pending pod → node, 45–120 s" overflows the "Node autoscaler" box: "pending" starts to the left of the box border and the text runs through the border. The "load x, p99" arrow runs from Prometheus over the daemon box, its label sits above the figure, and the "load x, p99" box and arrow head into the daemon dashed box edge, not into Algorithm 1 or 2. It is not obvious which algorithm consumes the load. The caption stands alone, but "hybrid-predictive scenario (S4)" is not defined before p.4, and "û" is undefined there. Fix: define S4 in the caption; widen the node-autoscaler box; enlarge the w labels to at least 6.5 pt; add arrows from Prometheus to each algorithm; state the three-pod floor in the Kubernetes box.
- **Table I (p.2).** Narrow justified columns produce large gaps ("not      reimplemented;" ; "largest   upper-envelope"). The "Decision factor" cell wraps to six lines in the right column. Left-align the text columns. Terms used: "Refresh: forecast and reservation hourly; model daily" is cryptic ("model daily" = retrained daily). "Dimension" needs a gloss ("scaling dimension").
- **Algorithms 1 and 2 (p.3).** 8 pt, legible. Algorithm 1 right-aligned comments sit in a ragged column ("▷ burst share, capped" and "▷ SLO pacing term" are on different lines from their code and offset). Algorithm 2 line 6 holds `hold (T_p, t + 90 s)`, whose semantics (the hold is stored, refreshed on each new forecast?) are not described. Line 10 breaks onto a second row. Neither algorithm's caption says what it returns.
- **Table II (p.3).** "MAE" is not defined for the Skill column's neighbour; the "±" is across three seeds and the caption does not say so; "Skill" is blank for linear autoregression, linear trend and seasonal naive (see 2b). Rows lack "n seeds" for the deterministic baselines. Caption: "Forecast error on the held-out ClarkNet test region, 9-step horizon, in RPS of the replayed (×33) series." The test region's length (samples) is missing; the reader cannot judge the 22% and 0.216.
- **Table III (p.4).** Fine. The "Forecast: no/yes" column is understandable only after reading §III.B. Add "(Alg. 2 only)" or rename "GRU forecast".
- **Table IV (p.4).** Caption is long (6 lines) and carries a footnote and four definitions; it does stand alone except for "weight-time product" and "SLO viol." as a count with no denominator. The S4 row is flagged with a superscript "a", but the flag is easy to miss and the conclusion that the row "does not measure the forecaster" sits in the body. Put a visible rule or a row label ("S4, earlier GRU") instead. "Pod-s" is cryptic as a column header; "Pod-seconds (K8s)" fits.
- **Table V (p.4).** Columns "n", "d" and "Wins" need the body or caption: n = pairs, d = paired Cohen's d (stated in the caption), Wins = pairs S4 won (stated). "S3" and "S4" columns are mean p99 (stated). Header "S4 − S3 [95% CI]" needs "(ms)". The pooled row's p comes from sampling (caption says so) but is also called descriptive (body). Batch letters A/B/C do not say which was pre-specified; add a column "Role" or mark C with a dagger and "pre-specified".
- **Fig. 2 (p.4).** Axis labels 6.5 pt. Row labels 7 pt. Marker sizes (0.07 vs 0.11 cm) are tiny; batch C's interval is about 2 mm wide at print size. The vertical zero line is dashed grey and thin. The caption does not say that left means S4 faster (it is on the axis label). The caption says "for the 25 pairs pooled" but the body calls the pooled row "descriptive". Figure and table share all numbers; see §4.

---

## 6. Style tells

- **Uniform sentence rhythm.** Prose is mostly 14–22 word declaratives joined by "and" or "so", often in a "X does A, and Y does B" frame, with no variation in length. Examples (p.1): "A Kubernetes deployment scales on what it has already observed. The Horizontal Pod Autoscaler (HPA) compares CPU use with a target and adds pods after the target is crossed [1]." "The decisions interact." A one-sentence paragraph-ending claim after a list, repeated at the end of nearly every paragraph.
- **"Only" as a tic.** "only" occurs about 14 times in the prose: "uses it only when" (abstract, contribution 2, §III.B), "sends to Knative only the load" (abstract), "depends only on" (abstract), "enters only the replica decision" (related work), "changes it only through the pods" (§III.A), "Only the paired batches below do" (§VI.A), "only from 4.0% to 3.2%" (§VI.C), "only effects larger than" (§VII), "Only Algorithm 2 uses the GRU forecast, and only in S4" (Fig. 1). Keep the three that carry a claim (abstract, §III.B, §VII) and delete the rest.
- **"Therefore", "consistent with", "we did not test".** "therefore" ×4 (§III.A, §III.B, §VII), "consistent with" ×2 (§VI.C, §VII opening), "we did not test it/this/them" ×3 in the conference build (§VII) and again in the journal text. The refrain is honest, but its form is formulaic. Group them in one "What we did not test" sentence list.
- **Stacked hedges.** p.5 §VII: "Our results are consistent with the following explanation. ... We did not test this directly ... A forecast is more likely to help where ... The paired batches tested none of these cases." Four hedging moves in six lines, each correct, together reading as defensive. One sentence of explanation, one of "untested", then the list of conditions.
- **Section title / body conflict.** §VI.C "Why the forecast did not help" with a body that says "is consistent with"; the §VII "Discussion" repeats it. The same explanation is offered twice with different confidence.
- **Hyphen-compound stacks.** "capacity-aware traffic distribution", "ElaX-derived replica scaling with a forecast", "forecast-then-reserve structure", "forecast-driven scaling decision", "slack-based online controller", "always-warm", "leak-free chronological protocol". Pairs of hyphenated modifiers read as generated.
- **Dashes and semicolons.** Prose has no em dashes and almost no semicolons, which is good. Semicolons appear in Table I ("used only if its target exceeds R(x_obs); raised target held 90 s") and Fig. 1 ("R(v) = ⌈αv + β⌉; S4 raises the target to R(max_k û)"). Replace with sentences or separate rows.
- **Passive where the actor matters.** "Hyperparameters and the epoch budget are selected with the Tree-structured Parzen Estimator", "The model is then refit", "A run counts only if it passes validity gates", "Costs are projected onto AWS prices", "The series is split in time order", "The projection charges nodes". Who set the 90 s hold, the 0.75 factor, the 140 ms guard, the 38-sample gap? A reviewer reads "chosen by the authors without tuning" and "tuned on batch A" very differently. State which parameters were tuned on which data. Good active sentences exist ("We use a one-sided exact paired permutation test").
- **Abstract as a list of seven results in 13 sentences.** Every sentence carries a number or a parameter. It reads as a data dump, not a story.
- **Generic phrasing.** "Surveys of serverless resource management describe the lag between a surge and the capacity that answers it" (the lag is said three ways), "asks when deep reinforcement learning beats calibrated baselines at all", "which lets us measure the effect of the forecast alone". "Holistic" is not used, but "captures", "integrated control architecture" and "coordinates" in contribution 1 are generic ("An integrated control architecture that coordinates Kubernetes replica scaling ... and capacity-aware traffic distribution ... between Kubernetes and Knative serverless services under a 200 ms p99 service-level objective (SLO)") — one 43-word sentence in which the verb "coordinates" does no work.

---

## Ten changes that would most improve a reviewer's score, ranked

1. **Put the research question, the null result with its baseline and its limit in the abstract.** "Adding a 135 s GRU forecast to a reactive hybrid changed mean p99 by −13.6 ms (95% CI [−63.5, +35.6]) at 45% more pod-seconds; ten pairs detect only effects above about 72 ms." Move the 72 ms power fact out of §VII. (Sections 2a, 2c.)
2. **Fix the abstract's four-scenario sentence.** Say pod-seconds count Kubernetes pods only, the projected cost does not resolve the difference, S4 in that batch is not the leak-free GRU, and S3 had worse latency than S1. Today it overstates the hybrid's value. (2b.)
3. **State exactly what was pre-specified for batch C and give the batches names and roles** (confirmatory vs exploratory, order, n, host load); add the sentence on the earlier excluded batch and on discarded runs. (2c, 3a.)
4. **Define every first-read term at first use**: p99, SLO, HPA, KPA, Knative, pod, pod-seconds, upper envelope, skill, persistence, leak-free, embargo, counterbalanced, validity gates, weight-time product, CPU-busy, decision factor. Remove "replica-seconds" and "Pod-s". (1a.)
5. **Rename the data "scaler" in §IV, and remove the symbol collisions** (batch C vs capacity C, n pods vs n pairs, r three ways, "desired replicas r"). (1b, 3b.)
6. **Recast the contributions as artifact plus findings**: the null result and the "GRU does not beat linear AR" finding become contributions; retitle the paper to a question. (2a.)
7. **Remove the dead pacing term** from Algorithm 1, Eq. (1) and §III.A; this also resolves the Eq. (1) vs Algorithm 1 mismatch. Drop the redundant conditions in Algorithm 2 lines 8 and 10 and fix its input line. (3b, 4.)
8. **Cut duplicate text** (ElaX three times; "applied only when" six times; roadmap sentence; weak related-work citations; Fig. 2 or the pooled p/d) and **use the freed space plus page 6** for the glossary, a design table and the journal-only paragraphs (three design choices, run conditioning and the delay cycle, single-window / timer-simulated delay / one parameter set, earlier-batch disclosure). (4.)
9. **Make the figures and tables stand alone**: fill the blank skill cells in Table II (derived); say "±" is over seeds; give Table IV a denominator and a visible earlier-GRU row label; enlarge Fig. 1's w labels and fix the node-autoscaler box overflow and missing arrows; left-align Table I; decide between Fig. 2 and Table V. (5.)
10. **Reduce the stylistic tells**: delete most of the 14 "only"s; collapse the "we did not test" refrain into one sentence; replace "Why the forecast did not help" with "A possible reason"; name the actor for every tuned constant; break the uniform sentence rhythm in the intro and abstract. (6.)

---

## Verdict

**Targeted edit pass, not a rewrite.** The structure is sound: motivation, a precise research question, architecture, forecaster, setup, results, a discussion that says what was and was not tested. The arithmetic recomputes everywhere I checked, and the honesty about the null result is real and is the paper's strength. The damage is concentrated in the first page (the abstract and contribution list undersell the actual finding and oversell the hybrid-vs-HPA comparison), in undefined terms and name drift, in one mis-described mechanism (the dead pacing term, the data "scaler"), and in a half-empty sixth page that could hold exactly the material a reviewer looks for (what was pre-specified, how the pairs were balanced, the simulated delay, the earlier excluded batch). All of that can be done by reordering, defining, cutting duplicates and restoring paragraphs the paper already contains. A full rewrite would risk losing the one thing the paper does well, so I would not recommend one. The abstract and the contribution list should be rewritten from scratch inside that pass.
