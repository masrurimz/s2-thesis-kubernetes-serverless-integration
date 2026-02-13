## 4.4 Cost Analysis

Cost analysis was performed using proxy estimates based on published cloud pricing models for AWS, GCP, and Azure. These are projected costs, not actual billing data.

### 4.4.1 Per-Provider Cost Breakdown

**Table 4.21: Monthly Cost Estimates at 100 RPS (AWS)**

| Scenario | K8s Cost | Serverless Cost | Total | vs S1 | vs S2 |
|----------|----------|-----------------|-------|-------|-------|
| S1 (K8s-only) | $141.12 | $0.00 | $162.85 | — | −44% |
| S2 (Serverless-only) | $0.00 | $267.84 | $289.57 | +78% | — |
| S3 (Hybrid Reactive) | $141.12 | $42.77 | $205.62 | +26% | −29% |
| S4 (Hybrid Predictive) | $141.12 | $30.46 | $193.31 | +19% | −33% |

**Table 4.22: Cross-Provider Monthly Cost Comparison**

| Scenario | AWS | GCP | Azure |
|----------|-----|-----|-------|
| S1 (K8s-only) | $162.85 | $149.22 | $90.12 |
| S2 (Serverless-only) | $289.57 | $320.57 | $280.20 |
| S3 (Hybrid Reactive) | $205.62 | $198.14 | $131.59 |
| S4 (Hybrid Predictive) | $193.31 | $184.50 | $119.67 |

### 4.4.2 Key Findings

**S4 is consistently cheaper than S3 across all providers.** The predictive routing variant reduces serverless invocation costs by anticipating load patterns rather than reacting to violations:

- **AWS**: $193.31 vs. $205.62 (6% savings, $12.31/month)
- **GCP**: $184.50 vs. $198.14 (7% savings, $13.64/month)
- **Azure**: $119.67 vs. $131.59 (9% savings, $11.92/month)

The savings mechanism is straightforward: predictive routing reduces unnecessary serverless invocations by pre-positioning capacity when surges are anticipated, rather than reactively scaling out (which triggers more serverless cold starts and invocations). The 6–9% savings range across providers reflects differences in per-invocation pricing and K8s control plane costs (AWS: $0.10/hr, GCP: $0.10/hr, Azure: $0/hr).

### 4.4.3 Limitations

These cost estimates carry several limitations. They assume constant 100 RPS workload—real workloads vary in intensity and pattern. They do not account for free tiers, reserved instances, committed-use discounts, or volume pricing that would apply in production. K8s control plane pricing varies by provider. The estimates project from the observed traffic distribution patterns between K8s and serverless backends; actual invocation counts in production would differ based on workload characteristics and configuration tuning.

---
