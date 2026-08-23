# Candidate analysis figures — definitive paired H2 bundle

Generated 2026-08-23 from real experiment data only. Every number below is either printed by
`make_candidates.py` (in this directory, run with `uv run python`) or directly readable in the
named source file. Nothing is estimated or filled in.

Bundle: `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5/` (definitive, 5 × S3
`s3-hybrid-reactive` + 5 × S4 `s4-hybrid-predictive`, ClarkNet replay, 1260 s per run).
HPO context: `results/experiments/tuning/gru_hpo_2026-07-09_224736/study.json`.

Method note (timestamps): `daemon.log` timestamps are box-local (UTC+7); `prometheus_export.json`
and `events.jsonl` are epoch/UTC. The script derives the local→UTC offset per run from the
`daemon_started` event and asserts it is a whole hour before use. x-axes are seconds from
`t_start` of each run's `result.json`. A guard asserts every log-derived event falls inside
[−300 s, +1800 s]; an earlier draft of this script had a −7 h double-shift bug that this check
now makes impossible to reintroduce silently.

---

## Figure 1 — `fig_cand1_routing_weights.png` (routing-weight timeline)

**Sources (exact):**
- `<run>/prometheus/prometheus_export.json` → series `daemon_weight_k3s`, `daemon_weight_knative`
  (85 samples each, `[unix_ts, weight%]`).
- `<run>/daemon.log` → `controller_decision_v3` lines → `action=` (REACTIVE / PREDICTIVE markers).
- `<run>/result.json` → `t_start` (x-origin).
- Runs shown: `s3-hybrid-reactive_run1` (top), `s4-hybrid-predictive_run1` (bottom).

**What it shows:** HAProxy routing weights over one full replay (0–1259 s), stacked S3/S4.
Decision moments overlaid: orange triangles = REACTIVE burst-routing decisions at y≈104;
purple dashed verticals = PREDICTIVE decisions.

**Numbers found:**

| | S3 run 1 | S4 run 1 |
|---|---|---|
| weight samples | 85 | 85 |
| k3s weight range | 66–100 % | 79–100 % |
| Knative weight range | 0–34 % | 0–21 % |
| REACTIVE decisions | 11 | 4 |
| PREDICTIVE decisions | 0 | 4 (at 455, 546, 561, 954 s) |
| `Weights updated` log lines | 28 | 21 |

**Thesis fit:** **Book-ready with light polish.** It makes the mechanism visible in one glance:
S3 repeatedly dumps burst overflow to Knative (11 REACTIVE bursts, up to 34 %) then pulls back,
while S4 pre-routes less (max 21 %) and replaces most late-run reactivity with 4 predictive
shifts. Caveats to state in the caption: single representative pair (run 1 of each); weights
are 15 s control-loop samples, so sub-interval changes are not resolved.

---

## Figure 2 — `fig_cand2_gru_pred_vs_actual.png` (GRU forecast vs observed load)

**Sources (exact):** all from `s4-hybrid-predictive_run1/`:
- `daemon.log` → `GRU prediction received ... predicted=N` (56 lines, 2026-07-14 02:08:08 →
  02:22:01 local; t ≈ 424–1257 s — forecasts exist only after model warm-up): the predictor's
  point forecast handed to the scaling loop.
- `daemon.log` → `algorithm2_decision ... observed_load=` (86 per-cycle values, 0.0–155.5 RPS):
  dense observed series.
- `daemon.log` → `controller_decision_v3 ... current_load=` (20 values, 42.4–160.2 RPS):
  routing-controller observed load (plotted as ×; sparse because the controller only logs when
  it re-decides weights).
- `result.json` → `predictive_count: 4` (matches the 4 marked PREDICTIVE decisions),
  `gru_predictions_used: 55`, `t_start`.

k6 was **not** usable for the observed series: `k6/*.json` is summary-aggregate only
(e.g. `http_reqs.count = 87840`, `rate = 73.19`) with no per-interval RPS series.

**What it shows:** observed load vs GRU point forecasts over the run; 4 PREDICTIVE decision
moments marked. Forecast range 36–143 RPS vs observed 0–160 RPS.

**Numbers found:** forecasts track the observed line well on gradual phases; the largest gap is
at the load peak (~560–590 s): observed ≈ 155–160 RPS vs forecast ≈ 125–140 RPS, i.e. the GRU
under-forecasts the sharpest rise by roughly 15–30 RPS. 56 forecasts received, 55 used
(`gru_predictions_used`), 4 acted on predictively.

**Thesis fit:** **Needs work before the book.** Real and honest, but (a) `predicted=N` is a
horizon point forecast (`required_steps` 3–5 × 15 s ≈ 45–75 s ahead), so the overlay alignment
is approximate — the caption must say this or reviewers will read vertical gaps as pure error;
(b) it is n = 1 run, so it is a mechanism illustration, not evidence; (c) the first observed
cycle (21.2 vs controller 42.4 RPS at 02:01:20) is a warm-up window artifact worth a footnote.
Best used as a qualitative companion to the H2 statistics, explicitly labelled as one
representative run.

---

## Analysis 3 — Spearman correlations across the 10 definitive runs

**Source:** `result.json` of all 10 runs; fields listed below. Computed with
`scipy.stats.spearmanr` (two-sided). Full machine-readable output: `spearman_correlations.csv`.

**Degenerate fields (excluded, zero variance):** `error_rate = 0.0` in all 10 runs.
`throughput_rps` varies only in the 5th decimal (73.19279–73.19313) — it is replay-driven and
effectively constant; its correlations are numeric noise and are not interpreted.

**Table (n = 10):** only |rho| ≥ 0.55 or p < 0.10 shown here; full table in the CSV.

| pair | rho | p |
|---|---|---|
| predictive_count ~ desired_replicas_final | +0.926 | 0.0001 |
| scale_out_count ~ desired_replicas_final | −0.918 | 0.0002 |
| scale_out_count ~ predictive_count | −0.900 | 0.0004 |
| k8s_replica_seconds ~ scale_out_count | −0.882 | 0.0007 |
| time_in_serverless_pct ~ scale_out_count | +0.874 | 0.0009 |
| knative_active_seconds ~ scale_out_count | +0.874 | 0.0009 |
| k8s_replica_seconds ~ time_in_serverless_pct | −0.842 | 0.0022 |
| k8s_replica_seconds ~ desired_replicas_final | +0.840 | 0.0023 |
| k8s_replica_seconds ~ predictive_count | +0.773 | 0.0088 |
| p99_latency_ms ~ desired_replicas_final | −0.750 | 0.0124 |
| p99_latency_ms ~ predictive_count | −0.724 | 0.0180 |
| p99_latency_ms ~ k8s_replica_seconds | −0.620 | 0.0558 |
| p99_latency_ms ~ scale_out_count | +0.618 | 0.0566 |
| time_in_serverless_pct ~ predictive_count | −0.597 | 0.0682 |

Identity pairs (rho = 1.000 by construction, not findings): `p99_latency_ms ~ slo_violations_k6`
and `time_in_serverless_pct ~ knative_active_seconds` (same quantity in two units).
Everything else (all `throughput_rps` rows, serverless ↔ p99 ρ=+0.306 p=0.39, etc.) is noise at
n = 10.

**Plain-language read:**
- **Strong and meaningful:** more predictive activity goes with fewer scale-outs, more
  replica-seconds held, and lower p99 / fewer SLO violations. That is exactly the H2 story
  (S4 pre-provisions capacity instead of reacting). Scenario medians: S3 p99 192.2 ms / 813 SLO
  violations / 10 scale-outs vs S4 104.9 ms / 18 / 4.
- **The confound to state openly:** `predictive_count`, `desired_replicas_final`, and much of
  `k8s_replica_seconds` separate S4 from S3 almost perfectly, so these correlations largely
  re-encode the between-scenario difference on 10 points. They are a consistency check on the
  paired analysis, not independent evidence. The thesis should keep the paired permutation test
  as the actual H2 evidence and use this table as descriptive support only.
- **Noise:** anything involving `throughput_rps` (fixed by the replay) or with p > 0.10.

**Thesis fit:** **Data-sufficient as a table, not a figure.** A correlation heatmap at n = 10
would over-dress it; the selected rows above (or the CSV) belong in the chapter-4 discussion of
why S4 wins, with the confound sentence verbatim.

---

## GRU HPO context (`gru_hpo_2026-07-09_224736/study.json`)

30 Optuna trials; best trial 25: `hidden_size=128`, `num_layers=1`,
`learning_rate=3.799e-4`, `sequence_length=30`, `dropout=0.1037`, `best_rmse_pct=4.745`.
**Honesty flag:** `data_source` in the study file is `"synthetic"` — the HPO search ran on
synthetic data, not on the ClarkNet trace. If the thesis cites the tuned hyperparameters, it
should say the search space was screened on synthetic series and validated later on the replay
bundle, or drop the 4.745 % RMSE figure from book claims.

## Gaps and non-plots (things checked and deliberately not plotted)

- `prometheus_export.json` per-run series `prom_p99_ms`, `prom_rps`, `cpu_usage_cores`,
  `memory_usage_bytes`, `node_count_schedulable`, `pods_pending_count` are **empty lists** in
  these runs — no p99/RPS timeline from Prometheus exists in this bundle.
- k6 per-interval RPS series does not exist (summary aggregates only) — hence daemon-side
  observed load in Figure 2.
- No per-request serverless-vs-k8s routing split over time is exported, so a "share of traffic
  on Knative over time" figure is not derivable from this bundle (weights are the closest proxy).
