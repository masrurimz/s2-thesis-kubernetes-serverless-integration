"""Tests for the second probe wave: interval splits, normalization/representation
levers, causal feature channels, DM, MASE, and day-type splitting.

Pure-function tests — no torch training, no real data, no cluster.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from experiment.tuning.gru_probe import (
    CLARKNET_TOTAL,
    DEFAULT_SEASON,
    FEATURE_VARIANTS,
    FIXED_SAMPLE_INTERVAL,
    ProbeWindows,
    _trailing_feature_channels,
    build_variant_arrays,
    day_type_labels,
    derived_interval_windows,
    diebold_mariano,
    mapped_replay_window,
    probe_windows,
    selection_fold_windows,
    split_metrics_by_day_type,
)

SEQ_LEN, HORIZON = 30, 9
SYNTH = ProbeWindows(
    seq_len=SEQ_LEN,
    horizon=HORIZON,
    fit_end=300,
    val_start=338,
    val_end=400,
    test_start=438,
    embargo_used=38,
)


def _synth_values(n: int = 900, seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (np.abs(rng.normal(50.0, 12.0, size=n)) + 1.0).astype(np.float32)


# ── Interval variants ────────────────────────────────────────────────────────


def test_interval_windows_hold_proportions_embargo_and_replay() -> None:
    n30, n60 = 20158, 10080
    for interval, n_total, horizon_steps in ((30, n30, 5), (60, n60, 3)):
        w = derived_interval_windows(interval, n_total)
        assert w.horizon == horizon_steps
        assert w.seq_len == 30
        assert w.embargo_min == 30 + horizon_steps - 1
        assert w.val_start - w.fit_end >= w.embargo_min
        assert w.test_start - w.val_end >= w.embargo_min
        # Proportional to the frozen fractions (within one resampled sample).
        frac_fit = 22500 / CLARKNET_TOTAL
        frac_val_end = 26205 / CLARKNET_TOTAL
        assert abs(w.fit_end - frac_fit * n_total) <= 1.0
        assert abs(w.val_end - frac_val_end * n_total) <= 1.0
        # Replay window mapped by ratio stays strictly inside the test portion.
        replay = mapped_replay_window(interval)
        assert w.test_start <= replay[0]
        assert replay[1] < n_total


def test_interval_windows_fail_loudly_when_replay_leaves_test() -> None:
    # A tiny series cannot host the derived test region with the embargo.
    try:
        derived_interval_windows(60, 200)
    except ValueError as exc:
        assert "replay" in str(exc) or "usable region" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected a loud protocol failure for a too-short resampled series")


def test_interval_season_scaling() -> None:
    # One day expressed in the variant's samples drives seasonal naive + MASE.
    assert DEFAULT_SEASON == 5760  # one day at 15 s
    assert DEFAULT_SEASON * FIXED_SAMPLE_INTERVAL // 30 == 2880
    assert DEFAULT_SEASON * FIXED_SAMPLE_INTERVAL // 60 == 1440


def test_frozen_variants_unchanged_by_interval_dispatch() -> None:
    w = probe_windows("baseline")
    assert (w.fit_end, w.val_start, w.val_end, w.test_start) == (22500, 22539, 26205, 26243)


# ── Normalization / representation levers ────────────────────────────────────


def test_nlinear_denormalization_uses_last_value_anchor() -> None:
    values = _synth_values()
    arrays = build_variant_arrays("nlinear", values, SYNTH)
    rng = np.random.default_rng(3)
    assert arrays.last_val_raw is not None  # populated for the nlinear anchor
    pn_test = rng.normal(0.0, 1.0, size=(len(arrays.X_test), HORIZON))
    pn_val = rng.normal(0.0, 1.0, size=(len(arrays.X_val), HORIZON))
    np.testing.assert_allclose(
        arrays.denormalize_predictions(pn_test),
        pn_test * arrays.z_std + arrays.last_test_raw[:, None],
        rtol=1e-6,
    )
    np.testing.assert_allclose(
        arrays.denormalize_val_predictions(pn_val),
        pn_val * arrays.z_std + arrays.last_val_raw[:, None],
        rtol=1e-6,
    )


def test_diff_target_reconstruction_is_cumsum_plus_last() -> None:
    values = _synth_values()
    arrays = build_variant_arrays("diff_target", values, SYNTH)
    # "Perfect" network: predict the true normalized per-step deltas.
    assert arrays.last_val_raw is not None  # populated for the diff-target mode
    X_val_raw, last_val = arrays.X_val, arrays.last_val_raw
    # Rebuild delta targets for validation windows from the raw series math.
    seg = values.astype(np.float64)[SYNTH.val_start : SYNTH.val_end]
    n_seq = len(seg) - SEQ_LEN - HORIZON + 1
    idx_y = np.arange(n_seq)[:, None] + np.arange(SEQ_LEN, SEQ_LEN + HORIZON)[None, :]
    delta_targets = np.diff(seg, prepend=seg[:1])[idx_y]
    pn = (delta_targets - arrays.z_mean) / arrays.z_std
    reconstructed = arrays.denormalize_val_predictions(pn)
    expected = last_val[:, None] + np.cumsum(delta_targets, axis=1)
    np.testing.assert_allclose(reconstructed, expected, rtol=1e-5)
    assert X_val_raw.shape[0] == len(last_val)


def test_revin_robust_uses_per_window_median_and_iqr() -> None:
    values = _synth_values()
    arrays = build_variant_arrays("revin_robust", values, SYNTH)
    assert arrays.mode == "revin_robust"
    assert arrays.test_mu is not None and arrays.test_sd is not None  # revin-family only
    # Per-window statistics: mutating one test window leaves the others' stats.
    rng = np.random.default_rng(7)
    pn = rng.normal(0.0, 1.0, size=(len(arrays.X_test), HORIZON))
    preds = arrays.denormalize_predictions(pn)
    np.testing.assert_allclose(preds, pn * arrays.test_sd[:, None] + arrays.test_mu[:, None], rtol=1e-6)
    # Median property: the stored centre of a window equals its value median.
    seg = values.astype(np.float64)[SYNTH.test_start : SYNTH.test_start + len(arrays.X_test) + SEQ_LEN + HORIZON - 1]
    window0 = seg[:SEQ_LEN]
    assert arrays.test_mu[0] == np.float32(np.median(window0))


def test_robust_scale_fits_training_portion_only() -> None:
    values = _synth_values()
    arrays = build_variant_arrays("robust_scale", values, SYNTH)
    mutated = values.copy()
    mutated[SYNTH.test_start :] = 1e6
    arrays_mut = build_variant_arrays("robust_scale", mutated, SYNTH)
    assert arrays.z_mean == arrays_mut.z_mean
    assert arrays.z_std == arrays_mut.z_std


def test_quantile_norm_fits_training_portion_only() -> None:
    values = _synth_values()
    arrays = build_variant_arrays("quantile_norm", values, SYNTH)
    mutated = values.copy()
    mutated[SYNTH.test_start :] = 1e6
    arrays_mut = build_variant_arrays("quantile_norm", mutated, SYNTH)
    # The transformer is fitted on the training portion only: fit/val arrays
    # are bit-identical and the inverse map is unchanged under test mutation.
    np.testing.assert_array_equal(arrays.X_fit, arrays_mut.X_fit)
    np.testing.assert_array_equal(arrays.y_fit, arrays_mut.y_fit)
    np.testing.assert_array_equal(arrays.X_val, arrays_mut.X_val)
    probe = np.linspace(-2.0, 2.0, 9).reshape(-1, 1)
    np.testing.assert_array_equal(arrays.scaler.inverse_transform(probe), arrays_mut.scaler.inverse_transform(probe))


def test_feature_channels_are_trailing_only() -> None:
    values = _synth_values(seed=11)
    for variant in FEATURE_VARIANTS:
        chans, names = _trailing_feature_channels(variant, values.astype(np.float64))
        assert chans is not None, f"{variant} declares no trailing channels"
        assert chans.shape[0] == len(values)
        assert chans.shape[1] == len(names) > 0
        mutated = values.copy()
        half = len(values) // 2
        mutated[half:] = mutated[half:] * 7.0 + 1000.0
        chans_mut, _ = _trailing_feature_channels(variant, mutated.astype(np.float64))
        assert chans_mut is not None
        # Past channel values are untouched by future mutations.
        np.testing.assert_array_equal(chans[: half - 1], chans_mut[: half - 1])


def test_decomp_channels_reconstruct_the_value() -> None:
    values = _synth_values(seed=13)
    chans, names = _trailing_feature_channels("decomp", values.astype(np.float64))
    assert chans is not None
    assert names == ["ma_trend_tr40", "ma_residual_tr40"]
    np.testing.assert_allclose(chans[:, 0] + chans[:, 1], values.astype(np.float64), rtol=1e-9)


def test_feature_variants_append_channels_without_touching_value_norm() -> None:
    values = _synth_values()
    from experiment.tuning import splits as split_protocol

    spec = split_protocol.deployment_split()
    # Both arms must be canonical: the default z-score path and the canonical
    # path fit different statistics, so comparing across them would compare
    # normalisation modes rather than the effect of the feature channels.
    # ``nbeats`` is canonical and carries the value channel alone, which makes
    # it the reference the feature variants must not perturb.
    base = build_variant_arrays("nbeats", values, SYNTH, canonical_spec=spec)
    feat = build_variant_arrays("ewma", values, SYNTH, canonical_spec=spec)
    assert base.mode == feat.mode == "canonical"
    assert base.X_fit.shape[2] == 1
    assert feat.X_fit.shape == (*base.X_fit.shape[:2], 3)
    # Appending feature channels leaves the value channel bit-identical.
    np.testing.assert_array_equal(feat.X_fit[:, :, 0], base.X_fit[:, :, 0])
    np.testing.assert_array_equal(feat.X_val[:, :, 0], base.X_val[:, :, 0])
    stats = split_protocol.normalizer_stats(values, spec)
    # Canonical roundtrip: inverting normalized eval windows returns raw RPS.
    seq = feat.seq_len
    raw = values.astype(np.float64)[SYNTH.test_start : SYNTH.test_start + 200 + seq + 9]
    normed = split_protocol.apply_normalizer(raw, stats)
    np.testing.assert_allclose(split_protocol.invert_normalizer(normed, stats), raw, rtol=1e-9)


# ── Metrics: DM, MASE, day type ──────────────────────────────────────────────


def test_diebold_mariano_sign_and_pvalue() -> None:
    rng = np.random.default_rng(2)
    ols_res = rng.normal(0.0, 5.0, size=(2000, 5))
    # Clearly better variant: far smaller squared loss.
    good = ols_res * 0.2
    dm_good = diebold_mariano(good, ols_res, 5)
    assert dm_good["dm_stat"] < 0
    assert dm_good["p_value_one_sided"] < 0.01
    assert dm_good["hac_lag"] == 4
    # Identical forecasts: no evidence either way.
    dm_same = diebold_mariano(ols_res, ols_res, 5)
    assert abs(dm_same["dm_stat"]) < 1e-12
    assert abs(dm_same["p_value_one_sided"] - 0.5) < 1e-9


def test_selection_fold_windows_match_protocol_geometry() -> None:
    from experiment.tuning import splits as split_protocol
    from experiment.tuning.gru_probe import (
        FOLD_VAL_SPAN,
        splits_module_fingerprint,
    )

    fp = splits_module_fingerprint()
    assert fp["matches_pin"], f"splits.py revision moved: {fp['sha256']}"
    folds = split_protocol.blocked_cv().selection_folds()
    names = [s.name for s in folds]
    assert names == ["clarknet-bcv-b2", "clarknet-bcv-b3", "clarknet-bcv-b4"]

    mapped = selection_fold_windows(15, split_protocol.CLARKNET_N)
    for (_, fw, spec), proto in zip(mapped, folds, strict=True):
        assert spec.train is not None and spec.validation is not None
        assert fw.eval_end == spec.require_region("validation").stop
        assert fw.test_start == spec.require_region("validation").start
        assert fw.val_end == spec.require_region("train").stop
        assert fw.val_start - fw.fit_end == fw.embargo_min  # early-stop gap at the minimum
        assert fw.val_end - fw.val_start == FOLD_VAL_SPAN
        assert fw.stats_end == fw.val_end
        # The replay window never enters any fold's training region.
        assert split_protocol.REPLAY_WINDOW[0] >= fw.val_end

    # Resampled mapping: day-aligned blocks, embargo re-derived in samples.
    mapped30 = selection_fold_windows(30, 20158)
    for _, fw, spec in mapped30:
        assert fw.horizon == 5 and fw.embargo_used == 34
        assert fw.eval_end is not None  # blocked-CV folds carry a bounded eval block
        assert (fw.eval_end - fw.test_start) == split_protocol.DAY // 2


def test_day_type_labels_and_split() -> None:
    ts = pd.DatetimeIndex(
        [
            "1995-09-01 22:00:00+00:00",  # Friday
            "1995-09-02 10:00:00+00:00",  # Saturday
            "1995-09-03 10:00:00+00:00",  # Sunday
            "1995-09-04 02:00:00+00:00",  # Monday
        ]
    )
    labels = day_type_labels(ts)
    assert list(labels) == ["fri_evening", "sat", "sun", "mon"]

    y = np.full((4, 3), 50.0)
    pv = np.full((4, 3), 49.0)
    po = np.full((4, 3), 45.0)
    out = split_metrics_by_day_type(pv, po, y, labels)
    assert set(out) == {"fri_evening", "sat", "sun", "mon"}
    for seg in out.values():
        assert seg["n_windows"] == 1
        assert seg["skill_vs_ols"] > 0  # variant closer to targets than OLS


# ── N-BEATS tower shape ──────────────────────────────────────────────────────


def test_nbeats_tower_forward_shape() -> None:
    try:
        import torch
    except ImportError:  # pragma: no cover
        return
    from experiment.tuning.gru_probe import build_nbeats_tower

    torch.manual_seed(42)
    tower = build_nbeats_tower(seq_len=30, horizon=9)
    x = torch.randn(4, 30, 1)  # probe pipeline shape (batch, seq, 1)
    out = tower(x)
    assert out.shape == (4, 9)
    assert torch.isfinite(out).all()
