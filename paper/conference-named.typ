// Conference version with the author block, for venues that review single-blind
// and for the camera-ready. Same body as conference.typ.
// Build: cd paper && make conference-named
#import "ieee.typ": ieee
#import "authors.typ": authors
#import "sections/body.typ": abstract, body, keywords

#show: ieee.with(
  title: [Scaling Kubernetes Replicas with GRU Forecasts and Routing Overflow to Serverless],
  authors: authors,
  abstract: abstract,
  index-terms: keywords,
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#body(extended: false)
