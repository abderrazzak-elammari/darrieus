"""Exact solutions and benchmark values used to check the solver."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

# Schafer & Turek (1996), test 2D-1, values of John (2004) on very fine meshes.
CYLINDER_2D1 = {"cD": 5.57953523, "cL": 0.010618948, "dp": 0.11752016}


@dataclass(frozen=True)
class TaylorCouette:
    """Flow between an inner cylinder turning at omega and a fixed outer one."""

    r1: float = 0.5
    r2: float = 1.0
    omega: float = 1.0
    nu: float = 0.1

    @property
    def a(self) -> float:
        return -self.omega * self.r1**2 / (self.r2**2 - self.r1**2)

    @property
    def b(self) -> float:
        return self.omega * self.r1**2 * self.r2**2 / (self.r2**2 - self.r1**2)

    def u_theta(self, r: ArrayLike) -> NDArray[np.float64]:
        r = np.asarray(r, dtype=float)
        return self.a * r + self.b / r

    def torque(self) -> float:
        """Torque of the fluid on the inner cylinder, per unit length and density."""
        return -4.0 * np.pi * self.nu * self.b
