#!/usr/bin/env python3
"""Convert archived reference PDFs to markdown with YAML frontmatter.

The PDFs in ``docs/references/`` are the canonical archive. This script derives a
readable markdown copy of each into ``docs/references/md/`` so an agent or a
person can grep and read a paper without a PDF toolchain.

Frontmatter is assembled from two sources:

- ``REFERENCES.md`` supplies the curated fields (title, identifier, key insight)
  because that manifest is the reviewed record of what each paper is for.
- The PDF itself supplies the mechanical fields (page count, sha256, first-page
  text) so a mismatch between the manifest row and the archived object is
  visible rather than assumed.

Usage::

    uv run --with pymupdf4llm python docs/references/convert_to_markdown.py
    uv run --with pymupdf4llm python docs/references/convert_to_markdown.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REFERENCES_DIR = Path(__file__).resolve().parent
MANIFEST = REFERENCES_DIR / "REFERENCES.md"
BIBLIOGRAPHY = REFERENCES_DIR / "bibliography.yaml"
OUT_DIR = REFERENCES_DIR / "md"

# Manifest tables come in two layouts. The citation tables are
#   | **Title** — Subtitle | `file.pdf` | arxiv:1234.5678 | Key insight |
# and the methodology tables fold the filename into the identifier column:
#   | **Title** | arXiv:1234.5678 · `file.pdf` | Used for |
# so the filename is located anywhere in the row rather than in a fixed column.
FILE_IN_ROW = re.compile(r"`(?P<file>[^`]+\.pdf)`")
ARXIV_ID = re.compile(r"arxiv:\s*(?P<id>[\w.\-/]+)", re.IGNORECASE)
DOI_ID = re.compile(r"doi:\s*(?P<id>[\w.\-/]+)", re.IGNORECASE)
IDENT_IN_ROW = re.compile(
    r"(arxiv:\s*[\w.\-/]+|doi:\s*[\w.\-/]+|https?://\S+|(?<![\w./-])[\w-]+(?:\.[\w-]+)+/\S+)",
    re.IGNORECASE,
)
BARE_HOST = re.compile(r"^(?P<host>[\w-]+(?:\.[\w-]+)+/\S*)$")


def doi_of(identifier: str) -> str:
    m = DOI_ID.search(identifier or "")
    return m.group(1).rstrip(".,;") if m else ""


def arxiv_of(identifier: str) -> str:
    m = ARXIV_ID.search(identifier or "")
    return m.group(1).rstrip(".,;") if m else ""


def source_url(identifier: str) -> str:
    """Resolve a manifest identifier to a URL a reader can follow.

    The manifest records whichever identifier the paper actually has, so this
    normalises the three forms it uses — arXiv, DOI, and a bare or full URL —
    into one link. An identifier that is none of those (a venue name, say)
    yields an empty string rather than a guessed link.
    """
    ident = identifier.strip()
    if not ident:
        return ""
    if ident.startswith(("http://", "https://")):
        return ident.rstrip(").,")
    m = ARXIV_ID.search(ident)
    if m:
        return f"https://arxiv.org/abs/{m.group('id').rstrip('.,;')}"
    m = DOI_ID.search(ident)
    if m:
        return f"https://doi.org/{m.group('id').rstrip('.,;')}"
    m = BARE_HOST.match(ident)
    if m:
        return f"https://{m.group('host').rstrip(').,')}"
    return ""


def parse_manifest(text: str) -> dict[str, dict[str, str]]:
    """Return ``{pdf filename: {title, identifier, insight}}`` from every table."""
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        file_match = FILE_IN_ROW.search(line)
        if not file_match:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        title = cells[0].replace("**", "").strip()
        if title.lower().startswith(("paper", "dataset", "---")):
            continue
        ident = ""
        for cell in cells[1:]:
            found = IDENT_IN_ROW.search(cell)
            if found:
                ident = found.group(1).strip()
                break
        rows[file_match.group("file")] = {
            "title": title,
            "identifier": ident,
            "insight": cells[-1].strip(),
        }
    return rows


def split_title(title: str) -> tuple[str, str]:
    """Split a manifest title on the em dash into (short title, subtitle)."""
    for sep in (" — ", " – ", " - "):
        if sep in title:
            head, tail = title.split(sep, 1)
            return head.strip(), tail.strip()
    return title.strip(), ""


def yaml_str(value: str) -> str:
    """Quote a scalar for YAML, collapsing whitespace and escaping quotes."""
    flat = " ".join(value.split())
    return '"' + flat.replace("\\", "\\\\").replace('"', '\\"') + '"'


def first_page_text(pdf_path: Path) -> str:
    import pymupdf

    with pymupdf.open(pdf_path) as doc:
        if not doc.page_count:
            return ""
        return " ".join((doc[0].get_text() or "").split())


def load_bibliography() -> dict[str, dict]:
    """Read the curated record for each PDF. Missing file is an error, not a default."""
    import yaml

    if not BIBLIOGRAPHY.exists():
        raise SystemExit(f"{BIBLIOGRAPHY.name} is missing — run docs/references/fetch_bibliography.py first")
    data = yaml.safe_load(BIBLIOGRAPHY.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def convert(pdf_path: Path, meta: dict[str, str], bib: dict, out_dir: Path) -> dict[str, object]:
    import pymupdf
    import pymupdf4llm

    body = pymupdf4llm.to_markdown(str(pdf_path))
    with pymupdf.open(pdf_path) as doc:
        pages = doc.page_count

    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    head = first_page_text(pdf_path)[:200]
    url = source_url(meta["identifier"])

    # The bibliographic block comes from the registry-backed record; the archive
    # block is read off the file. Keeping them separate is the point: a reader
    # can cite from the first without trusting the second, and a mismatch between
    # them (a title that drifted, a year that disagrees) is visible.
    front = ["---", "# --- bibliographic record ---"]
    front.append(f"entry_type: {bib.get('entry_type', 'misc')}")
    front.append(f"title: {yaml_str(bib.get('title') or meta['title'])}")
    authors = bib.get("authors") or []
    if authors:
        front.append("authors:")
        front.extend(f"  - {yaml_str(a)}" for a in authors)
    else:
        front.append("authors: []")
    front.append(f"year: {int(bib.get('year') or 0)}")
    front.append(f"venue: {yaml_str(bib.get('venue', ''))}")
    front.append(f"volume: {yaml_str(bib.get('volume', ''))}")
    front.append(f"issue: {yaml_str(bib.get('issue', ''))}")
    front.append(f"pages: {yaml_str(bib.get('pages', ''))}")
    front.append(f"publisher: {yaml_str(bib.get('publisher', ''))}")
    if bib.get("published_venue") or bib.get("published_year"):
        front.append(f"published_venue: {yaml_str(bib.get('published_venue', ''))}")
        front.append(f"published_year: {int(bib.get('published_year') or 0)}")
    front.append(f"doi: {yaml_str(doi_of(meta['identifier']))}")
    front.append(f"arxiv: {yaml_str(arxiv_of(meta['identifier']))}")
    front.append(f"url: {yaml_str(url)}")
    front.append("")
    front.append("# --- archive record ---")
    front.append(f"source_pdf: {pdf_path.name}")
    front.append(f"source_sha256: {digest}")
    front.append(f"pdf_pages: {pages}")
    front.append(f"converted: {datetime.now(timezone.utc).date().isoformat()}")
    front.append(f"record_source: {bib.get('record_source', 'manual')}")
    if bib.get("review"):
        front.append(f"review: {yaml_str(bib['review'])}")
    front.append(f"key_insight: {yaml_str(meta['insight'])}")
    front.append(f"first_page: {yaml_str(head)}")
    front.append("---")
    front.append("")

    out_path = out_dir / (pdf_path.stem + ".md")
    out_path.write_text("\n".join(front) + body, encoding="utf-8")
    return {"file": out_path.name, "pages": pages, "chars": len(body), "sha256": digest, "url": url}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report drift without writing")
    args = ap.parse_args()

    rows = parse_manifest(MANIFEST.read_text(encoding="utf-8"))
    bib = load_bibliography()
    pdfs = sorted(REFERENCES_DIR.glob("*.pdf"))
    if not pdfs:
        print("no PDFs found", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(exist_ok=True)
    missing_meta: list[str] = []
    missing_bib: list[str] = []
    no_url: list[str] = []
    written = 0
    for pdf in pdfs:
        meta = rows.get(pdf.name)
        if meta is None:
            missing_meta.append(pdf.name)
            continue
        if pdf.name not in bib:
            missing_bib.append(pdf.name)
            continue
        out_path = OUT_DIR / (pdf.stem + ".md")
        if args.check:
            state = "present" if out_path.exists() else "MISSING"
            print(f"{state:8s} {pdf.name}")
            continue
        info = convert(pdf, meta, bib[pdf.name], OUT_DIR)
        written += 1
        if not info["url"]:
            no_url.append(f"{pdf.name} ({meta['identifier'] or 'no identifier'})")
        print(f"{info['pages']:>4d}p {info['chars']:>8d}c  {info['file']}")

    if missing_meta:
        print(f"\n{len(missing_meta)} PDF(s) with no manifest row:", file=sys.stderr)
        for name in missing_meta:
            print(f"  {name}", file=sys.stderr)
    if missing_bib:
        print(f"\n{len(missing_bib)} PDF(s) with no bibliography entry:", file=sys.stderr)
        for name in missing_bib:
            print(f"  {name}", file=sys.stderr)
    if missing_meta or missing_bib:
        return 1

    if no_url:
        print(f"\n{len(no_url)} paper(s) with no resolvable source_url:")
        for name in no_url:
            print(f"  {name}")

    if not args.check:
        print(f"\n{written} file(s) written to {OUT_DIR.relative_to(REFERENCES_DIR.parent.parent)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
