"""Documentation drift guard: every documented ``uv run thesis`` command must exist.

Walks the repository's markdown files, extracts ``uv run thesis <path> <flags>``
invocations from fenced code blocks and inline code, and resolves each one
against the CLI's own typer app in process. A doc that names a command the CLI
no longer registers, or a flag the command no longer accepts, fails here.

The in-process walk is the seam: ``apps/cli/cli/main.py`` registers all
sub-apps at import time (each guarded by ``try/except ImportError``), so
importing :mod:`cli.main` and walking ``typer.main.get_command(app)`` yields
the full command tree in milliseconds. This typer version vendors its click
fork as ``typer._click``, so the stock ``click.Group`` isinstance check does
not hold; group membership is detected by the ``commands`` attribute instead.

Not covered, deliberately: the ``thesis-*`` console scripts and ``python -m``
forms are separate entry points, and shell metacharacter lines (pipes,
redirects, command chains, variable expansion) are skipped because their
argument boundaries cannot be parsed reliably. Lines whose unparsable content
is only a ``<placeholder>`` argument are parsed; the placeholder value is
exempt but the command chain must still resolve.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import typer.main
from cli.main import app

REPO_ROOT = Path(__file__).resolve().parents[3]

# Markdown roots to walk: the repo root recursively covers docs/, apps/, libs/,
# results/, data/ and the top-level files in one pass. Excluded trees are the
# frozen archived/ snapshot, VCS/venv internals, and results/experiments/ (run
# output, not documentation).
EXCLUDED_DIR_NAMES = {"archived", ".git", ".venv", "node_modules", "__pycache__"}
EXCLUDED_PARTS_PREFIX = ("results", "experiments")

COMMAND_RE = re.compile(r"uv\s+run\s+thesis\s+(?P<rest>[^\n`]+)")
COMMENT_RE = re.compile(r"\s+#.*$")
PLACEHOLDER_RE = re.compile(r"^<[\w][\w.-]*>$")
# Tokens that make a line unparseable when they are not placeholders: shell
# pipes, redirects, command chaining, and variable expansion.
META_CHARS = set("|&$<>;")

# Deliberately illustrative placeholder arguments seen in the docs. The command
# chain that carries them must still resolve; only the argument value is exempt
# from checking. A new placeholder form in a doc makes this set fail first, so
# adding one is a conscious decision.
ALLOWED_PLACEHOLDERS = {
    "<bundle>",  # e.g. AGENTS.md: thesis analysis runs results/experiments/phase-b/<bundle>
    "<experiment-folder>",  # e.g. AGENTS.md: thesis analysis cost --experiment-dir .../<experiment-folder>
    "<action>",  # libs/infra/AGENTS.md: thesis infra cluster <action> (positional: create, delete, status)
    "...",  # e.g. results/README.md: thesis experiment run ...  (ellipsis, more args implied)
}

# Click adds --help at parse time rather than declaring it in params, so every
# command accepts it even though it never appears in ``cmd.params``.
IMPLICIT_FLAGS = {"--help"}


def _iter_markdown_files() -> list[Path]:
    files = [
        p
        for p in REPO_ROOT.rglob("*.md")
        if not (set(p.relative_to(REPO_ROOT).parts[:-1]) & EXCLUDED_DIR_NAMES)
        and not p.relative_to(REPO_ROOT).parts[:2] == EXCLUDED_PARTS_PREFIX
    ]
    return sorted(files)


def _logical_lines(text: str) -> list[tuple[int, str]]:
    """Join backslash continuations; yield (1-based start line, logical line)."""
    out: list[tuple[int, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        start = i
        buf = lines[i]
        while buf.rstrip().endswith("\\") and i + 1 < len(lines):
            buf = buf.rstrip()[:-1] + " " + lines[i + 1].lstrip()
            i += 1
        out.append((start + 1, buf))
        i += 1
    return out


def _accepted_flags(cmd: object) -> set[str]:
    return {
        opt for param in getattr(cmd, "params", []) for opt in [*param.opts, *param.secondary_opts]
    } | IMPLICIT_FLAGS


def _tokenize(rest: str) -> list[str] | None:
    """Tokenize a command tail; None when the line is not safely parseable."""
    line = COMMENT_RE.sub("", rest)
    try:
        tokens = shlex.split(line)
    except ValueError:
        # Unbalanced quotes: not parseable, skip.
        return None
    scrubbed = []
    for token in tokens:
        if PLACEHOLDER_RE.match(token) or token in ALLOWED_PLACEHOLDERS:
            scrubbed.append(token)
        elif set(token) & META_CHARS:
            # Redirect, pipe, chain, or expansion outside a placeholder: the
            # argument boundaries cannot be trusted.
            return None
        else:
            scrubbed.append(token)
    return scrubbed


def _walk_chain(root: object, tokens: list[str]) -> tuple[list[str], object, list[str]]:
    """Consume the longest leading token run that names real subcommands."""
    node = root
    chain: list[str] = []
    rest = tokens
    while rest:
        subs = getattr(node, "commands", None) or {}
        if rest[0].startswith("-") or rest[0] not in subs:
            break
        node = subs[rest[0]]
        chain.append(rest[0])
        rest = rest[1:]
    return chain, node, rest


def _check_invocation(root: object, rel: Path, lineno: int, rest: str) -> list[str]:
    """Return a failure message list for one documented invocation."""
    tokens = _tokenize(rest)
    if tokens is None:
        return []
    chain, node, remaining = _walk_chain(root, tokens)

    chain_label = f"thesis {' '.join(chain)}".strip()
    is_group = hasattr(node, "commands")
    accepted = _accepted_flags(node)
    subcommands = sorted((getattr(node, "commands", None) or {}).keys())

    failures: list[str] = []
    placeholders = set()
    for token in remaining:
        if PLACEHOLDER_RE.match(token) or token in ALLOWED_PLACEHOLDERS:
            placeholders.add(token)
        elif token.startswith("-"):
            name = token.split("=", 1)[0]
            if name not in accepted:
                failures.append(
                    f"{rel}:{lineno}: flag '{name}' is not accepted by '{chain_label}'; accepted: {sorted(accepted)}"
                )
        elif is_group:
            # No group in this CLI takes positional arguments, so a bare word
            # after one is a command that no longer exists (or never did).
            failures.append(
                f"{rel}:{lineno}: '{token}' is not a subcommand of '{chain_label}'; subcommands are {subcommands}"
            )
        # A bare word after a leaf command is a positional argument value;
        # values are not checked.

    unknown_placeholders = placeholders - ALLOWED_PLACEHOLDERS
    if unknown_placeholders:
        failures.append(
            f"{rel}:{lineno}: placeholder argument(s) {sorted(unknown_placeholders)} in '{chain_label}' "
            f"are not in ALLOWED_PLACEHOLDERS; add them there if the example is deliberately illustrative"
        )
    return failures


def _check_all_docs() -> tuple[list[str], int]:
    root = typer.main.get_command(app)
    failures: list[str] = []
    checked = 0
    for path in _iter_markdown_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, logical in _logical_lines(text):
            for match in COMMAND_RE.finditer(logical):
                checked += 1
                failures.extend(_check_invocation(root, path.relative_to(REPO_ROOT), lineno, match["rest"]))
    return failures, checked


def test_documented_thesis_commands_resolve() -> None:
    """Every `uv run thesis <path> <flags>` in the markdown docs must resolve."""
    failures, _checked = _check_all_docs()
    assert not failures, "\n".join(["Documented commands drifted from the CLI: ", *failures])


def test_doc_walk_is_not_vacuous() -> None:
    """The walker must find documented commands; zero means the scan broke.

    If this fails after an honest docs cleanup, lower the floor, do not delete
    the test: a walker that finds nothing would pass every drift check.
    """
    _failures, checked = _check_all_docs()
    assert checked >= 20, f"expected dozens of documented `uv run thesis` invocations, found {checked}"
