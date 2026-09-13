# Capacity-relative crossing target and interval variants (2026-09-13)

Two probes against the per-fold OLS autoregression, under the leak-free split protocol.

## Interval

60-second buckets lower absolute error for any model, because the target becomes coarser and
the wall-clock horizon grows from 135 to 180 seconds. Fold error falls from 36.69 to 25.18
served RPS for the autoregression and from 36.69 to 25.30 for the network. Each resampled
variant is gated against its own per-fold OLS (25.1746 at 60 s), because cross-interval RMSE
is not comparable. This is an interval and horizon change, not a modelling win.

## Crossing target

The predictor is asked for the time until the load crosses the capacity ceiling, and the
question is scored as a decision rather than as a point forecast.

- Recall 0.988 +/- 0.009, against 0.008-0.042 for OLS plus threshold and 0.119-0.163 for persistence.
- Precision 0.336, false-alarm rate 0.598.
- Predicted crossing-time MAE 3.50 steps, about 52 seconds.
- Per-step Brier 0.233 against 0.049 for the reference: the probabilities are overconfident and
  the per-step score fails. The rule therefore reads recall at a bounded false-alarm rate
  rather than a calibrated probability, and calibration is pending.

Labels exist only where the capacity ceiling is approached: 6 replicas in the code default,
not the paired configuration's 10.

Full records: `t_cross.json`.
