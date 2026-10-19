# Build both paper versions from paper/.
#   make            -> conference.pdf + journal.pdf
#   make conference -> six-page anonymous conference version
#   make journal    -> extended named-author version
#   make numbers    -> rederive numbers.json from the result bundles
#   make check      -> fail if numbers.json no longer matches the bundles
TYPST = typst compile --root ..
SOURCES = sections/body.typ sections/common.typ numbers.json ieee.typ ../thesis-typst/src/bibliography.bib

all: conference journal

conference: conference.pdf
journal: journal.pdf

conference.pdf: conference.typ $(SOURCES)
	$(TYPST) conference.typ conference.pdf

journal.pdf: journal.typ $(SOURCES)
	$(TYPST) journal.typ journal.pdf

numbers numbers.json: derive_numbers.py
	cd .. && uv run python paper/derive_numbers.py

check:
	cd .. && uv run python paper/derive_numbers.py --check

watch:
	typst watch --root .. conference.typ conference.pdf

clean:
	rm -f conference.pdf journal.pdf

.PHONY: all conference journal numbers check watch clean
