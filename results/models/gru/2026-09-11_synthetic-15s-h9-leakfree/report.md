# GRU/LSTM leak-free study (horizon 9)

Generated: 2026-09-11T01:05:59  
Git: `f4f2c44ebd6a346b0377b69e379bc7ca3334273c` (dirty=true)  
Seeds: [42] — trials per cell: 6

## Protocol

Chronological splits with embargo = sequence_length + horizon - 1 at every boundary. Selection (hyperparameters + epoch budget) on the validation portion only; refit on train+validation at the frozen budget; test evaluated once per seed.

### Data arm: synthetic

- Samples: 17280
- Split indices: train_end=9644, val_start=9682, val_end=11253, test_start=11291, embargo=38
- Derivation: seed 42, 72 h at 1-minute resolution (base_rps 100); each minute value held across its four 15 s buckets; splits proportional to the ClarkNet protocol fractions with the same embargo rule

## Holdout results (test portion, mean ± std across seeds)

### synthetic

| cell | RMSE | MAE | nRMSE | skill vs persistence | coverage |
|---|---|---|---|---|---|
| gru | 6.063 ± 0.000 | 4.122 ± 0.000 | 0.0521 ± 0.0000 | 0.219 ± 0.000 | 0.865 |

- gru archetype RMSE (OOD check): spike=20.22, ramp=22.99, periodic=26.67, stationary=0.23
- Baselines on identical windows: persistence RMSE 7.768, linear trend 12.152, seasonal naive 11.297
- Rolling-origin over test (5 blocks): RMSE 5.950 ± 0.213

## Winner

No winner (need both cells on the clarknet arm).
