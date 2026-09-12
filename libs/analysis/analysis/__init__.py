"""Domain analysis library for thesis experiment results.

Consumed by ``apps/analysis`` (CLI) and ``apps/cli`` (the home view's bundle
verdict). ``apps/experiment`` and ``apps/dashboard`` do not import it. Depends on ``libs/shared`` for
statistical primitives (``shared.stats``), models (``shared.models``), and
scenario constants (``shared.scenarios``).
"""
