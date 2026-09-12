"""The half of a command's output a program reads instead of a person.

Three rules live here, so they are stated once and applied everywhere:

* **One line of JSON.** `--json` prints `json.dumps(..., separators=(",", ":"))`, not the
  indented form. Pretty-printing costs 27% to 40% more tokens on this repository's own
  payloads (measured against the evidence registry: 39,816 vs 28,982 tokens for the same
  142 entries) and buys a parser nothing. A person who wants it readable pipes through
  `jq .`.
* **Plain `print`, never a `rich` console.** A rich console soft-wraps at the terminal
  width, which corrupts a payload mid-token when the line is long.
* **A next step.** A command that answers a question says what to run with the answer.

Truncation carries its own size and its own escape hatch, so a long cell cannot quietly
eat an agent's budget and an agent cannot mistake a truncated value for a whole one.
"""

from __future__ import annotations

import json
from typing import Any, Sequence

DEFAULT_TRUNCATE = 120


def json_line(payload: Any) -> str:
    """The payload as one line of JSON — the form `--json` prints."""
    return json.dumps(payload, separators=(",", ":"), default=str)


def print_json(payload: Any) -> None:
    """Print the payload as one line of JSON."""
    print(json_line(payload))


def print_next(steps: Sequence[str]) -> None:
    """Print the commands that follow from this result, one per line.

    Real paths are carried through when the command has them; only values the caller
    must choose stay as placeholders, like `<bundle>`.
    """
    for step in steps:
        print(f"next: {step}")


def truncate(text: str, limit: int = DEFAULT_TRUNCATE, *, full: bool = False) -> str:
    """Cut `text` to `limit` characters, naming the real length and the way to see it."""
    if full or len(text) <= limit:
        return text
    return f"{text[:limit]}… (truncated, {len(text)} chars — use --full)"
