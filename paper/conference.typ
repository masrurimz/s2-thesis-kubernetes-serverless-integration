// TIME-E 2026 conference version — 6-page IEEE two-column, A4, double-blind.
// Build: typst compile --root .. paper/conference.typ paper/conference.pdf
#import "ieee.typ": ieee
#import "sections/content.typ": *

#show: ieee.with(
  title: [Prediction-Gated Hybrid Routing Between Kubernetes and Serverless
    Backends Under Realistic Workload],
  // Double-blind review: no author names or affiliations in the manuscript.
  authors: (),
  abstract: abstract(extended: false),
  index-terms: index-terms(),
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#introduction(extended: false)
#related(extended: false)
#design(extended: false)
#methodology(extended: false)
#results(extended: false)
#discussion(extended: false)
#conclusion(extended: false)
