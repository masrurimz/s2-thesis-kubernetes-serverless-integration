# Interim status — 2026-09-13_probes-representation (partial round)

**Status as of 2026-09-13 ~01:5x UTC: 8 of 12 variants complete; 4 queued, not run.**
This is a partial round, not the whole one. The H1 baseline measurement window
opened on this box mid-batch; per the coordinator's instruction the batch was
stopped cleanly (driver cancelled, zero training processes verified) so the
latency measurements are not degraded. The four queued variants run only after
an explicit go.

Completed (record + probes.md row present):

- interval30, interval60, revin_robust, nlinear, diff_target, robust_scale,
  quantile_norm, nbeats

Queued (implementation complete and smoke-verified; no record yet):

- roll_stats, ewma, diff_input, decomp

Protocol pin carried by every record (`splits_module.sha256` in each JSON):

- 5f937edb361fbcea1a49334d92d768d409eefd1b12c563c5e708b9a1919631e3 (matches the
  coordinator's pinned revision; `matches_pin: true` in each record).

Unit chain, stated once for the whole bundle: protocol references are counts
per 15 s bucket on the raw trace; divide by 15 for raw RPS; multiply by 33.0
for the served replay amplitude this harness measures. All RMSE/MAE/MASE
numbers in these records are at the served amplitude (RPS × 33). The 15 s
selection-fold gate reference in that unit is 36.689 (= 16.677 counts/bucket);
the measured fold OLS mean across the completed 15 s variants is
36.6896 ± 0.2396, confirming the wiring. Resampled variants (interval30/60)
compare against their own per-fold OLS on identical windows (30.4102 / 25.1746)
— cross-interval RMSE is not comparable because the target series itself is
aggregated differently.
