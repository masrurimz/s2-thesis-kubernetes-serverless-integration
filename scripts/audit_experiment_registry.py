#!/usr/bin/env python3
"""Audit and classify all experiment bundles into a machine-readable registry.

Walks results/experiments, results/models, results/cost and classifies each
directory by role. Never auto-sets role: final — that is human-only.

Usage:
    uv run python scripts/audit_experiment_registry.py           # dry-run print
    uv run python scripts/audit_experiment_registry.py --write   # update REGISTRY.yaml
"""

import argparse
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
REGISTRY_PATH = RESULTS_DIR / "experiments" / "REGISTRY.yaml"

SCENARIO_PATTERN = re.compile(r"(s[1-4]-[a-z-]+)")
DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


def classify_role(dirname: str, has_report: bool, n_clean: int) -> str:
    """Auto-classify a directory into a role (never 'final')."""
    dl = dirname.lower()
    if "abort" in dl or "invalid" in dl:
        return "invalidated"
    if any(k in dl for k in ("smoke", "sanity", "probe", "quick", "calibration", "test", "v2-", "v3-")):
        # v2-/v3- are controller version sanity checks, not thesis runs
        if "sanity" in dl or "probe" in dl or "quick" in dl:
            return "smoke"
    if any(k in dl for k in ("smoke", "sanity", "probe", "quick", "calibration", "test")):
        return "smoke"
    if has_report and n_clean == 0:
        return "incomplete"
    if has_report and n_clean > 0:
        return "intermediate"
    if not has_report:
        return "incomplete"
    return "incomplete"


def count_clean_runs(report_path: Path) -> int:
    """Extract 'N clean' from report.md header (handles markdown bold)."""
    if not report_path.exists():
        return 0
    try:
        text = report_path.read_text(errors="replace")
        m = re.search(r"(\d+)\s+clean", text)
        return int(m.group(1)) if m else -1
    except Exception:
        return -1


def scan_dir(root_name: str, dir_path: Path) -> dict | None:
    """Scan a single experiment directory."""
    if not dir_path.is_dir():
        return None

    dirname = dir_path.name
    has_meta = (dir_path / "meta.yaml").exists()
    report_path = dir_path / "report.md"
    has_report = report_path.exists()
    n_clean = count_clean_runs(report_path)

    # Infer scenarios from subdirectory names
    subdirs = [d.name for d in dir_path.iterdir() if d.is_dir()] if dir_path.exists() else []
    scenarios = sorted(set(m.group(1) for d in subdirs for m in [SCENARIO_PATTERN.search(d)] if m))

    # Infer date from dirname
    date_match = DATE_PATTERN.search(dirname)
    date = date_match.group(1) if date_match else ""

    role = classify_role(dirname, has_report, max(n_clean, 0))

    # Generate stable id
    dirpath_rel = str(dir_path.relative_to(RESULTS_DIR))
    slug = dirname.replace("_", "-")
    exp_id = f"{root_name}.{slug}"

    return {
        "id": exp_id,
        "root": root_name,
        "path": dirpath_rel,
        "date": date,
        "role": role,
        "scenarios": scenarios,
        "n_clean": n_clean,
        "has_meta": has_meta,
        "has_report": has_report,
        "claims_supported": [],
        "supersedes": [],
        "superseded_by": None,
        "notes": "",
    }


def scan_all() -> list[dict]:
    """Scan all three roots."""
    entries = []

    # experiments: depth 2 (phase-x/date-slug)
    exp_root = RESULTS_DIR / "experiments"
    if exp_root.exists():
        for phase_dir in sorted(exp_root.iterdir()):
            if not phase_dir.is_dir():
                continue
            for exp_dir in sorted(phase_dir.iterdir()):
                if not exp_dir.is_dir():
                    continue
                entry = scan_dir("experiments", exp_dir)
                if entry:
                    entries.append(entry)

    # models: depth 2 (type/date-slug)
    models_root = RESULTS_DIR / "models"
    if models_root.exists():
        for type_dir in sorted(models_root.iterdir()):
            if not type_dir.is_dir():
                continue
            for model_dir in sorted(type_dir.iterdir()):
                if not model_dir.is_dir():
                    continue
                entry = scan_dir("models", model_dir)
                if entry:
                    entries.append(entry)

    # cost: depth 1 (date-slug)
    cost_root = RESULTS_DIR / "cost"
    if cost_root.exists():
        for cost_dir in sorted(cost_root.iterdir()):
            if not cost_dir.is_dir():
                continue
            entry = scan_dir("cost", cost_dir)
            if entry:
                entries.append(entry)

    return entries


def print_summary(entries: list[dict]):
    """Print classification summary."""
    from collections import Counter

    by_role = Counter(e["role"] for e in entries)
    by_root = Counter(e["root"] for e in entries)

    print(f"\n{'=' * 60}")
    print("Experiment Registry Audit Summary")
    print(f"{'=' * 60}")
    print(f"Total dirs: {len(entries)}")
    print("\nBy root:")
    for root, count in sorted(by_root.items()):
        print(f"  {root}: {count}")
    print("\nBy role:")
    for role, count in sorted(by_role.items()):
        print(f"  {role}: {count}")

    print(f"\n{'=' * 60}")
    print("Intermediate runs (candidates for audit review):")
    print(f"{'=' * 60}")
    for e in entries:
        if e["role"] == "intermediate":
            print(f"  {e['id']:50s} n={e['n_clean']:>3}  scenarios={e['scenarios']}")

    print("\nFinal (human-marked):")
    finals = [e for e in entries if e["role"] == "final"]
    if finals:
        for e in finals:
            print(f"  {e['id']:50s} scenarios={e['scenarios']}")
    else:
        print("  (none yet — mark in REGISTRY.yaml to promote)")


def main():
    parser = argparse.ArgumentParser(description="Audit experiment registry")
    parser.add_argument("--write", action="store_true", help="Write REGISTRY.yaml")
    args = parser.parse_args()

    entries = scan_all()
    print_summary(entries)

    if args.write:
        registry = {
            "version": 1,
            "last_audited": "2026-07-10",
            "total_dirs": len(entries),
            "experiments": entries,
        }
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_PATH, "w") as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"\n✅ Written: {REGISTRY_PATH} ({len(entries)} entries)")
    else:
        print("\n(dry-run — use --write to update REGISTRY.yaml)")


if __name__ == "__main__":
    main()
