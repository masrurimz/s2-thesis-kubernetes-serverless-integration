# GRU/LSTM leak-free study (horizon 9)

Generated: 2026-09-10T22:43:53  
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
| gru | 29.635 ± 0.016 | 22.486 ± 0.079 | 0.3961 ± 0.0002 | 0.216 ± 0.000 | 0.921 |

- gru archetype RMSE (OOD check): spike=26.58, ramp=24.27, periodic=25.42, stationary=4.74
- Baselines on identical windows: persistence RMSE 37.813, linear trend 46.534, seasonal naive 53.688
- Rolling-origin over test (5 blocks): RMSE 29.039 ± 6.893

## Winner

`clarknet/gru` (mean RMSE 29.635); artifact `results/models/gru/2026-09-10_clarknet-15s-h9-leakfree/artifacts/clarknet_gru_s44.pt` (sha256 `20623c19c8407b11…`). Promotion to data/models/gru_model.pt happens only with --promote.
