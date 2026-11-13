"""Reader-facing checks on the conference text of the paper.

Prints the reverse outline (first and last sentence of every paragraph), the skim
view (headings, captions and first sentences), sentences over the length limit,
and abbreviations used before they are defined. Run from the repository root:

    uv run python paper/readability.py outline
    uv run python paper/readability.py skim
    uv run python paper/readability.py lint [--json]
    uv run python paper/readability.py suspects [--body PATH] [--json]

`suspects` points at sentences with the patterns readers tripped on: a dangling "one",
a name repeated inside one sentence, an object placed before the thing it describes,
a sentence that shares nothing with the one before, packed clauses, and our own
shorthand. It finds candidates for a human to judge, not verdicts.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent
BODY = PAPER / "sections" / "body.typ"
COMMON = PAPER / "sections" / "common.typ"
TITLE_SOURCE = PAPER / "conference.typ"
MAX_WORDS = 25
KNOWN = {"AWS", "CPU", "CPUs", "HTTP", "API", "EKS", "I/O", "RMSE", "MAE", "USD", "CI", "S1", "S2", "S3", "S4", "RPS"}
SHORTHAND = (
    "decision factor",
    "envelope",
    "pod-seconds",
    "loaded-host",
    "scenario batch",
    "confirmatory",
    "node tier",
    "set delay",
    "hold",
    "eligible",
    "proactive",
)
LINKS = {
    "this",
    "these",
    "that",
    "those",
    "it",
    "its",
    "they",
    "their",
    "both",
    "each",
    "the",
    "so",
    "thus",
    "therefore",
    "however",
    "because",
    "since",
    "while",
    "although",
    "also",
    "first",
    "second",
    "third",
    "finally",
    "then",
    "instead",
    "here",
    "there",
    "such",
    "in",
    "for",
    "once",
    "when",
    "if",
    "as",
    "our",
    "we",
}
STOP = {
    "about",
    "after",
    "also",
    "because",
    "before",
    "between",
    "could",
    "every",
    "from",
    "have",
    "into",
    "more",
    "only",
    "other",
    "than",
    "that",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "does",
    "each",
    "same",
    "both",
}


def _drop_extended(text: str) -> str:
    out, i = [], 0
    while (j := text.find("#if extended [", i)) != -1:
        out.append(text[i:j])
        depth, k = 0, j + len("#if extended ")
        while k < len(text):
            depth += {"[": 1, "]": -1}.get(text[k], 0)
            k += 1
            if depth == 0:
                break
        i = k
    out.append(text[i:])
    return "".join(out)


def _plain(text: str) -> str:
    text = re.sub(r"#[A-Z]\.[\w.]+", "N", text)
    text = re.sub(r"\$[^$]*\$", "X", text)
    text = re.sub(r"@(sec|tab|fig|alg):\w+", "Section", text)
    text = re.sub(r"\s?@[\w-]+", "", text)
    text = re.sub(r"<[\w:]+>", "", text)
    text = text.replace("~", " ").replace("\\[", "[").replace("\\]", "]").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def _sentences(par: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.?!])\s+(?=[A-Z(])", par) if s]


def paragraphs(source: Path = BODY) -> list[tuple[str, str]]:
    src = source.read_text()
    abstract = src.split("#let abstract = [", 1)[1].split("\n]\n", 1)[0]
    body = _drop_extended(src.split("#let body(extended: false) = [", 1)[1])
    pars: list[tuple[str, str]] = [("Abstract", _plain(abstract))]
    section, current = "", []

    def flush() -> None:
        text = _plain(re.sub(r"^\*[^*]+\*\s*", "", " ".join(current)))
        if text and text not in {"]", "N"}:
            pars.append((section, text))
        current.clear()

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#tab-", "#fig-", "#alg-", "//")):
            flush()
        elif stripped.startswith("="):
            flush()
            section = _plain(stripped.lstrip("= "))
        else:
            current.append(stripped)
    flush()
    return pars


def captions() -> list[str]:
    return [_plain(c) for c in re.findall(r"caption: \[(.*?)\],?\n", COMMON.read_text())]


def lint() -> dict[str, list]:
    long, undefined, seen = [], [], set()
    for section, par in paragraphs():
        for defined in re.findall(r"\(([A-Za-z0-9-]{2,})\)", par):
            seen.add(defined)
        for s in _sentences(par):
            words = len(s.split())
            if words > MAX_WORDS:
                long.append({"section": section, "words": words, "sentence": s})
            for tok in re.findall(r"\b[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*\b", s):
                if tok not in seen and tok not in KNOWN and f"({tok})" not in s:
                    undefined.append({"section": section, "abbreviation": tok, "sentence": s})
                seen.add(tok)
    return {"long_sentences": long, "used_before_defined": undefined}


def _stems(text: str) -> set[str]:
    return {w[:5] for w in re.findall(r"[a-z][a-z-]{3,}", text.lower()) if w not in STOP}


def suspects(body: Path = BODY) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def flag(section: str, kind: str, sentence: str, detail: str) -> None:
        rows.append({"section": section, "kind": kind, "detail": detail, "sentence": sentence})

    for section, par in paragraphs(body):
        previous = ""
        for s in _sentences(par):
            if re.search(r"\b(from|use|uses|with|without|has|have|need|needs) one\b(?=[.,;)])", s):
                flag(section, "referent", s, '"one" with no noun after it')
            names = re.findall(r"\b[A-Z][a-z]+[A-Z]?\w*\b", s[1:])
            repeated = sorted({n for n in names if names.count(n) > 1 and n not in {"Section", "The"}})
            if repeated:
                flag(section, "repeat-name", s, f"{', '.join(repeated)} twice in one sentence")
            if m := re.search(r"\b(send|sends|sent|give|gives|route|routes|add|adds) to [\w-]+ (the|a|an|any) ", s):
                flag(section, "word-order", s, f'object comes after "{m.group(0).strip()}"')
            first = s.split()[0].lower().strip(",")
            if previous and first not in LINKS and not (_stems(" ".join(s.split()[:8])) & _stems(previous)):
                flag(section, "no-link", s, "opening words share nothing with the sentence before")
            clauses = s.count(",") + len(re.findall(r"\b(and|but|while|whereas|because|so|which|that)\b", s))
            if clauses >= 7:
                flag(section, "packed", s, f"{clauses} clause markers")
            for term in SHORTHAND:
                if re.search(rf"\b{re.escape(term)}\b", s, re.IGNORECASE):
                    flag(section, "shorthand", s, term)
            previous = s
    return rows


def main(argv: list[str]) -> int:
    mode = argv[0] if argv else "lint"
    if mode == "outline":
        for section, par in paragraphs():
            s = _sentences(par)
            print(f"[{section}]\n  first: {s[0]}\n  last:  {s[-1]}\n")
    elif mode == "skim":
        title = re.search(r"title: \[(.*?)\]", TITLE_SOURCE.read_text())
        print(f"TITLE: {title.group(1) if title else ''}\n")
        last = None
        for section, par in paragraphs():
            if section == "Abstract":
                print(f"ABSTRACT: {par}\n")
                continue
            if section != last:
                print(f"\n## {section}")
                last = section
            print(f"- {_sentences(par)[0]}")
        print("\nCAPTIONS:")
        for c in captions():
            print(f"- {c}")
    elif mode == "lint":
        report = lint()
        if "--json" in argv:
            print(json.dumps(report, separators=(",", ":")))
        else:
            for kind, rows in report.items():
                print(f"{kind}: {len(rows)}")
                for r in rows:
                    print("  " + " | ".join(str(v) for v in r.values()))
    elif mode == "suspects":
        body = Path(argv[argv.index("--body") + 1]) if "--body" in argv else BODY
        rows = suspects(body)
        if "--json" in argv:
            print(json.dumps(rows, separators=(",", ":")))
        else:
            print(f"{len(rows)} suspect(s)")
            for r in rows:
                print(" | ".join(r.values()))
    else:
        print("usage: readability.py outline|skim|lint [--json]|suspects [--body PATH] [--json]", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
