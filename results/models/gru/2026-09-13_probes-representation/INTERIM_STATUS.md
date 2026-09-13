# Status — 2026-09-13_probes-representation (complete)

**Status as of 2026-09-13 ~16:30 UTC: all 12 specified variants have records.**
The round is complete. The batch was paused mid-day for the H1 baseline
measurement window, then resumed; the four queued variants and the calendar
re-run finished after the gate.

Completed (record + report.md row present):

- interval30, interval60, revin_robust, nlinear, diff_target, robust_scale,
  quantile_norm, nbeats  (first batch, splits pin 5f937edb)
- roll_stats, ewma, diff_input, decomp, calendar  (second batch, splits pin
  cd7b5266 — the regime-gap-note revision; geometry identical)

**Gate verdict: none of the twelve beats the per-fold OLS autoregression on the
selection folds** (`beats_ols_on_selection_folds = false` in every record).
Selection-fold RMSE vs OLS 36.69 served RPS: decomp 37.41, ewma 37.51,
roll_stats 37.61, diff_input 37.70, calendar 38.55. `ewma` (+0.53%) and `decomp`
(+0.06%) beat OLS on the *test* region and still fail the selection gate — the
selection folds decide, not the test region.

Protocol pin carried by every record (`splits_module.sha256` in each JSON):

- 5f937edb361fbcea1a49334d92d768d409eefd1b12c563c5e708b9a1919631e3 — first batch
- cd7b5266635275f1eb2f1176da30f3e93c90f6c3e1524f0c6c22e7e9e400e25a — second batch
  (adds the computed regime-gap note; split boundaries and geometry unchanged)

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
