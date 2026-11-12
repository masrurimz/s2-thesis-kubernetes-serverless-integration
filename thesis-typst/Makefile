# Typst build automation for ITS thesis template (master's only)
# Structure: thesis-typst/src/{thesis.typ,template.typ,content.typ,...}
.PHONY: master master-id check-id clean watch help

all: master

master:
	mkdir -p build
	typst compile src/thesis.typ build/thesis.pdf
	@echo "Output: build/thesis.pdf"

# Indonesian edition: --input lang=id selects content/<name>.id.typ for the
# body and switches headings, hyphenation and the CSL citation locale.
master-id:
	mkdir -p build
	typst compile --input lang=id src/thesis.typ build/thesis-id.pdf
	@echo "Output: build/thesis-id.pdf"

# Fail when an Indonesian chapter drops a citation, label, figure, table or
# number that its English source carries.
check-id:
	python3 check_id_parity.py

clean:
	rm -rf build
	@echo "Cleaned build/"

# Preview mode (for live preview)
watch:
	mkdir -p build
	typst watch src/thesis.typ build/thesis.pdf

# Help
help:
	@echo "ITS Thesis Typst Template (Master)"
	@echo "=================================="
	@echo ""
	@echo "Targets:"
	@echo "  master (default) - Build the English edition"
	@echo "  master-id        - Build the Indonesian edition"
	@echo "  check-id         - Compare each Indonesian chapter with its English source"
	@echo "  clean            - Remove build artifacts"
	@echo "  watch            - Watch & live preview"
	@echo ""
	@echo "Usage:"
	@echo "  make"
	@echo "  make watch"
	@echo ""
	@echo "Files to edit:"
	@echo "  src/thesis.typ   - Master's config + content"
	@echo "  src/template.typ - Layout and styling"
