#!/usr/bin/env python3
"""Generate synthetic k6 stage files for AAPA workload archetypes.

Each archetype is a 20-minute trace (40 stages × 30s) designed to test
specific controller behaviors. Based on AAPA (arXiv:2507.05653) classification:
SPIKE, PERIODIC, RAMP, STATIONARY.

Output: data/trace-replay/archetype_{name}_k6_stages.json
"""

import json
import math
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
STAGE_DURATION = "30s"
NUM_STAGES = 40  # 40 × 30s = 20 min


def make_stages(targets: list[int]) -> list[dict]:
    return [{"duration": STAGE_DURATION, "target": t} for t in targets]


def spike() -> list[dict]:
    """Baseline 40 → sudden spike to 200 for 4 stages → back to 40.

    Tests reactive vs predictive burst handling.
    """
    targets = [40] * 5  # 0-2.5min: baseline
    targets += [80] * 2  # 2.5-3.5min: ramp up
    targets += [200] * 4  # 3.5-5.5min: SPIKE (2x K8s capacity)
    targets += [80] * 2  # 5.5-6.5min: ramp down
    targets += [40] * 5  # 6.5-9min: recovery baseline
    targets += [50] * 5  # 9-11.5min: moderate load
    targets += [60] * 4  # 11.5-13.5min: gentle increase
    targets += [40] * 13  # 13.5-20min: return to baseline
    return make_stages(targets[:NUM_STAGES])


def periodic() -> list[dict]:
    """Sinusoidal: 40 + 35×sin(t/60×π), period ~2 min, range 5-75 RPS.

    Tests prediction accuracy on repeating patterns.
    """
    targets = []
    for i in range(NUM_STAGES):
        t_sec = i * 30
        rps = int(40 + 35 * math.sin(t_sec / 60 * math.pi))
        targets.append(max(5, rps))
    return make_stages(targets)


def ramp() -> list[dict]:
    """Linear increase from 20 to 150 RPS over 20 min.

    Tests capacity-driven scaling responsiveness.
    """
    targets = []
    for i in range(NUM_STAGES):
        rps = int(20 + (150 - 20) * i / (NUM_STAGES - 1))
        targets.append(rps)
    return make_stages(targets)


def stationary() -> list[dict]:
    """Constant 120 RPS — above K8s capacity (84 RPS) for entire run.

    Tests sustained serverless overflow.
    """
    return make_stages([120] * NUM_STAGES)


def high_load() -> list[dict]:
    """Constant 200 RPS — well into serverless-expensive zone.

    At 200 RPS, Lambda needs ~26 PC instances (200×0.126s=25.2).
    PC capacity alone costs ~$112/mo. Total serverless ~$280/mo vs EC2 ~$195/mo.
    """
    return make_stages([200] * NUM_STAGES)


ARCHETYPES = {
    "spike": spike,
    "periodic": periodic,
    "ramp": ramp,
    "stationary": stationary,
    "high_load": high_load,
}


def main() -> int:
    for name, generator in ARCHETYPES.items():
        stages = generator()
        path = OUTPUT_DIR / f"archetype_{name}_k6_stages.json"
        with open(path, "w") as f:
            json.dump(stages, f, indent=2)

        rps_values = [s["target"] for s in stages]
        print(
            f"  {name:12s}: {len(stages)} stages, "
            f"RPS {min(rps_values)}-{max(rps_values)}, "
            f"mean {sum(rps_values) / len(rps_values):.0f}"
        )
    print(f"\nGenerated {len(ARCHETYPES)} archetype files in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
