# Paper figures

Exported from the thesis figure sources for the 6–7 page conference paper. Each file is one figure, rendered at 300 ppi for PNG and vector for SVG.

Regenerate from `thesis-typst/src`:

```bash
for spec in 1:fig01-control-loop 2:fig02-paired-p99 3:fig03-slo-violations \
            4:fig04-p99-boxplot 5:fig05-node-provisioning 6:fig06-monthly-cost \
            7:fig07-replication-forest; do
  p=${spec%%:*}; n=${spec##*:}
  typst compile --format png --ppi 300 --pages "$p" export-paper-figures.typ "figures/paper/$n.png"
  typst compile --format svg --pages "$p" export-paper-figures.typ "figures/paper/$n.svg"
done
```

| Figure | Shows | Source | Key numbers |
|---|---|---|---|
| fig01-control-loop | System architecture and the 15 s control loop: clients, HAProxy, monitoring, GRU server, routing daemon, both backends | `content/ch03-figures.typ` | Weighted routing via HAProxy Runtime API; Algorithm 1 routing plus Algorithm 2 scaling; GRU FastAPI on port 8090; Knative and K3s on one physical testbed |
| fig02-paired-p99 | Per-pair p99, S3 against S4, July paired batch (history), n = 5 | `2026-07-14_clarknet-tuned-paired-n5` | S3 235,6 / 192,2 / 151,4 / 164,0 / 199,2 ms; S4 101,4 / 104,9 / 100,5 / 155,7 / 167,4 ms; SLO line at 200 ms; p = 0,0312, the 1/32 design floor |
| fig03-slo-violations | SLO violations, July batch (history) and replication tier | `2026-07-14_clarknet-tuned-paired-n5` and `2026-08-09_clarknet-replay_032257` | July batch 656 against 130, a drop of 80,2 percent; replication tier per-run means 399,6 against 18,4 (five-run totals 1998 against 92) |
| fig04-p99-boxplot | Four-scenario p99 boxplot with 20 run points, n = 5 | `2026-08-09_clarknet-replay_032257` | Medians S1 112,7; S2 79,0; S3 151,6; S4 93,8 ms; SLO line at 200 ms |
| fig05-node-provisioning | Node CPU percent over time, with provisioning and consolidation markers | `2026-07-14_clarknet-tuned-paired-n5/raw/s3-hybrid-reactive_run1` | pending_detected 317,7 and 576,9 s; node_created 394,4 and 669,5 s; scale_down 762,2 s; node_deleted 763,7 s |
| fig06-monthly-cost | Monthly cost by scenario (n = 1 diagnostic) | `results/cost_analysis/cost_analysis_20260711_112337.json` | S1 132; S2 395; S3 147; S4 143 USD per month; July paired batch S3 = S4 = 163 USD |
| fig07-replication-forest | H2 forest plot, mean difference with 95 percent CI across batches | July batch and replication bundles | July batch −62,5 ms [−100,9; −26,2], p = 0,0312; RUN1 −4,0 [−57,8; +66,1], p = 0,436; RUN2 −58,0 [−161,5; −2,8], p = 0,062; RUN3 −52,5 [−102,6; −11,8], p = 0,032 |

Notes:

- The figure sources stay in `content/figures.typ` and `content/ch03-figures.typ`. Change a number there, then rerun the command above.
- `fig07` is a matplotlib PNG rendered by `uv run python -m analysis_cli.thesis_figures`; the harness embeds it at 420 pt.
- Captions for the paper are written in the paper, not baked into the images.
- Axis values are integers. The SLO annotation reads `SLO 200 ms`. The compilation reports no overflow, so no label is clipped.
