#!/usr/bin/env python3
"""Check that each Indonesian chapter still says what its English source says.

The Indonesian edition keeps its body in `src/content/<name>.id.typ`, a translation of
`src/content/<name>.typ`. A translation may reword anything, but it must carry the same
citations, labels, heading keys, figures, tables, code blocks and numbers. This script
compares those per file pair and prints what one side has that the other lacks.

Numbers compare by their digits, so `0.307` matches `0,307` and `1,998` matches `1.998`.
Dates compare as day, month, year, so `2026-08-09`, `August 9, 2026` and `9 Agustus 2026` match.

    python3 check_id_parity.py            # every pair
    python3 check_id_parity.py ch04-results
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

CONTENT = Path(__file__).parent / "src" / "content"

PATTERNS = {
    "citation": re.compile(r"(?<![\w@])@([A-Za-z][\w:-]*\w)"),
    "label": re.compile(r"<([A-Za-z][\w:-]*)>"),
    "heading key": re.compile(r'H\("([^"]+)"\)'),
    "code block": re.compile(r"`[^`\n]+`"),
}
COUNTED = {"figure(": "figure", "table(": "table", "image(": "image", "#import": "import"}
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
MONTHS = (
    ("January", "Januari"),
    ("February", "Februari"),
    ("March", "Maret"),
    ("April", "April"),
    ("May", "Mei"),
    ("June", "Juni"),
    ("July", "Juli"),
    ("August", "Agustus"),
    ("September", "September"),
    ("October", "Oktober"),
    ("November", "November"),
    ("December", "Desember"),
)
MONTH_NUMBER = {name: str(i) for i, pair in enumerate(MONTHS, 1) for name in pair}
MONTH_NAME = re.compile(r"\b(" + "|".join(sorted(MONTH_NUMBER, key=len, reverse=True)) + r")\b")


def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!:)//.*$", "", line) for line in text.splitlines())


def numbers(text: str) -> Counter:
    text = PATTERNS["code block"].sub(" ", text)
    text = ISO_DATE.sub(lambda m: f"{m[3]} {m[2]} {m[1]}", text)
    text = MONTH_NAME.sub(lambda m: f" {MONTH_NUMBER[m[1]]} ", text)
    return Counter(re.sub(r"[.,]", "", m).lstrip("0") or "0" for m in NUMBER.findall(text))


def facts(path: Path) -> dict[str, Counter]:
    text = strip_comments(path.read_text(encoding="utf-8"))
    out = {name: Counter(p.findall(text)) for name, p in PATTERNS.items()}
    out["structure"] = Counter({label: text.count(token) for token, label in COUNTED.items()})
    out["number"] = numbers(text)
    return out


def compare(name: str) -> list[str]:
    en, idn = CONTENT / f"{name}.typ", CONTENT / f"{name}.id.typ"
    a, b = facts(en), facts(idn)
    problems = []
    for kind in a:
        only_en, only_id = a[kind] - b[kind], b[kind] - a[kind]
        if only_en:
            problems.append(f"  {kind} only in English: {dict(only_en)}")
        if only_id:
            problems.append(f"  {kind} only in Indonesian: {dict(only_id)}")
    return problems


def main() -> int:
    names = sys.argv[1:] or sorted(p.name.removesuffix(".id.typ") for p in CONTENT.glob("*.id.typ"))
    failed = 0
    for name in names:
        problems = compare(name)
        print(f"{name}: {'ok' if not problems else f'{len(problems)} difference(s)'}")
        for line in problems:
            print(line)
        failed += bool(problems)
    print(f"{len(names) - failed} of {len(names)} file pair(s) match")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
