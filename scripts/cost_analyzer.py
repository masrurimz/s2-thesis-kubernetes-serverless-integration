#!/usr/bin/env python3
"""Pointer: canonical version is thesis/scripts/cost_analyzer.py"""
# This is a convenience wrapper. The canonical version lives in thesis/scripts/.
import subprocess, sys, os
canonical = os.path.join(os.path.dirname(__file__), '..', 'thesis', 'scripts', 'cost_analyzer.py')
sys.exit(subprocess.call([sys.executable, canonical] + sys.argv[1:]))
