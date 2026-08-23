# Typst build automation for ITS thesis template (master's only)
# Structure: thesis-typst/src/{thesis.typ,template.typ,content.typ,...}
.PHONY: master master-id clean watch help

all: master

master:
	mkdir -p build
	@echo "Building Master's Thesis PDF..."
	@echo "Output: build/thesis.pdf"

# Indonesian body edition: same sources, --input lang=id switches text
# language, hyphenation, and CSL citation locale (see src/thesis.typ header)
master-id:
	mkdir -p build
	typst compile --input lang=id src/thesis.typ build/thesis-id.pdf
	@echo "Output: build/thesis-id.pdf"

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
	@echo "  master (default) - Build master's thesis PDF"
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
