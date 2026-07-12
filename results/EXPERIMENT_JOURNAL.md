# Experiment Journal

> **This file is generated.** Do not hand-edit.
>
> Canonical sources:
> - **Governance:** `results/evidence/registry-events.jsonl`
> - **Execution:** per-run `events.jsonl` inside each bundle
> - **Registry:** `results/evidence/registry.yaml`
> - **Query cache:** `results/evidence/catalog.duckdb` (rebuilt, not canonical)

**Latest audit:** 2026-07-12T05:30:01.899091+00:00

## Summary

- **Total bundles:** 123
- **By role:** diagnostic=79, final=5, intermediate=39
- **By status:** archived=9, current=51, invalidated=63

## Bundles

| Date | ID | Role | Valid/Total | Treatment | Claims | Path |
|------|----|------|------------|-----------|--------|------|
| 2026-07-11 | `experiments.2026-07-11-scaling-fix-n1` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-11_scaling_fix_n1` |
| 2026-07-11 | `experiments.2026-07-11-paired-h2` | diagnostic | 10/10 | 256/257 (✗) | — | `experiments/phase-b/2026-07-11_paired-h2` |
| 2026-07-11 | `experiments.2026-07-11-nolimit-n1-v2` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-11_nolimit_n1_v2` |
| 2026-07-11 | `experiments.2026-07-11-nolimit-n1` | diagnostic | 2/4 | — | — | `experiments/phase-b/2026-07-11_nolimit_n1` |
| 2026-07-11 | `experiments.2026-07-11-fair-tuned-n1` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-11_fair_tuned_n1` |
| 2026-07-10 | `experiments.surrogate-2026-07-10-125705` | diagnostic | 0/0 | — | — | `experiments/tuning/surrogate_2026-07-10_125705` |
| 2026-07-10 | `experiments.surrogate-2026-07-10-125615` | diagnostic | 0/0 | — | — | `experiments/tuning/surrogate_2026-07-10_125615` |
| 2026-07-10 | `experiments.2026-07-10-tuned-holdout` | intermediate | 5/6 | 402/402 (✓) | — | `experiments/phase-b/2026-07-10_tuned_holdout` |
| 2026-07-10 | `experiments.2026-07-10-gp-holdout-n5` | intermediate | 5/6 | 400/400 (✓) | — | `experiments/phase-b/2026-07-10_gp_holdout_n5` |
| 2026-07-10 | `experiments.2026-07-10-cpulimit-n1` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-10_cpulimit_n1` |
| 2026-07-09 | `experiments.gru-hpo-2026-07-09-224736` | diagnostic | 0/0 | — | — | `experiments/tuning/gru_hpo_2026-07-09_224736` |
| 2026-07-09 | `experiments.gru-hpo-2026-07-09-221557` | diagnostic | 0/0 | — | — | `experiments/tuning/gru_hpo_2026-07-09_221557` |
| 2026-07-09 | `experiments.gru-hpo-2026-07-09-212419` | diagnostic | 0/0 | — | — | `experiments/tuning/gru_hpo_2026-07-09_212419` |
| 2026-07-09 | `experiments.gru-hpo-2026-07-09-191537` | diagnostic | 0/0 | — | — | `experiments/tuning/gru_hpo_2026-07-09_191537` |
| 2026-07-09 | `experiments.gru-hpo-2026-07-09-191315` | diagnostic | 0/0 | — | — | `experiments/tuning/gru_hpo_2026-07-09_191315` |
| 2026-07-09 | `experiments.gru-hpo-2026-07-09-191123` | diagnostic | 0/0 | — | — | `experiments/tuning/gru_hpo_2026-07-09_191123` |
| 2026-07-08 | `experiments.2026-07-08-s2-pipefix` | intermediate | 1/2 | — | — | `experiments/phase-b/2026-07-08_s2-pipefix` |
| 2026-07-08 | `experiments.2026-07-08-pipefix` | intermediate | 3/4 | 0/79 (✗) | — | `experiments/phase-b/2026-07-08_pipefix` |
| 2026-07-08 | `experiments.2026-07-08-fib33-v2` | intermediate | 2/3 | 80/80 (✓) | — | `experiments/phase-b/2026-07-08_fib33_v2` |
| 2026-07-08 | `experiments.2026-07-08-fib33-proactive` | final | 10/11 | 402/402 (✓) | — | `experiments/phase-b/2026-07-08_fib33_proactive` |
| 2026-07-08 | `experiments.2026-07-08-fib33-n5` | final | 20/21 | 401/401 (✓) | — | `experiments/phase-b/2026-07-08_fib33_n5` |
| 2026-07-08 | `experiments.2026-07-08-fib33` | intermediate | 4/5 | 0/79 (✗) | — | `experiments/phase-b/2026-07-08_fib33` |
| 2026-07-07 | `experiments.2026-07-07-smoke` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_smoke` |
| 2026-07-07 | `experiments.2026-07-07-s3-s4-60min` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s3-s4-60min` |
| 2026-07-07 | `experiments.2026-07-07-s3-consistent` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s3-consistent` |
| 2026-07-07 | `experiments.2026-07-07-s2-works` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s2-works` |
| 2026-07-07 | `experiments.2026-07-07-s2-min7` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s2-min7` |
| 2026-07-07 | `experiments.2026-07-07-s2-min5` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s2-min5` |
| 2026-07-07 | `experiments.2026-07-07-s2-min-scale-3` | intermediate | 1/2 | — | — | `experiments/phase-b/2026-07-07_s2-min-scale-3` |
| 2026-07-07 | `experiments.2026-07-07-s2-hpa-quick` | diagnostic | 1/2 | — | — | `experiments/phase-b/2026-07-07_s2-hpa-quick` |
| 2026-07-07 | `experiments.2026-07-07-s2-final2` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s2-final2` |
| 2026-07-07 | `experiments.2026-07-07-s2-final` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s2-final` |
| 2026-07-07 | `experiments.2026-07-07-s2-cli-final` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s2-cli-final` |
| 2026-07-07 | `experiments.2026-07-07-s2-clean` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s2-clean` |
| 2026-07-07 | `experiments.2026-07-07-s1-s4-fixed` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-07_s1-s4-fixed` |
| 2026-07-07 | `experiments.2026-07-07-s1-s4-fib30` | diagnostic | 2/4 | — | — | `experiments/phase-b/2026-07-07_s1-s4-fib30` |
| 2026-07-07 | `experiments.2026-07-07-s1-s3-s4` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s1-s3-s4` |
| 2026-07-07 | `experiments.2026-07-07-s1-only` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_s1-only` |
| 2026-07-07 | `experiments.2026-07-07-no-cpu-limits` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_no-cpu-limits` |
| 2026-07-07 | `experiments.2026-07-07-kpa-fix` | diagnostic | 2/4 | — | — | `experiments/phase-b/2026-07-07_kpa-fix` |
| 2026-07-07 | `experiments.2026-07-07-final-nolimits` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-07_final-nolimits` |
| 2026-07-06 | `experiments.2026-07-06-sanity-v2` | diagnostic | 2/4 | — | — | `experiments/phase-b/2026-07-06_sanity-v2` |
| 2026-07-06 | `experiments.2026-07-06-sanity-check` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-06_sanity-check` |
| 2026-07-06 | `experiments.2026-07-06-s1-s4-fair-calibrated` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-06_s1-s4-fair-calibrated` |
| 2026-07-05 | `experiments.2026-07-05-s2-metrics-fixed` | intermediate | 1/2 | — | — | `experiments/phase-b/2026-07-05_s2-metrics-fixed` |
| 2026-07-05 | `experiments.2026-07-05-s2-io-bound` | intermediate | 1/2 | — | — | `experiments/phase-b/2026-07-05_s2-io-bound` |
| 2026-07-05 | `experiments.2026-07-05-s2-final-cost` | intermediate | 1/2 | — | — | `experiments/phase-b/2026-07-05_s2-final-cost` |
| 2026-07-05 | `experiments.2026-07-05-s2-cpu-limit` | intermediate | 1/2 | — | — | `experiments/phase-b/2026-07-05_s2-cpu-limit` |
| 2026-07-05 | `experiments.2026-07-05-s1-s4-io-fixed` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_s1-s4-io-fixed` |
| 2026-07-05 | `experiments.2026-07-05-s1-s4-io-bound` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_s1-s4-io-bound` |
| 2026-07-05 | `experiments.2026-07-05-n1-validation` | intermediate | 2/3 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_n1-validation` |
| 2026-07-05 | `experiments.2026-07-05-n1-full` | intermediate | 4/5 | 81/81 (✓) | — | `experiments/phase-b/2026-07-05_n1-full` |
| 2026-07-05 | `experiments.2026-07-05-n1-fib33` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_n1-fib33` |
| 2026-07-05 | `experiments.2026-07-05-highload-n1` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_highload-n1` |
| 2026-07-05 | `experiments.2026-07-05-high-load-quick` | diagnostic | 2/3 | — | — | `experiments/phase-b/2026-07-05_high-load-quick` |
| 2026-07-05 | `experiments.2026-07-05-final-all-fixes` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_final-all-fixes` |
| 2026-07-05 | `experiments.2026-07-05-clarknet-replay` | intermediate | 4/6 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_clarknet-replay` |
| 2026-07-05 | `experiments.2026-07-05-clarknet-n1` | intermediate | 4/5 | 80/80 (✓) | — | `experiments/phase-b/2026-07-05_clarknet-n1` |
| 2026-07-05 | `experiments.2026-07-05-clarknet-cpu-limit` | intermediate | 4/5 | 0/0 (✗) | — | `experiments/phase-b/2026-07-05_clarknet-cpu-limit` |
| 2026-07-05 | `experiments.2026-07-05-calibration-test` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-07-05_calibration-test` |
| 2026-07-04 | `experiments.2026-07-04-v3-tuned-sanity` | diagnostic | 1/2 | — | — | `experiments/phase-b/2026-07-04_v3-tuned-sanity` |
| 2026-07-04 | `experiments.2026-07-04-v3-tuned-quick2` | diagnostic | 1/1 | 10/10 (✓) | — | `experiments/phase-b/2026-07-04_v3-tuned-quick2` |
| 2026-07-04 | `experiments.2026-07-04-v3-tuned-quick` | diagnostic | 0/1 | — | — | `experiments/phase-b/2026-07-04_v3-tuned-quick` |
| 2026-07-04 | `experiments.2026-07-04-v3-tuned-full` | intermediate | 2/2 | 80/80 (✓) | — | `experiments/phase-b/2026-07-04_v3-tuned-full` |
| 2026-07-04 | `experiments.2026-07-04-v3-soft-reset` | intermediate | 0/1 | 9/9 (✓) | — | `experiments/phase-b/2026-07-04_v3-soft-reset` |
| 2026-07-04 | `experiments.2026-07-04-v3-quick3` | diagnostic | 1/1 | 8/8 (✓) | — | `experiments/phase-b/2026-07-04_v3-quick3` |
| 2026-07-04 | `experiments.2026-07-04-v3-probe-quick` | diagnostic | 0/1 | 8/8 (✓) | — | `experiments/phase-b/2026-07-04_v3-probe-quick` |
| 2026-07-04 | `experiments.2026-07-04-v3-probe-full` | diagnostic | 1/2 | 80/80 (✓) | — | `experiments/phase-b/2026-07-04_v3-probe-full` |
| 2026-07-04 | `experiments.2026-07-04-v3-full-soft-reset` | intermediate | 1/2 | 79/79 (✓) | — | `experiments/phase-b/2026-07-04_v3-full-soft-reset` |
| 2026-07-04 | `experiments.2026-07-04-v3-fixed-sanity` | diagnostic | 1/1 | 72/72 (✓) | — | `experiments/phase-b/2026-07-04_v3-fixed-sanity` |
| 2026-07-04 | `experiments.2026-07-04-v3-capacity-sanity` | diagnostic | 2/2 | 79/79 (✓) | — | `experiments/phase-b/2026-07-04_v3-capacity-sanity` |
| 2026-07-04 | `experiments.2026-07-04-v3-300m-quick` | diagnostic | 0/1 | 10/10 (✓) | — | `experiments/phase-b/2026-07-04_v3-300m-quick` |
| 2026-07-04 | `experiments.2026-07-04-v2-controller-sanity` | diagnostic | 2/2 | 80/80 (✓) | — | `experiments/phase-b/2026-07-04_v2-controller-sanity` |
| 2026-07-04 | `experiments.2026-07-04-smoke2` | diagnostic | 1/2 | 71/71 (✓) | — | `experiments/phase-b/2026-07-04_smoke2` |
| 2026-07-04 | `experiments.2026-07-04-isolated-smoke` | diagnostic | 1/2 | 1/1 (✓) | — | `experiments/phase-b/2026-07-04_isolated-smoke` |
| 2026-07-04 | `experiments.2026-07-04-all4-scenarios` | intermediate | 4/5 | 71/71 (✓) | — | `experiments/phase-b/2026-07-04_all4_scenarios` |
| 2026-07-03 | `experiments.2026-07-03-phase-b-v3-n5` | diagnostic | 12/15 | 322/322 (✓) | — | `experiments/phase-b/2026-07-03_phase-b-v3-n5` |
| 2026-02-25 | `experiments.2026-02-25-s3s4-post-weight-commit-fix` | intermediate | 2/2 | 81/81 (✓) | — | `experiments/phase-b/2026-02-25_s3s4-post-weight-commit-fix` |
| 2026-02-25 | `experiments.2026-02-25-s3s4-post-predictive-reachability` | intermediate | 2/2 | 81/81 (✓) | — | `experiments/phase-b/2026-02-25_s3s4-post-predictive-reachability` |
| 2026-02-25 | `experiments.2026-02-25-s3s4-post-p0p2-fixes` | intermediate | 2/2 | 80/80 (✓) | — | `experiments/phase-b/2026-02-25_s3s4-post-p0p2-fixes` |
| 2026-02-22 | `experiments.2026-02-22-sanity-5runs` | diagnostic | 3/4 | 82/82 (✓) | — | `experiments/phase-b/2026-02-22_sanity-5runs` |
| 2026-02-22 | `experiments.2026-02-22-full-phase-b-canonical-r5` | diagnostic | 0/1 | — | — | `experiments/phase-b/2026-02-22_full-phase-b-canonical-r5` |
| 2026-02-22 | `experiments.2026-02-22-clarknet-replay` | diagnostic | 0/0 | — | — | `experiments/phase-b/2026-02-22_clarknet-replay` |
| 2026-02-21 | `experiments.2026-02-21-clarknet-replay` | diagnostic | 0/0 | — | — | `experiments/phase-b/2026-02-21_clarknet-replay` |
| 2026-02-21 | `experiments.2026-02-21-all-scenarios-rerun-v2` | diagnostic | 3/4 | 0/0 (✗) | — | `experiments/phase-b/2026-02-21_all-scenarios-rerun-v2` |
| 2026-02-21 | `cost.2026-02-21-s2-validation-v2-unified-aws-cost` | diagnostic | 0/0 | — | — | `cost/2026-02-21_s2-validation-v2-unified-aws-cost` |
| 2026-02-21 | `cost.2026-02-21-all-scenarios-rerun-v2-unified-aws-cost` | diagnostic | 0/0 | — | — | `cost/2026-02-21_all-scenarios-rerun-v2-unified-aws-cost` |
| 2026-02-20 | `experiments.2026-02-20-s2-serverless-validation-v2` | diagnostic | 1/1 | — | — | `experiments/phase-b/2026-02-20_s2-serverless-validation-v2` |
| 2026-02-20 | `experiments.2026-02-20-s2-serverless-validation` | diagnostic | 1/1 | — | — | `experiments/phase-b/2026-02-20_s2-serverless-validation` |
| 2026-02-20 | `cost.2026-02-20-s2-validation-unified-aws-cost` | diagnostic | 0/0 | — | — | `cost/2026-02-20_s2-validation-unified-aws-cost` |
| 2026-02-19 | `experiments.2026-02-19-pilot-n2-validity-gates-rerun` | intermediate | 8/8 | 160/160 (✓) | — | `experiments/phase-b/2026-02-19_pilot-n2-validity-gates-rerun` |
| 2026-02-19 | `cost.2026-02-19-pilot-n2-unified-aws-cost` | diagnostic | 0/0 | — | — | `cost/2026-02-19_pilot-n2-unified-aws-cost` |
| 2026-02-18 | `experiments.2026-02-18-pilot-n2-validity-gates` | intermediate | 8/8 | 161/161 (✓) | — | `experiments/phase-b/2026-02-18_pilot-n2-validity-gates` |
| 2026-02-18 | `experiments.2026-02-18-fib34-validation` | diagnostic | 4/4 | 80/80 (✓) | — | `experiments/phase-b/2026-02-18_fib34-validation` |
| 2026-02-18 | `cost.2026-02-18-fib34-unified-aws-cost` | diagnostic | 0/0 | — | — | `cost/2026-02-18_fib34-unified-aws-cost` |
| 2026-02-17 | `cost.2026-02-17-three-model-cost-comparison` | diagnostic | 0/0 | — | — | `cost/2026-02-17_three-model-cost-comparison` |
| 2026-02-16 | `experiments.2026-02-16-validation-metrics-fixes` | diagnostic | 4/4 | 78/78 (✓) | — | `experiments/phase-b/2026-02-16_validation-metrics-fixes` |
| 2026-02-16 | `experiments.2026-02-16-s1-hpa-validation` | diagnostic | 1/1 | — | — | `experiments/phase-b/2026-02-16_s1-hpa-validation` |
| 2026-02-16 | `experiments.2026-02-16-clarknet-replay-full` | diagnostic | 0/2 | — | — | `experiments/phase-b/2026-02-16_clarknet-replay-full` |
| 2026-02-16 | `experiments.2026-02-16-clarknet-replay` | diagnostic | 4/4 | 0/0 (✗) | — | `experiments/phase-b/2026-02-16_clarknet-replay` |
| 2026-02-15 | `experiments.2026-02-15-recalibration` | diagnostic | 0/0 | — | — | `experiments/phase-b/2026-02-15_recalibration` |
| 2026-02-15 | `experiments.2026-02-15-mechanism-revalidation-v3` | diagnostic | 0/0 | — | — | `experiments/phase-a1/2026-02-15_mechanism-revalidation-v3` |
| 2026-02-15 | `experiments.2026-02-15-mechanism-revalidation-v2` | diagnostic | 0/0 | — | — | `experiments/phase-a1/2026-02-15_mechanism-revalidation-v2` |
| 2026-02-15 | `experiments.2026-02-15-clarknet-replay-v3a-invalid` | diagnostic | 20/20 | 400/400 (✓) | — | `experiments/phase-b/2026-02-15_clarknet-replay-v3a-invalid` |
| 2026-02-15 | `experiments.2026-02-15-clarknet-replay` | intermediate | 4/4 | 80/80 (✓) | — | `experiments/phase-b/2026-02-15_clarknet-replay` |
| 2026-02-14 | `experiments.2026-02-14-mechanism-revalidation` | diagnostic | 0/0 | — | — | `experiments/phase-a1/2026-02-14_mechanism-revalidation` |
| 2026-02-14 | `experiments.2026-02-14-clarknet-replay-ABORTED` | diagnostic | 1/2 | 0/0 (✗) | — | `experiments/phase-b/2026-02-14_clarknet-replay-ABORTED` |
| 2026-02-14 | `experiments.2026-02-14-clarknet-replay` | intermediate | 20/20 | 0/0 (✗) | — | `experiments/phase-b/2026-02-14_clarknet-replay` |
| 2026-02-14 | `experiments.2026-02-14-calibration-work-5ms` | diagnostic | 0/0 | — | — | `experiments/phase-b/2026-02-14_calibration-work-5ms` |
| 2026-02-13 | `models.2026-02-13-training-clarknet-calgary` | final | 0/0 | — | — | `models/gru/2026-02-13_training-clarknet-calgary` |
| 2026-02-13 | `experiments.2026-02-13-t7-capacity-envelope` | diagnostic | 0/0 | — | — | `experiments/validation/2026-02-13_t7-capacity-envelope` |
| 2026-02-13 | `experiments.2026-02-13-t6-gru-daemon-validation` | diagnostic | 0/0 | — | — | `experiments/validation/2026-02-13_t6-gru-daemon-validation` |
| 2026-02-13 | `experiments.2026-02-13-infrastructure-validation` | diagnostic | 0/0 | — | — | `experiments/validation/2026-02-13_infrastructure-validation` |
| 2026-02-13 | `experiments.2026-02-13-dynamic-workload` | diagnostic | 0/6 | — | — | `experiments/phase-c/2026-02-13_dynamic-workload` |
| 2026-02-12 | `experiments.2026-02-12-replicated-20runs` | diagnostic | 0/0 | — | — | `experiments/phase-b/2026-02-12_replicated-20runs` |
| 2026-02-12 | `experiments.2026-02-12-predictive-trigger` | final | 0/0 | — | — | `experiments/phase-a1/2026-02-12_predictive-trigger` |
| 2026-02-12 | `experiments.2026-02-12-calibration` | diagnostic | 0/0 | — | — | `experiments/phase-b/2026-02-12_calibration` |
| 2026-02-11 | `experiments.2026-02-11-stress-tests` | diagnostic | 0/0 | — | — | `experiments/phase-a1/2026-02-11_stress-tests` |
| 2026-02-11 | `cost.2026-02-11-proxy-analysis` | diagnostic | 0/0 | — | — | `cost/2026-02-11_proxy-analysis` |
| 2026-02-10 | `models.2026-02-10-training-synthetic` | final | 0/0 | — | — | `models/gru/2026-02-10_training-synthetic` |
| 1970-01-01 | `experiments.trials` | diagnostic | 0/0 | — | — | `experiments/tuning/trials` |
| 1970-01-01 | `experiments.surrogate-validation` | intermediate | 1/2 | 81/81 (✓) | — | `experiments/tuning/surrogate_validation` |
| 1970-01-01 | `experiments.smoke-test` | diagnostic | 0/2 | — | — | `experiments/phase-b/smoke-test` |

## Recent Governance Events (last 20)

| Timestamp | Event | Experiment | Bundle | Run |
|-----------|-------|------------|--------|-----|
| 2026-07-12T05:30:01.899091+00:00 | registry_audited | registry | /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration/results/evidence | — |
| 2026-07-12T05:29:40.179507+00:00 | registry_audited | registry | /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration/results/evidence | — |
