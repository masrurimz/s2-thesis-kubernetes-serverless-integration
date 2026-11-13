// Journal version: same body with the extended sections, named authors.
// Build: cd paper && make journal
// The IEEE layout is a neutral manuscript format; apply the chosen journal's template on submission.
#import "ieee.typ": ieee
#import "authors.typ": authors
#import "sections/body.typ": abstract, body, keywords

#show: ieee.with(
  title: [Does a GRU Forecast Still Help Kubernetes Scaling When Serverless Absorbs Overflow? \
    A Paired Evaluation],
  authors: authors,
  abstract: abstract,
  index-terms: keywords,
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#body(extended: true)
