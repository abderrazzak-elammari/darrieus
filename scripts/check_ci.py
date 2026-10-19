"""Fail if the coarse verification runs of the CI drift from their known accuracy.

python scripts/check_ci.py couette.csv cylinder.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

from darrieus.reference import CYLINDER_2D1
from darrieus.rotor import read_csv


def main(couette: Path, cylinder: Path) -> None:
    c = read_csv(couette)
    torque_error = abs(c["torque"][-1] / c["torque_exact"][-1] - 1)
    y = read_csv(cylinder)
    drag_error = abs(y["cD"][-1] / CYLINDER_2D1["cD"] - 1)
    print(f"Couette torque error {torque_error:.2%}, cylinder drag error {drag_error:.2%}")
    # Values of the CI meshes: 2.2 % and 0.4 %.
    if torque_error > 0.03 or drag_error > 0.01:
        sys.exit(1)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
