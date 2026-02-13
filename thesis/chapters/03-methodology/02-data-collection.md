## 3.2 Data Collection (Pengumpulan Data)

### 3.2.1 Primary Training Data: Synthetic Workload Patterns

The GRU prediction model is trained on synthetically generated traffic patterns designed to represent common cloud workload characteristics. Four pattern types are combined to produce the training dataset:

- **Diurnal cycles**: Sinusoidal traffic patterns simulating daily usage peaks and troughs, representing the most common workload shape in web applications.
- **Bursty spikes**: Short-duration traffic surges injected at random intervals, simulating flash crowd events and viral content scenarios.
- **Gradual ramps**: Linearly increasing traffic segments representing organic growth or planned load increases.
- **Baseline noise**: Gaussian random fluctuations added to all patterns to simulate real-world measurement variability.

These four components are superimposed and scaled to produce time-series sequences of requests per second (RPS). The synthetic approach was chosen for three reasons: (1) it provides controlled ground-truth labels for supervised training, (2) it enables generation of arbitrary quantities of training data, and (3) it allows systematic inclusion of specific pattern types (particularly bursty spikes and ramps) that are underrepresented in historical trace datasets.

**Data Processing Pipeline:**

```
Pattern Definition → Traffic Simulation → RPS Time Series → Sliding Windows → Train/Val/Test Split
```

Processing steps:

1. Generate synthetic traffic patterns by combining the four component types with configurable amplitudes and frequencies.
2. Construct sliding window sequences using a 60-second input window to capture short-term temporal dependencies.
3. Split the resulting sequences into training (70%), validation (15%), and test (15%) sets with temporal ordering preserved to prevent data leakage.

### 3.2.2 Reference Data: Real HTTP Traces

ClarkNet and Calgary HTTP trace datasets are used for baseline model comparison and validation of the GRU model's generalization capability. These datasets are **not** used for training.

**Table 3-1: Reference Dataset Characteristics**

| Dataset | Requests | Time Period | Source | Usage |
|---------|----------|-------------|--------|-------|
| ClarkNet | ~2M | Aug–Sep 1995 | ClarkNet WWW Server | Baseline comparison |
| Calgary | ~2M | Oct 1994 | University of Calgary CS | Pattern validation |

**Table 3-2: Dataset Request Examples**

| Dataset | Request Example |
|---------|-----------------|
| University of Calgary | `local - - [24/Oct/1994:13:41:41 -0600] "GET index.html HTTP/1.0" 200 150` |
| ClarkNet | `204.249.225.59 - - [28/Aug/1995:00:00:34 -0400] "GET /pub/rmharris/catalogs/dawsocat/intro.html HTTP/1.0" 200 3542` |

**Real Trace Processing Pipeline (for baseline comparison):**

```
Raw HTTP Logs → CLF Parsing → Timestamp Extraction → RPS Aggregation → Time Series
```

The real trace data undergoes the same sliding window transformation as the synthetic data to enable direct comparison of prediction accuracy across data sources. The key difference is aggregation granularity: synthetic data uses 1-second intervals (matching the live prediction server), while real traces are aggregated at 5-minute intervals due to the lower temporal resolution of historical access logs.
