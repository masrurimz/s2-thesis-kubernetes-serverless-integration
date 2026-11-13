// Conference version with the author block, for venues that review single-blind
// and for the camera-ready. Same body as conference.typ.
// Build: cd paper && make conference-named
#import "ieee.typ": ieee
#import "authors.typ": authors
#import "sections/body.typ": abstract, body, keywords

#show: ieee.with(
  title: [Does a GRU Forecast Still Help Kubernetes Scaling When Serverless Absorbs Overflow?],
  authors: authors,
  abstract: abstract,
  index-terms: keywords,
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#body(extended: false)
