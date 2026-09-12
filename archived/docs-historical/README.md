# Historical docs

Superseded documentation, moved here from `docs/` on 2026-09-12. Kept for provenance only. Do not follow these instructions.

| File | Was | Superseded | Current equivalent |
|------|-----|------------|--------------------|
| `02-setup-cluster.md` | `docs/getting-started/02-setup-cluster.md` | 2025-07-13 | Governed testbed lifecycle: `thesis infra setup`, `thesis infra ensure` (`uv run thesis infra --help`); walkthrough in `docs/getting-started/02-quick-start.md` |
| `03-deploying-services.md` | `docs/getting-started/03-deploying-services.md` | 2026-02-14 | `thesis infra deploy-app` deploys `test-app` to both clusters; walkthrough in `docs/getting-started/02-quick-start.md` |
| `04-teardown.md` | `docs/getting-started/04-teardown.md` | 2025-07-13 | `thesis infra teardown` |
| `CODEBASE-INVENTORY.md` | `docs/CODEBASE-INVENTORY.md` | 2026-01-14 | Repository map in the root `AGENTS.md` (workspace packages under `libs/` and `apps/`) |
| `IMPLEMENTATION_CROSSCHECK.md` | `docs/IMPLEMENTATION_CROSSCHECK.md` | 2026-01-15 | Root `AGENTS.md` module map; SLO truth in `apps/routing/routing/monitoring/slo_monitor.py`, spec in `docs/specs/` |

The three getting-started guides describe the abandoned Cluster A/B/C layout (`cluster-configs/`, PostgreSQL + MinIO + Rust app); that tree is preserved under `archived/cluster-configs/` and `archived/apps-rust/`.
