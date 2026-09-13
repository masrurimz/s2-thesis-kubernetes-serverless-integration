# EDA - clarknet

Source: `data/processed/clarknet_real_rps.parquet`

Units: counts per 15 s bucket. Divide by 15 for requests per second. The original series is the raw trace; the deployment arm serves that series multiplied by the manifest factor 33.0. Level-shift ratios, autocorrelations, skew, kurtosis and zero shares are unit-free.

## Shape

```json
{
  "units": "counts per 15 s bucket; divide by 15 for requests per second",
  "samples": 40315,
  "span_start": "1995-08-28 04:00:30+00:00",
  "span_end": "1995-09-04 03:59:00+00:00",
  "span_days": 6.999,
  "resolution_sec": 15,
  "expected_buckets_if_gapless": 40315,
  "missing_buckets": 0,
  "mean": 41.0414,
  "std": 22.9477,
  "cv": 0.5591,
  "min": 0.0,
  "max": 188.0,
  "p01_p05_p25_p50_p75_p95_p99": [
    5.0,
    11.0,
    24.0,
    37.0,
    55.0,
    84.0,
    107.0
  ],
  "zero_share": 0.0007,
  "below_1_share": 0.0007,
  "skew": 0.8838,
  "kurtosis": 0.8158,
  "mean_to_max_ratio": 0.2183
}
```

## Day-type profile

| day | buckets | share | mean | p95 | max |
|---|---|---|---|---|---|
| Mon | 5755 | 0.1428 | 41.917 | 85.0 | 164.0 |
| Tue | 5760 | 0.1429 | 46.659 | 91.05 | 175.0 |
| Wed | 5760 | 0.1429 | 46.871 | 92.0 | 188.0 |
| Thu | 5760 | 0.1429 | 45.792 | 88.0 | 146.0 |
| Fri | 5760 | 0.1429 | 46.995 | 91.0 | 162.0 |
| Sat | 5760 | 0.1429 | 30.887 | 60.0 | 106.0 |
| Sun | 5760 | 0.1429 | 28.17 | 53.0 | 94.0 |

## Hourly profile

```json
{
  "hourly_mean_first_day": {
    "0": 45.358,
    "1": 47.771,
    "2": 45.354,
    "3": 45.546,
    "4": 35.654,
    "5": 26.3,
    "6": 27.012,
    "7": 24.121,
    "8": 19.312,
    "9": 19.908,
    "10": 20.363,
    "11": 24.846,
    "12": 31.35,
    "13": 38.425,
    "14": 50.2,
    "15": 57.867,
    "16": 60.388,
    "17": 59.483,
    "18": 61.733,
    "19": 70.254,
    "20": 66.683,
    "21": 60.562,
    "22": 56.021,
    "23": 52.833
  },
  "peak_hour": 19,
  "trough_hour": 8,
  "peak_to_trough_ratio": 3.638
}
```

## Seasonal structure

```json
{
  "autocorr_lag_1": 0.7307,
  "autocorr_lag_4": 0.615,
  "autocorr_lag_120": 0.5435,
  "autocorr_lag_480": 0.481,
  "autocorr_daily_5760": 0.4546,
  "stl_variance_share": "skipped: ModuleNotFoundError"
}
```

## Stationarity

```json
{
  "skipped": "ModuleNotFoundError"
}
```

## Forecastability

```json
{
  "permutation_entropy": {
    "m4": 0.9911326207320784,
    "m5": 0.9875675090029443,
    "m6": 0.9835217349781831
  },
  "spectral_entropy": 0.5664834257583647,
  "level_slope_fit": {
    "residual_std": 15.145106844684621,
    "series_std": 22.947704075967867,
    "residual_variance_share": 0.4355782658092313
  },
  "permutation_entropy_of_level_slope_residuals_m5": 0.994638560055631,
  "white_noise_reference_m5": 0.9995949434217731
}
```

## Blocked design (1d blocks)

3 blocks, 3 with train/test day-type overlap, 2 testing a weekend day.

| block | train span | test span | train days | test days | train mean | test mean | shift |
|---|---|---|---|---|---|---|---|
| 3 | 1995-08-28 04:00:30+00:00 to 1995-08-31 03:50:45+00:00 | 1995-08-31 04:00:30+00:00 to 1995-09-01 04:00:15+00:00 | Mon,Thu,Tue,Wed | Fri,Thu | 45.852 | 45.031 | 0.982 |
| 4 | 1995-08-28 04:00:30+00:00 to 1995-09-01 03:50:45+00:00 | 1995-09-01 04:00:30+00:00 to 1995-09-02 04:00:15+00:00 | Fri,Mon,Thu,Tue,Wed | Fri,Sat | 45.645 | 46.633 | 1.022 |
| 5 | 1995-08-28 04:00:30+00:00 to 1995-09-02 03:50:45+00:00 | 1995-09-02 04:00:30+00:00 to 1995-09-03 04:00:15+00:00 | Fri,Mon,Sat,Thu,Tue,Wed | Sat,Sun | 45.861 | 29.796 | 0.65 |

## Blocked design (7d blocks)

0 blocks, 0 with train/test day-type overlap, 0 testing a weekend day.

| block | train span | test span | train days | test days | train mean | test mean | shift |
|---|---|---|---|---|---|---|---|