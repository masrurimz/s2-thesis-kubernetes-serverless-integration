// Journal version: same body with the extended sections, named authors.
// Build: cd paper && make journal
// The IEEE layout is a neutral manuscript format; apply the chosen journal's template on submission.
#import "ieee.typ": ieee
#import "authors.typ": authors
#import "sections/body.typ": abstract, body, keywords

#show: ieee.with(
  title: [Scaling Kubernetes Replicas with GRU Forecasts and Routing Overflow to Serverless: \
    Architecture and Paired Evaluation],
  authors: authors,
  abstract: abstract,
  index-terms: keywords,
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#body(extended: true)
