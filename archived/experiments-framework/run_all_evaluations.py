#!/usr/bin/env python3
"""Run all thesis hypothesis evaluations."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from evaluations.h2_evaluation import H2Evaluator


def main():
    print("=" * 70)
    print("THESIS HYPOTHESIS EVALUATION SUITE")
    print("=" * 70)
    print()
    
    # Run H2
    print("Running H2 evaluation (Predictive > Reactive)...")
    h2 = H2Evaluator()
    h2_result = h2.run_evaluation(simulate=True)
    
    # Summary
    print()
    print("=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)
    print()
    print(f"H2 (Predictive > Reactive):  {'PROVEN ✓' if h2_result.hypothesis_proven else 'NOT PROVEN ✗'}")
    print()


if __name__ == "__main__":
    main()
