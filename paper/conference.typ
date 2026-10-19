// Conference version: six pages, IEEE two-column, A4, double-blind.
// Build: cd paper && make conference
#import "ieee.typ": ieee
#import "sections/body.typ": abstract, body, keywords

#show: ieee.with(
  title: [Forecast-Driven Replica Scaling in a Hybrid Kubernetes--Knative Deployment: \
    Architecture and Paired Evaluation],
  // Double-blind review: no author names or affiliations in the manuscript.
  authors: (),
  abstract: abstract,
  index-terms: keywords,
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#body(extended: false)
