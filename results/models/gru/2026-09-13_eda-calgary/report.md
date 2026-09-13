# EDA - calgary

Source: `data/processed/calgary_real_rps.parquet`

Units: counts per 15 s bucket. Divide by 15 for requests per second. The original series is the raw trace; the deployment arm serves that series multiplied by the manifest factor 33.0. Level-shift ratios, autocorrelations, skew, kurtosis and zero shares are unit-free.

## Shape

```json
{
  "units": "counts per 15 s bucket; divide by 15 for requests per second",
  "samples": 2027652,
  "span_start": "1994-10-24 19:41:30+00:00",
  "span_end": "1995-10-11 20:14:15+00:00",
  "span_days": 352.023,
  "resolution_sec": 15,
  "expected_buckets_if_gapless": 2027652,
  "missing_buckets": 0,
  "mean": 0.3576,
  "std": 1.2205,
  "cv": 3.413,
  "min": 0.0,
  "max": 69.0,
  "p01_p05_p25_p50_p75_p95_p99": [
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    2.0,
    6.0
  ],
  "zero_share": 0.8411,
  "below_1_share": 0.8411,
  "skew": 7.0287,
  "kurtosis": 80.9166,
  "mean_to_max_ratio": 0.0052
}
```

## Day-type profile

| day | buckets | share | mean | p95 | max |
|---|---|---|---|---|---|
| Mon | 289034 | 0.1425 | 0.365 | 2.0 | 30.0 |
| Tue | 293760 | 0.1449 | 0.429 | 3.0 | 33.0 |
| Wed | 292858 | 0.1444 | 0.452 | 3.0 | 69.0 |
| Thu | 288000 | 0.142 | 0.437 | 3.0 | 37.0 |
| Fri | 288000 | 0.142 | 0.386 | 2.0 | 38.0 |
| Sat | 288000 | 0.142 | 0.215 | 1.0 | 35.0 |
| Sun | 288000 | 0.142 | 0.218 | 1.0 | 37.0 |

## Hourly profile

```json
{
  "hourly_mean_first_day": {
    "0": 0.183,
    "1": 0.371,
    "2": 0.033,
    "3": 0.05,
    "4": 0.117,
    "5": 0.138,
    "6": 0.05,
    "7": 0.075,
    "8": 0.0,
    "9": 0.05,
    "10": 0.138,
    "11": 0.021,
    "12": 0.013,
    "13": 0.108,
    "14": 0.092,
    "15": 0.312,
    "16": 0.533,
    "17": 0.242,
    "18": 0.358,
    "19": 0.283,
    "20": 0.362,
    "21": 0.8,
    "22": 0.442,
    "23": 0.304
  },
  "peak_hour": 21,
  "trough_hour": 8,
  "peak_to_trough_ratio": 800000000.0
}
```

## Seasonal structure

```json
{
  "autocorr_lag_1": 0.3546,
  "autocorr_lag_4": 0.1786,
  "autocorr_lag_120": 0.0703,
  "autocorr_lag_480": 0.0531,
  "autocorr_daily_5760": 0.0483,
  "autocorr_weekly_40320": 0.0509,
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
    "m4": 0.403585915120618,
    "m5": 0.37390517332014195,
    "m6": 0.3490108882870893
  },
  "spectral_entropy": 0.9305298715592561,
  "level_slope_fit": {
    "residual_std": 1.1326858734512395,
    "series_std": 1.2204928496514031,
    "residual_variance_share": 0.8612881845535678
  },
  "permutation_entropy_of_level_slope_residuals_m5": 0.4167840211264181,
  "white_noise_reference_m5": 0.9999939139241548
}
```

## Blocked design (1d blocks)

349 blocks, 349 with train/test day-type overlap, 150 testing a weekend day.

| block | train span | test span | train days | test days | train mean | test mean | shift |
|---|---|---|---|---|---|---|---|
| 3 | 1994-10-24 19:41:30+00:00 to 1994-10-27 19:31:45+00:00 | 1994-10-27 19:41:30+00:00 to 1994-10-28 19:41:15+00:00 | Mon,Thu,Tue,Wed | Fri,Thu | 0.258 | 0.37 | 1.437 |
| 4 | 1994-10-24 19:41:30+00:00 to 1994-10-28 19:31:45+00:00 | 1994-10-28 19:41:30+00:00 to 1994-10-29 19:41:15+00:00 | Fri,Mon,Thu,Tue,Wed | Fri,Sat | 0.283 | 0.183 | 0.648 |
| 5 | 1994-10-24 19:41:30+00:00 to 1994-10-29 19:31:45+00:00 | 1994-10-29 19:41:30+00:00 to 1994-10-30 19:41:15+00:00 | Fri,Mon,Sat,Thu,Tue,Wed | Sat,Sun | 0.266 | 0.153 | 0.577 |
| 6 | 1994-10-24 19:41:30+00:00 to 1994-10-30 19:31:45+00:00 | 1994-10-30 19:41:30+00:00 to 1994-10-31 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Mon,Sun | 0.247 | 0.217 | 0.878 |
| 7 | 1994-10-24 19:41:30+00:00 to 1994-10-31 19:31:45+00:00 | 1994-10-31 19:41:30+00:00 to 1994-11-01 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Mon,Tue | 0.242 | 0.397 | 1.639 |
| 8 | 1994-10-24 19:41:30+00:00 to 1994-11-01 19:31:45+00:00 | 1994-11-01 19:41:30+00:00 to 1994-11-02 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Tue,Wed | 0.262 | 0.292 | 1.114 |
| 9 | 1994-10-24 19:41:30+00:00 to 1994-11-02 19:31:45+00:00 | 1994-11-02 19:41:30+00:00 to 1994-11-03 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Thu,Wed | 0.265 | 0.41 | 1.547 |
| 10 | 1994-10-24 19:41:30+00:00 to 1994-11-03 19:31:45+00:00 | 1994-11-03 19:41:30+00:00 to 1994-11-04 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Thu | 0.28 | 0.358 | 1.281 |
| 11 | 1994-10-24 19:41:30+00:00 to 1994-11-04 19:31:45+00:00 | 1994-11-04 19:41:30+00:00 to 1994-11-05 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Sat | 0.287 | 0.193 | 0.673 |
| 12 | 1994-10-24 19:41:30+00:00 to 1994-11-05 19:31:45+00:00 | 1994-11-05 19:41:30+00:00 to 1994-11-06 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Sat,Sun | 0.279 | 0.099 | 0.353 |
| 349 | 1994-10-24 19:41:30+00:00 to 1995-10-08 19:31:45+00:00 | 1995-10-08 19:41:30+00:00 to 1995-10-09 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Mon,Sun | 0.356 | 0.473 | 1.33 |
| 350 | 1994-10-24 19:41:30+00:00 to 1995-10-09 19:31:45+00:00 | 1995-10-09 19:41:30+00:00 to 1995-10-10 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Mon,Tue | 0.356 | 0.539 | 1.513 |
| 351 | 1994-10-24 19:41:30+00:00 to 1995-10-10 19:31:45+00:00 | 1995-10-10 19:41:30+00:00 to 1995-10-11 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Tue,Wed | 0.356 | 0.746 | 2.093 |
| ... | 336 further blocks, full table in eda.json | | | | | | |

## Blocked design (7d blocks)

49 blocks, 49 with train/test day-type overlap, 49 testing a weekend day.

| block | train span | test span | train days | test days | train mean | test mean | shift |
|---|---|---|---|---|---|---|---|
| 3 | 1994-10-24 19:41:30+00:00 to 1994-10-27 19:31:45+00:00 | 1994-10-27 19:41:30+00:00 to 1994-11-03 19:41:15+00:00 | Mon,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.258 | 0.289 | 1.122 |
| 4 | 1994-10-24 19:41:30+00:00 to 1994-11-03 19:31:45+00:00 | 1994-11-03 19:41:30+00:00 to 1994-11-10 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.28 | 0.213 | 0.763 |
| 5 | 1994-10-24 19:41:30+00:00 to 1994-11-10 19:31:45+00:00 | 1994-11-10 19:41:30+00:00 to 1994-11-17 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.252 | 0.208 | 0.823 |
| 6 | 1994-10-24 19:41:30+00:00 to 1994-11-17 19:31:45+00:00 | 1994-11-17 19:41:30+00:00 to 1994-11-24 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.239 | 0.237 | 0.988 |
| 7 | 1994-10-24 19:41:30+00:00 to 1994-11-24 19:31:45+00:00 | 1994-11-24 19:41:30+00:00 to 1994-12-01 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.239 | 0.25 | 1.047 |
| 8 | 1994-10-24 19:41:30+00:00 to 1994-12-01 19:31:45+00:00 | 1994-12-01 19:41:30+00:00 to 1994-12-08 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.241 | 0.213 | 0.884 |
| 9 | 1994-10-24 19:41:30+00:00 to 1994-12-08 19:31:45+00:00 | 1994-12-08 19:41:30+00:00 to 1994-12-15 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.237 | 0.215 | 0.908 |
| 10 | 1994-10-24 19:41:30+00:00 to 1994-12-15 19:31:45+00:00 | 1994-12-15 19:41:30+00:00 to 1994-12-22 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.234 | 0.215 | 0.922 |
| 11 | 1994-10-24 19:41:30+00:00 to 1994-12-22 19:31:45+00:00 | 1994-12-22 19:41:30+00:00 to 1994-12-29 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.231 | 0.07 | 0.301 |
| 12 | 1994-10-24 19:41:30+00:00 to 1994-12-29 19:31:45+00:00 | 1994-12-29 19:41:30+00:00 to 1995-01-05 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.214 | 0.092 | 0.429 |
| 49 | 1994-10-24 19:41:30+00:00 to 1995-09-14 19:31:45+00:00 | 1995-09-14 19:41:30+00:00 to 1995-09-21 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.337 | 0.609 | 1.808 |
| 50 | 1994-10-24 19:41:30+00:00 to 1995-09-21 19:31:45+00:00 | 1995-09-21 19:41:30+00:00 to 1995-09-28 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.342 | 0.68 | 1.987 |
| 51 | 1994-10-24 19:41:30+00:00 to 1995-09-28 19:31:45+00:00 | 1995-09-28 19:41:30+00:00 to 1995-10-05 19:41:15+00:00 | Fri,Mon,Sat,Sun,Thu,Tue,Wed | Fri,Mon,Sat,Sun,Thu,Tue,Wed | 0.349 | 0.61 | 1.747 |
| ... | 36 further blocks, full table in eda.json | | | | | | |