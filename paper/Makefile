# Build both paper versions. Run from repo root or this dir.
#   make            -> conference.pdf + journal.pdf
#   make conference -> TIME-E 6-page anonymous version
#   make journal    -> extended named-author version
TYPST = typst compile --root ..

all: conference journal

conference: conference.pdf
journal: journal.pdf

conference.pdf: conference.typ sections/content.typ ieee.typ ../thesis-typst/src/bibliography.bib
	$(TYPST) conference.typ conference.pdf

journal.pdf: journal.typ sections/content.typ ieee.typ ../thesis-typst/src/bibliography.bib
	$(TYPST) journal.typ journal.pdf

watch:
	typst watch --root .. conference.typ conference.pdf

clean:
	rm -f conference.pdf journal.pdf

.PHONY: all conference journal watch clean
