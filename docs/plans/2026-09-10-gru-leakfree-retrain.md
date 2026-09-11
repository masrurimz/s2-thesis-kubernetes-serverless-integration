# GRU retrain program: leak-free protocol and a model the thesis can defend

The deployed GRU was retrained in 18 seconds on synthetic data to raise its horizon from 5 to 9 steps. It carries the definitive H2 result, it was never evaluated on the ClarkNet trace the testbed replays, and its supporting HPO study ran at horizon 5 on synthetic data while the thesis text claims otherwise. This plan replaces it with a ClarkNet-trained, horizon-9 model whose accuracy is measured out of sample on the exact window the testbed replays, and it adds the missing GRU-versus-LSTM comparison measured on our own data.

## Definition of done

One command runs the whole study and writes a bundle. Done means all of these hold at once.

1. The training split is chronological, the normalisation is fit on the training portion only, and no input or target window crosses a split boundary. A check inside the pipeline fails the run when that is violated.
2. The ClarkNet replay window sits strictly inside the held-out test portion, so the model never saw it. The pipeline asserts this by index and fails the run otherwise.
3. Hyperparameters are selected on a validation portion only, at the deployment horizon of 9 steps. The holdout is evaluated once.
4. The reported accuracy comes with these baselines computed on the same windows: persistence, linear trend, and seasonal naive.
5. GRU and LSTM are trained under one protocol, one trial budget, and one seed set, and the difference is reported with a paired test.
6. Every number in the bundle names its split indices, seeds, and the sha256 of the model artifact.
7. Thesis chapters, `results/claims/FINAL_NUMBERS.md`, and the professor Q and A entries quote only the new bundle.

## Protocol

### Data

| Series | Source | Role |
|---|---|---|
| ClarkNet, 15 s | `data/processed/clarknet_real_rps.parquet` resampled to 15 s, 40,315 samples | Training, validation, test, and the deployment slice |
| Replay window | 15 s indices 28,860 to 28,940, from `data/trace-replay/clarknet_replay_manifest.json` | Held-out deployment slice. The testbed replays exactly this |
| Synthetic archetypes | `data/trace-replay/synthetic_archetypes.py`, spike, ramp, periodic, stationary | Out-of-distribution check. Never used for selection |

### Splits

Chronological, no shuffling, and an embargo of `sequence_length + horizon - 1` samples at every boundary. With a 30-step input and a 9-step horizon the embargo is 38 samples, which is 9.5 minutes.

| Portion | 15 s indices | Samples | Purpose |
|---|---|---|---|
| Train | 0 to 22,500 | 22,500 | Fit weights and the normalisation statistics |
| Embargo | 22,501 to 22,538 | 38 | Discard |
| Validation | 22,539 to 26,204 | 3,666 | Early stopping and hyperparameter selection |
| Embargo | 26,205 to 26,242 | 38 | Discard |
| Test | 26,243 to 40,314 | 14,072 | Reported once. Contains the replay window at 28,860 |

Final model fit rule. Select hyperparameters and the epoch budget on validation, then refit on train plus validation at that frozen budget, then evaluate on test once.

### Evaluation

Fixed-origin holdout metrics answer "how good is the deployed model". Rolling-origin folds answer "how stable is that number".

| Metric | Definition |
|---|---|
| RMSE and MAE | Per horizon step 1 to 9, in requests per second, plus the percentage form |
| Normalised RMSE | RMSE divided by the mean target, matching the existing figure of merit |
| Skill score | `1 - RMSE_model / RMSE_persistence`, the headline number |
| Under-prediction on rising targets | Mean and p90 of `(actual - predicted)`, per horizon step. This is the quantity behind the 40 to 50 percent ramp shortfall recorded as Bug 13 |
| Upper-envelope coverage | Fraction of rising targets inside `point + offsets`, matching the serving contract |
| Per-archetype RMSE | The out-of-distribution check on the synthetic spike, ramp, periodic, and stationary series |

The replay slice is reported on its own. It is the distribution the closed loop actually sees, and it is the number to put in the thesis.

### Seeds and statistics

Five seeds for the final comparison, meaning five training runs per cell. Report mean and standard deviation across seeds for the holdout metrics, and mean and standard deviation across rolling-origin folds for the stability numbers. Compare GRU against LSTM with a paired test across folds and seeds, reusing the permutation machinery in `libs/analysis` rather than a new implementation.

### Artifact

`results/models/gru/<date>_clarknet-15s-h9-leakfree/` holds `meta.yaml`, `study.json`, `metrics.json`, `report.md`, per-horizon CSVs, and the model file. `meta.yaml` records the split indices, the embargo, the seeds, the configuration per cell, the git revision, and the sha256 of the model. Promotion to `data/models/gru_model.pt` happens only through an explicit flag, and the previous artifact is backed up and hashed first.

## Phases

### Phase 1. Build the harness

- [ ] Fit the normalisation on the training portion only in `GRUPredictor.train`.
- [ ] Split values before creating windows, with the embargo, in `GRUPredictor.train`.
- [ ] Add a `cell_type` field to `GRUConfig` so the LSTM arm shares the network, the split, and the serving path.
- [ ] Thread the horizon through `apps/experiment/experiment/tuning/gru_hpo.py`, replacing the literal 5 with the calibration horizon of 9.
- [ ] Add the seasonal naive baseline next to persistence and linear trend.
- [ ] Add rolling-origin evaluation with per-fold aggregation.
- [ ] Add multi-seed runs and the paired GRU against LSTM comparison.
- [ ] Write the bundle with split indices, seeds, and artifact hashes.
- [ ] Add a `--promote` flag, off by default.

### Phase 2. Prove the harness catches leakage

- [ ] A test that no training window overlaps a validation window by index.
- [ ] A test that perturbing the validation portion leaves the fitted scaler unchanged.
- [ ] A leak-versus-clean RMSE gain measurement on one synthetic series, reported in the bundle as harness evidence.

### Phase 3. Run the study

- [ ] Hyperparameter search on the development portion at horizon 9, both cells, 30 trials.
- [ ] Final fits on train plus validation, five seeds per cell.
- [ ] Holdout, replay-slice, and archetype evaluation with baselines.
- [ ] Promotion gate result against persistence and linear trend recorded.

### Phase 4. Re-derive what the numbers touch

- [ ] `results/claims/FINAL_NUMBERS.md`, quoting the new bundle only.
- [ ] `results/models/gru/` bundle registered in the evidence registry.
- [ ] Thesis chapter 3 protocol text, chapter 4 results, chapter 1 and 5 claims.
- [ ] The HPO data-source contradiction between chapter 4 and QA-016, settled from `study.json`.
- [ ] QA-017 rewritten around our own measured comparison.

### Phase 5. Decide on the testbed rerun

- [ ] Promote the new artifact, or keep the old one and disclose.
- [ ] Rerun the paired S3 and S4 bundle, about 1.9 hours for five pairs, or record why not. This is EVID-003.

## Phase 6. Predictor improvement round

The first leak-free study used a six-trial search over a narrow space and no architecture work. Measured against a linear autoregression on the same window, the GRU does not yet earn its place (29.63 against 29.46 RMSE), so this phase exists to find out whether the model class is the limit or the training recipe is.

Stage 1, cheap single-configuration probes, one change at a time, each measured on the same held-out region.

- [ ] Longer input window. Thirty samples is 7.5 minutes. Test 120 samples, 30 minutes. Requires the split embargo to grow from 38 to 128 samples, so the split builder must derive the gap from the window and horizon instead of the frozen literals.
- [ ] Calendar features. Time-of-day sine and cosine as exogenous inputs. This is the standard first win on a diurnal trace and the plain GRU cannot see the hour at all.
- [ ] Reversible instance normalization @kim2022revin, per window, inverted at the output. The standard remedy for the distribution shift between the training region and the replay region.
- [ ] Log transform of the target, because request rates are right skewed and a burst dominates the squared error.
- [ ] Asymmetric loss. Train the point head with a pinball or asymmetric squared loss at the upper quantile instead of optimizing the asymmetry only in the selection metric.
- [ ] Seed ensembling. Average the three seed artifacts. Nearly free, since the seeds are already trained.

Stage 1 results, single seed each, identical held-out windows, OLS autoregression as the gate.

| Lever | Model RMSE | OLS on same windows | Kept |
|---|---|---|---|
| baseline, 30-window | 29.6612 | 29.4649 | reference |
| 120-window | 28.2156 | 28.1172 | no, gate not cleared |
| RevIN | 29.5852 | 29.4649 | no |
| seed ensemble, 3 seeds | 29.6051 | 29.4649 | no |
| log target | 30.0321 | 29.4649 | no, worse |
| calendar features, raw sin/cos | 40.6016 | 29.4649 | no, harmful |
| pinball loss at q=0.9 | 50.4815 | 29.4649 | no, mis-specified for a point head |

**No lever cleared the gate.** The 120-window is the only one that lowers absolute error, by 4.9%, and it lowers the linear arm by the same amount, so the conclusion that the network is equivalent to a linear model at this resolution survives every lever tried. Stage 2 was therefore not entered. The 120-window remains the one candidate worth adopting, and running it under the full study protocol costs six to twelve hours at that window size.

Stage 2, only if stage 1 shows a lever that moves the held-out error beyond noise.

- [ ] Wider search on the winning lever set, thirty trials or more, identical budget for GRU and LSTM.
- [ ] Re-derive every downstream number if the model changes, then re-run the replay-slice and baseline comparison.

Gate. A change is kept only when it reduces holdout RMSE against a linear autoregression on identical windows. A change that only closes the gap to linear is reported as a limitation, not a win.

### Refit leak found and fixed mid-run (2026-09-10)

The first LSTM attempt early-stopped on the test region. `GRUPredictor.train` decided `has_val` from the length of the validation slice rather than from `val_ratio`, so the refit call `train(full_df, val_ratio=0.0, train_end=splits.val_end)` still took the early-stopping branch, with the test region as its validation slice. The run was stopped, the contract fixed so `val_ratio=0.0` always uses the no-validation final-fit path, and a unit test added that mutates the test region and asserts the training history is unchanged.

The completed GRU bundle is not affected, because the code at that time refit on the train portion with the validation portion as its early-stopping slice. It is however a protocol deviation, since the specification says refit on train plus validation, so both arms are re-run under the corrected call before any of these numbers reach the thesis as final.

Consequence for sequencing: the probes run before the study re-runs, so a winning lever is integrated once instead of forcing a second re-run.

Stage 3, the synthetic arm, runs under the identical protocol so the pre-registered H3 target is re-derived on clean ground rather than quoted from the superseded bundles.

## What this closes

| Current gap | Evidence today | After |
|---|---|---|
| Deployed model trained on synthetic data in 18 s | `data/models/gru_model.pt` metadata, rmse 6.61 | ClarkNet-trained, horizon 9, leak-free |
| HPO ran at horizon 5 | `FIXED_HORIZON = 5` in `gru_hpo.py` | Searched at the deployed horizon |
| HPO data source contradicting the thesis | `study.json` says synthetic, QA-016 says ClarkNet | One recorded source |
| Normalisation fit on all data including the internal validation slice | `gru_predictor.py:206` | Fit on train only |
| Windows built before the split | `gru_predictor.py:212` then `:215` | Split first, embargo enforced |
| No GRU against LSTM comparison on our data | Only borrowed literature | Our own paired measurement |
| No baselines in the thesis numbers | Baselines exist in the HPO code but are not in the thesis | Persistence, trend, seasonal naive |
| No artifact hash anywhere | `results/evidence/_artifact_index.jsonl` covers JSON only | sha256 in the bundle metadata and the trail |

## Open decisions for the operator

1. Retrain target. ClarkNet-trained with the replay window held out, or keep the synthetic-trained model and add the study beside it. Recommendation is the first, because the second leaves the headline result resting on an artifact the thesis cannot defend.
2. Testbed rerun. Rerun the five paired S3 and S4 runs once the new artifact is promoted, or publish the model study alone with a disclosure that the closed-loop evidence predates it. Recommendation is the rerun, which is what EVID-003 already asks for.

## Risks

- A ClarkNet-trained model may be less accurate on the replay window than the synthetic-trained one, since the synthetic generator was built to be predictable. That is a finding, not a failure, and the thesis reports it either way.
- The replay window is 80 samples at 15 s. Window count there is small, so the replay-slice metrics carry wide uncertainty. Report them with the fold spread and do not over-claim.
- Torch on the Radeon iGPU is flaky on this box. If the GPU path fails, run on CPU, which is minutes for a model of this size.
- Changing the artifact invalidates the S4 evidence until the rerun lands. Do not promote before the rerun is scheduled.
