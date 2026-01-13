# Data

HTTP trace datasets for training and evaluation.

## Structure

```
data/
├── raw/                # Original log files
│   ├── clarknet/      # ClarkNet WWW server logs (~2M requests)
│   └── calgary/       # University of Calgary CS logs (~2M requests)
└── processed/         # RPS time series (ready for training)
    ├── clarknet_rps.parquet
    ├── calgary_rps.parquet
    └── splits/        # Train/val/test splits
```

## Dataset Sources (Thesis 3.2)

| Dataset | Requests | Time Period | Source |
|---------|----------|-------------|--------|
| ClarkNet | ~2M | Aug-Sep 1995 | ClarkNet WWW Server |
| Calgary | ~2M | Oct 1994 | University of Calgary CS |

## Log Format (CLF)

```
204.249.225.59 - - [28/Aug/1995:00:00:34 -0400] "GET /pub/rmharris/catalogs/dawsocat/intro.html HTTP/1.0" 200 3542
```

## Processing Pipeline

```
Raw HTTP Logs → CLF Parsing → Timestamp Extraction → RPS Aggregation → Time Series
```

1. Parse Combined Log Format entries
2. Extract timestamp for each request
3. Aggregate to requests-per-second (RPS)
4. Create sliding window sequences for GRU
5. Split: 70% train / 15% validation / 15% test

## Download Links

- ClarkNet: ftp://ita.ee.lbl.gov/traces/clarknet-http.tar.gz
- Calgary: ftp://ita.ee.lbl.gov/traces/calgary-http.tar.gz
