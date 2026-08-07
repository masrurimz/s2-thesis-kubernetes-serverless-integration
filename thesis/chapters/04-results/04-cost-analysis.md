## 4.4 Cost Analysis

Cost values in this chapter are AWS proxy projections derived from measured resource consumption. They are **projected, not billed**: no scenario represents an actual cloud invoice. The model maps Kubernetes capacity to EKS/EC2 and serverless execution to Lambda-equivalent usage, using the same pricing assumptions across scenarios.

### 4.4.1 Diagnostic Four-Scenario Projection (n=1)

The corrected diagnostic bundle `2026-07-11_scaling_fix_n1` gives the following directional monthly projections:

| Scenario | Projected monthly USD | Evidence tier |
|---|---:|---|
| S1 (K8s+HPA) | 132 | n=1 diagnostic |
| S2 (Knative-only) | 394 | n=1 diagnostic |
| S3 (hybrid-reactive) | 147 | n=1 diagnostic |
| S4 (hybrid-predictive) | 142 | n=1 diagnostic |

These values characterize the single diagnostic run and must not be treated as universal cost rankings.

### 4.4.2 Definitive Paired Projection (n=5)

For the definitive ClarkNet paired bundle `2026-07-14_clarknet-tuned-paired-n5`, the projected monthly costs are identical:

| Scenario | Projected monthly USD | Interpretation |
|---|---:|---|
| S3 (hybrid-reactive) | **163** | Same measured resource envelope as S4 |
| S4 (hybrid-predictive) | **163** | Identical proxy projection |

The paired result therefore supports a performance comparison at equal modeled cost: S4's primary p99 is 126.0 ms versus S3's 188.5 ms, while the projected monthly cost is USD 163 for each. This is an internal comparison of the same model, not evidence of billed savings.

### 4.4.3 Interpretation and Limits

The diagnostic values show why cost must be reported with performance and evidence tier. S1 is projected at USD 132 but has diagnostic p99 of 2,421.3 ms; S2 is projected at USD 394 and has p99 of 77.7 ms; S3 and S4 occupy the hybrid trade-off region. The definitive paired bundle removes the apparent S3/S4 cost difference: both are USD 163 under the same proxy model.

The model assumes continuous replay at experiment intensity and uses production-oriented AWS resource assumptions rather than treating bounded k3d node counts as a cloud bill. Actual costs vary with region, reservations, request duration, concurrency, node type, traffic volume, and billed service configuration. Dynamic-node stress-harness cost is tracked separately from the serverless proxy and is directional.

Accordingly, this thesis claims **identical projected S3/S4 cost in the definitive paired comparison**, not monthly savings, cost superiority, or actual billing outcomes.

---

*Evidence: `results/claims/FINAL_NUMBERS.md`, `results/claims/CLAIMS_TO_EVIDENCE.md`, `results/experiments/phase-b/2026-07-11_scaling_fix_n1`, and `results/experiments/phase-b/2026-07-14_clarknet-tuned-paired-n5`. All values are projected, not billed.*
