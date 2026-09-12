"""The import graph is part of the contract, and a test that fails when it drifts.

Each layering rule here was read off the code before it was written down, so a
violation is a change in the architecture rather than a surprise. The contracts live
in pyproject.toml; this runs them so a normal test run catches a boundary crossed.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


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
