# Typst build automation for ITS thesis template (master's only)
# Structure: thesis-typst/src/{thesis.typ,template.typ,content.typ,...}
.PHONY: master clean watch help

all: master

master:
	mkdir -p build
	@echo "Building Master's Thesis PDF..."
	typst compile src/thesis.typ build/thesis.pdf
	@echo "Output: build/thesis.pdf"

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
