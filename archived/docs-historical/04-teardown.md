# Tearing Down the Setup
> **Historical.** Superseded 2025-07-13 by `thesis infra teardown` (see `docs/getting-started/02-quick-start.md`). Kept for provenance; do not follow these instructions.

Once the experiment is finished, you can tear down the Kubernetes clusters:

## Step 1: Tear Down Kubernetes Clusters

Run the following script to delete all clusters:

```bash
./infra/teardown-clusters.sh
```

This will remove **Cluster A**, **Cluster B**, and **Cluster C**.
