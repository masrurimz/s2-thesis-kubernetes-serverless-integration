// Journal version: same body with the extended sections, named authors.
// Build: cd paper && make journal
// The IEEE layout is a neutral manuscript format; apply the chosen journal's template on submission.
#import "ieee.typ": ieee
#import "sections/body.typ": abstract, body, keywords

#show: ieee.with(
  title: [Forecast-Driven Replica Scaling in a Hybrid Kubernetes--Knative Deployment: \
    Architecture and Paired Evaluation],
  authors: (
    (
      name: "Muhammad Zahid Masruri",
      department: [Department of Informatics],
      organization: [Institut Teknologi Sepuluh Nopember],
      location: [Surabaya, Indonesia],
      email: "masruri03@gmail.com",
    ),
    (
      name: "Royyana Muslim Ijtihadie",
      department: [Department of Informatics],
      organization: [Institut Teknologi Sepuluh Nopember],
      location: [Surabaya, Indonesia],
      email: "roy@if.its.ac.id",
    ),
  ),
  abstract: abstract,
  index-terms: keywords,
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#body(extended: true)
