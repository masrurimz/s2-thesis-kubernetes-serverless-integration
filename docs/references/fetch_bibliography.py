#!/usr/bin/env python3
"""Build ``docs/references/bibliography.yaml`` from the authoritative registries.

The bibliographic record for each archived paper comes from the registry that
owns its identifier, not from reading the PDF:

- a DOI resolves through **Crossref** (``api.crossref.org``)
- an arXiv ID resolves through the **arXiv abstract page**, whose ``citation_*``
  meta tags carry title, authors and date. The arXiv *API* is the obvious choice
  and the wrong one: it answers ``429 Rate exceeded`` after a handful of calls
  and stays that way, while the abs page has no such limit.

Both are deterministic and citable, which an extraction pass over a first page is
not: a language model asked for a venue will happily return a nearby string that
appears in the text (a department name, a co-author, the word "misc"), and no
cheap substring check tells that apart from a real answer.

``bibliography.yaml`` is the committed artifact and is meant to be read and
hand-corrected — a registry record can be thin (a preprint with no journal
reference) or wrong, and the file carries a ``review`` field for those cases.

The run checkpoints after **every** record and resumes by default, so a timeout
on paper 40 of 55 costs one paper, not the run.

Usage::

    uv run python docs/references/fetch_bibliography.py            # fetch, resuming
    uv run python docs/references/fetch_bibliography.py --force    # refetch all
    uv run python docs/references/fetch_bibliography.py --dry-run  # report only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

REFERENCES_DIR = Path(__file__).resolve().parent
MANIFEST = REFERENCES_DIR / "REFERENCES.md"
OUT = REFERENCES_DIR / "bibliography.yaml"

USER_AGENT = "thesis-references/1.0 (offline archive; mailto:research@example.org)"
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
ARXIV_DELAY_SEC = 1.0  # the abs page is not rate-limited, but be a good citizen

FILE_IN_ROW = re.compile(r"`(?P<file>[^`]+\.pdf)`")
ARXIV_ID = re.compile(r"arxiv:\s*(?P<id>[\w.\-/]+)", re.IGNORECASE)
DOI_ID = re.compile(r"doi:\s*(?P<id>[\w.\-/]+)", re.IGNORECASE)
URL_ID = re.compile(r"https?://\S+")


# ── HTTP ─────────────────────────────────────────────────────────────────────


def _fetch(url: str, timeout: int, accept: str, ua: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch(url: str, accept: str, ua: str = USER_AGENT, attempts: int = 3, timeout: int = 30) -> str:
    """GET with backoff. Raises on the last failure rather than returning junk."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return _fetch(url, timeout, accept, ua)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last = exc
            if attempt < attempts - 1:
                time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"gave up after {attempts} attempts: {last}")


# ── Manifest ─────────────────────────────────────────────────────────────────


def parse_manifest(text: str) -> dict[str, str]:
    """Return ``{pdf filename: identifier}`` from every table row."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        m = FILE_IN_ROW.search(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        ident = ""
        for cell in cells[1:]:
            found = ARXIV_ID.search(cell) or DOI_ID.search(cell) or URL_ID.search(cell)
            if found:
                ident = found.group(0)
                break
        out[m.group("file")] = ident
    return out


# ── Registries ───────────────────────────────────────────────────────────────


def from_crossref(doi: str) -> dict:
    """Map a Crossref work onto the record shape."""
    msg = json.loads(fetch(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", "application/json"))["message"]
    authors = [
        " ".join(p for p in (a.get("given", ""), a.get("family", "")) if p).strip() for a in msg.get("author", [])
    ]
    issued = (msg.get("issued", {}).get("date-parts") or [[0]])[0]
    return {
        "entry_type": "article" if msg.get("type") == "journal-article" else "inproceedings",
        "title": (msg.get("title") or [""])[0].strip(),
        "authors": [a for a in authors if a],
        "year": int(issued[0] or 0),
        "venue": (msg.get("container-title") or [""])[0].strip(),
        "volume": str(msg.get("volume") or ""),
        "issue": str(msg.get("issue") or ""),
        "pages": str(msg.get("page") or ""),
        "publisher": str(msg.get("publisher") or ""),
        "published_venue": "",
        "published_year": 0,
        "record_source": "crossref",
    }


def _meta(html: str, name: str) -> str:
    m = re.search(rf'<meta\s+name="{name}"\s+content="(.*?)"', html, re.S)
    return " ".join(m.group(1).split()) if m else ""


def _flip_name(name: str) -> str:
    """arXiv writes 'Family, Given'; the rest of the record uses 'Given Family'."""
    parts = [p.strip() for p in name.split(",", 1)]
    return f"{parts[1]} {parts[0]}" if len(parts) == 2 and parts[0] and parts[1] else name.strip()


def from_arxiv(arxiv_id: str) -> dict:
    """Map an arXiv abstract page onto the record shape."""
    html = fetch(f"https://arxiv.org/abs/{urllib.parse.quote(arxiv_id)}", "text/html", ua=BROWSER_UA)
    title = _meta(html, "citation_title")
    if not title:
        raise ValueError(f"no citation_title on the abs page for {arxiv_id}")
    authors = [_flip_name(a) for a in re.findall(r'name="citation_author"\s+content="(.*?)"', html)]
    date = _meta(html, "citation_date")
    journal = _meta(html, "citation_journal_title")
    return {
        "entry_type": "misc",
        "title": title,
        "authors": authors,
        "year": int(date[:4]) if date[:4].isdigit() else 0,
        "venue": journal or "arXiv preprint",
        "volume": _meta(html, "citation_volume"),
        "issue": _meta(html, "citation_issue"),
        "pages": "",
        "publisher": "",
        "published_venue": journal,
        "published_year": 0,
        "record_source": "arxiv",
    }


# ── Persistence ──────────────────────────────────────────────────────────────


def load_existing() -> dict[str, dict]:
    if not OUT.exists():
        return {}
    data = yaml.safe_load(OUT.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def write_atomic(records: dict[str, dict]) -> None:
    """Write the whole file via a temp file + rename, so a crash never truncates it."""
    body = to_yaml(records)
    fd, tmp = tempfile.mkstemp(dir=OUT.parent, prefix=".bibliography-", suffix=".yaml")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(tmp, OUT)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def yaml_scalar(value: object) -> str:
    flat = " ".join(str(value).split())
    return '"' + flat.replace("\\", "\\\\").replace('"', '\\"') + '"'


HEADER = """# Bibliographic record for every archived reference PDF.
#
# Generated by docs/references/fetch_bibliography.py from Crossref (DOIs) and the
# arXiv abstract pages (arXiv IDs) — the registries that own the identifiers, not
# an extraction pass over the PDFs. Hand-correct freely: a registry record can be
# thin (a preprint with no journal reference) or wrong, and `review` marks the
# entries that need a human eye. convert_to_markdown.py reads this file.
#
#   entry_type      article | inproceedings | misc
#   year            year of the version held in the archive
#   published_*     the venue of record when the archive holds a preprint
#   record_source   which registry answered (crossref | arxiv | manual)
#   review          non-empty means a person should confirm this entry
"""


def to_yaml(records: dict[str, dict]) -> str:
    lines = [HEADER]
    for name in sorted(records):
        r = records[name]
        lines.append(f"{yaml_scalar(name)}:")
        lines.append(f"  entry_type: {r.get('entry_type', 'misc')}")
        lines.append(f"  title: {yaml_scalar(r.get('title', ''))}")
        authors = r.get("authors") or []
        if authors:
            lines.append("  authors:")
            lines.extend(f"    - {yaml_scalar(a)}" for a in authors)
        else:
            lines.append("  authors: []")
        lines.append(f"  year: {int(r.get('year') or 0)}")
        lines.append(f"  venue: {yaml_scalar(r.get('venue', ''))}")
        lines.append(f"  volume: {yaml_scalar(r.get('volume', ''))}")
        lines.append(f"  issue: {yaml_scalar(r.get('issue', ''))}")
        lines.append(f"  pages: {yaml_scalar(r.get('pages', ''))}")
        lines.append(f"  publisher: {yaml_scalar(r.get('publisher', ''))}")
        lines.append(f"  published_venue: {yaml_scalar(r.get('published_venue', ''))}")
        lines.append(f"  published_year: {int(r.get('published_year') or 0)}")
        lines.append(f"  record_source: {r.get('record_source', 'manual')}")
        lines.append(f"  review: {yaml_scalar(r.get('review', ''))}")
        lines.append("")
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="refetch records already in the file")
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()

    idents = parse_manifest(MANIFEST.read_text(encoding="utf-8"))
    pdfs = sorted(p.name for p in REFERENCES_DIR.glob("*.pdf"))
    records = {} if args.force else load_existing()
    cached = len(records)
    failures: list[tuple[str, str]] = []

    for i, name in enumerate(pdfs, 1):
        if name in records:
            continue
        ident = idents.get(name, "")
        doi_m = DOI_ID.search(ident)
        arxiv_m = ARXIV_ID.search(ident)
        try:
            if doi_m:
                rec = from_crossref(doi_m.group(1))
            elif arxiv_m:
                rec = from_arxiv(arxiv_m.group(1))
                time.sleep(ARXIV_DELAY_SEC)
            else:
                rec = {
                    "entry_type": "misc",
                    "title": "",
                    "authors": [],
                    "year": 0,
                    "venue": "",
                    "volume": "",
                    "issue": "",
                    "pages": "",
                    "publisher": "",
                    "published_venue": "",
                    "published_year": 0,
                    "record_source": "manual",
                    "review": "no DOI or arXiv ID in the manifest; fill by hand",
                }
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError, RuntimeError) as exc:
            failures.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"[{i:2d}/{len(pdfs)}] FAIL  {name[:52]:52s} {exc}", flush=True)
            continue

        thin = [f for f in ("title", "authors", "year", "venue") if not rec.get(f)]
        if thin:
            rec["review"] = "registry returned no " + ", ".join(thin)
        records[name] = rec
        if not args.dry_run:
            write_atomic(records)
        print(
            f"[{i:2d}/{len(pdfs)}] {rec['record_source']:>8s}  {name[:52]:52s} "
            f"{rec.get('year') or '?':>5}  {str(rec.get('venue', ''))[:30]}",
            flush=True,
        )

    thin = [n for n, r in records.items() if r.get("review")]
    print(f"\n{len(records)}/{len(pdfs)} records ({cached} were already on disk); {len(thin)} flagged for review")
    for n in thin:
        print(f"  {n[:52]:52s} {records[n]['review']}")
    if failures:
        print(f"\n{len(failures)} failure(s) — rerun to retry just these:", file=sys.stderr)
        for name, err in failures:
            print(f"  {name}: {err}", file=sys.stderr)
    if not args.dry_run:
        print(f"\nwrote {OUT.relative_to(REFERENCES_DIR.parent.parent)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
