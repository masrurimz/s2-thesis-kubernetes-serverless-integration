# GRU/LSTM leak-free study (horizon 9)

Generated: 2026-09-10T23:43:44  
Git: `f4f2c44ebd6a346b0377b69e379bc7ca3334273c` (dirty=true)  
Seeds: [42, 43, 44] — trials per cell: 6

## Protocol

Chronological splits with embargo = sequence_length + horizon - 1 at every boundary. Selection (hyperparameters + epoch budget) on the validation portion only; refit on train+validation at the frozen budget; test evaluated once per seed.

### Data arm: clarknet

- Samples: 40315
- Split indices: train_end=22500, val_start=22539, val_end=26205, test_start=26243, embargo=38
- Replay scale factor: 33.0 (series multiplied before splitting; scaler fitted on the amplified training portion only)

## Holdout results (test portion, mean ± std across seeds)

### clarknet

| cell | RMSE | MAE | nRMSE | skill vs persistence | coverage |
|---|---|---|---|---|---|
| lstm | 29.917 ± 0.159 | 23.202 ± 0.243 | 0.3999 ± 0.0021 | 0.209 ± 0.004 | 0.927 |

- lstm archetype RMSE (OOD check): spike=36.78, ramp=23.18, periodic=26.47, stationary=4.37
- Baselines on identical windows: persistence RMSE 37.813, linear trend 46.534, seasonal naive 53.688
- Rolling-origin over test (5 blocks): RMSE 29.554 ± 6.454

## Winner

`clarknet/lstm` (mean RMSE 29.917); artifact `results/models/gru/2026-09-10_clarknet-15s-h9-lstm/artifacts/clarknet_lstm_s44.pt` (sha256 `5208a42ec6b90761…`). Promotion to data/models/gru_model.pt happens only with --promote.
