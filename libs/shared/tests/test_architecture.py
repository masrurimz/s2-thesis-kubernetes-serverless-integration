"""The import graph is part of the contract, and a test that fails when it drifts.

Each layering rule here was read off the code before it was written down, so a
violation is a change in the architecture rather than a surprise. The contracts live
in pyproject.toml; this runs them so a normal test run catches a boundary crossed.
"""

import ast
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

#: Bases that make a class a data-transfer object rather than behaviour.
DTO_BASES = frozenset({"BaseModel", "TypedDict", "Protocol", "NamedTuple"})

SCAN_ROOTS = ("apps", "libs")


def test_import_contracts_hold():
    result = subprocess.run(
        ["lint-imports"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, f"import contracts broken:\n{result.stdout}\n{result.stderr}"


def test_lint_imports_is_available():
    """A missing gate would make the contract above pass by not running."""
    probe = subprocess.run(["lint-imports", "--help"], capture_output=True, text=True, timeout=60)
    assert probe.returncode == 0, probe.stderr
    assert sys.version_info >= (3, 12)
    assert REPO_ROOT.name


def dto_definitions() -> dict[str, list[str]]:
    """Each DTO class name under apps/ and libs/, mapped to the modules defining it.

    Tests are skipped: they define stand-ins, not contracts. ``archived/`` is skipped
    for the same reason the other tools skip it, it is a frozen snapshot.
    """
    found: dict[str, list[str]] = {}
    for root in SCAN_ROOTS:
        for path in sorted((REPO_ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts or "tests" in path.parts:
                continue
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                bases = {ast.unparse(base).split(".")[-1] for base in node.bases}
                decorators = {ast.unparse(dec).split(".")[-1] for dec in node.decorator_list}
                if not (bases & DTO_BASES or "dataclass" in decorators):
                    continue
                relative = path.relative_to(REPO_ROOT).as_posix()
                found.setdefault(node.name, []).append(f"{relative}:{node.lineno}")
    return found


def test_dto_names_are_defined_once():
    """One name, one contract. A second definition lets the wrong import type-check.

    The prediction server and the routing daemon both answered ``/health`` with a class
    called ``HealthResponse`` while describing different payloads, so a reader could
    import either and nothing failed. A model two packages need belongs in
    ``libs/shared/shared/models/``; a shape only one package uses earns a name that says so.
    """
    definitions = dto_definitions()
    assert len(definitions) > 40, f"scanned too little to mean anything: {len(definitions)} classes"

    duplicates = {name: where for name, where in definitions.items() if len(where) > 1}
    assert not duplicates, "DTO names defined in more than one module:\n" + "\n".join(
        f"  {name}: {', '.join(sorted(where))}" for name, where in sorted(duplicates.items())
    )
