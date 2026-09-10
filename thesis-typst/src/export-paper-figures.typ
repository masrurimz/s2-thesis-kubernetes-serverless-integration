// Paper figure export harness.
// Renders each paper figure on its own page so it can be exported as PNG/SVG.
// Usage (from thesis-typst/src):
//   typst compile --format png --ppi 300 export-paper-figures.typ "figures/paper/fig-{p}.png"
//   typst compile --format svg export-paper-figures.typ "figures/paper/fig-{p}.svg"
// Page order: 1 control loop, 2 paired p99, 3 SLO violations, 4 p99 boxplot,
// 5 node provisioning, 6 monthly cost, 7 replication forest.

#import "content/ch03-figures.typ": fig-control-loop
#import "content/figures.typ": (
  fig-cost-comparison,
  fig-node-provisioning,
  fig-p99-boxplot,
  fig-paired-perpair,
  fig-slo-violations,
)

#set page(width: auto, height: auto, margin: 6pt)

#fig-control-loop()
#pagebreak()
#fig-paired-perpair()
#pagebreak()
#fig-slo-violations()
#pagebreak()
#fig-p99-boxplot()
#pagebreak()
#fig-node-provisioning()
#pagebreak()
#fig-cost-comparison()
#pagebreak()
#image("figures/fig04_6_replication_batches.png", width: 420pt)
