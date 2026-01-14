# Model Comparison Results

Generated: 2026-01-14 09:49

## Summary

```
              Model      RMSE       MAE      MAPE    RMSE %
  Moving Avg (w=15) 11.366227  9.214927  9.356022 11.116344
        EMA (α=0.3) 11.529450  9.367890  9.569601 11.275978
   Moving Avg (w=5) 11.776219  9.636620  9.855986 11.517322
  Linear Regression 11.816924  9.559499  9.767366 11.557132
 Naive (Last Value) 15.164265 12.445070 12.739017 14.830883
Seasonal Naive (1h) 18.939860 15.608451 15.469380 18.523474
```

## Analysis

- **Best Model**: Moving Avg (w=15) (RMSE: 11.12%)
- **Linear Regression**: RMSE 11.56%
- **Naive Baseline**: RMSE 14.83%

## Thesis Target

- Target: RMSE < 20% of average traffic
- Linear Regression: ✅ PASS
