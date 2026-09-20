// Extended journal version — same content, extended sections, named authors.
// Build: typst compile --root .. paper/journal.typ paper/journal.pdf
#import "ieee.typ": ieee
#import "sections/content.typ": *

#show: ieee.with(
  title: [Prediction-Gated Hybrid Routing Between Kubernetes and Serverless
    Backends: Design, Paired Evaluation, and the Role of Host-Load
    Instrumentation],
  authors: (
    (name: "Muhammad Zahid Masruri",
     department: [Department of Informatics],
     organization: [Institut Teknologi Sepuluh Nopember],
     location: [Surabaya, Indonesia],
     email: [masruri03\@gmail.com]),
    (name: "Royyana Muslim Ijtihadie",
     department: [Department of Informatics],
     organization: [Institut Teknologi Sepuluh Nopember],
     location: [Surabaya, Indonesia],
     email: [roy\@if.its.ac.id]),
  ),
  abstract: abstract(extended: true),
  index-terms: index-terms(),
  paper-size: "a4",
  bibliography: bibliography("../thesis-typst/src/bibliography.bib"),
)

#introduction(extended: true)
#related(extended: true)
#design(extended: true)
#methodology(extended: true)
#results(extended: true)
#discussion(extended: true)
#conclusion(extended: true)
