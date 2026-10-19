"""Torque histories of the rotor and the coefficients derived from them.

Everything is in the units of the FreeFEM script: rotor diameter D = 1, free stream
U = 1, density 1, so the torque is per unit span and scaled by rho U^2 D^2.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

RADIUS = 0.5


def read_csv(path: Path) -> dict[str, NDArray[np.float64]]:
    data = np.genfromtxt(path, delimiter=",", names=True)
    return {name: np.atleast_1d(data[name]) for name in data.dtype.names}


def power_coefficient(torque: NDArray[np.float64] | float, tsr: float) -> NDArray[np.float64]:
    """Cp = T omega / (rho U^3 D / 2), with omega = tsr U / R."""
    omega = tsr / RADIUS
    return np.asarray(torque) * omega / 0.5


def moment_coefficient(torque: NDArray[np.float64] | float) -> NDArray[np.float64]:
    """Cm = T / (rho U^2 D R / 2)."""
    return np.asarray(torque) / (0.5 * RADIUS)


@dataclass
class Run:
    tsr: float
    reynolds: float
    steps_per_rev: int
    theta: NDArray[np.float64]
    torque: NDArray[np.float64]
    blade1: NDArray[np.float64]
    blade2: NDArray[np.float64]
    fx: NDArray[np.float64]
    fy: NDArray[np.float64]

    @classmethod
    def load(cls, path: Path, tsr: float, reynolds: float, steps_per_rev: int) -> Run:
        d = read_csv(path)
        return cls(
            tsr,
            reynolds,
            steps_per_rev,
            d["theta_deg"],
            d["torque"],
            d["torque1"],
            d["torque2"],
            d["fx"],
            d["fy"],
        )

    @property
    def revolutions(self) -> int:
        return self.torque.size // self.steps_per_rev

    def per_revolution(self) -> NDArray[np.float64]:
        """Mean torque of each complete revolution."""
        n = self.revolutions * self.steps_per_rev
        return self.torque[:n].reshape(self.revolutions, self.steps_per_rev).mean(axis=1)

    def last_revolution(self) -> slice:
        return slice(self.torque.size - self.steps_per_rev, self.torque.size)

    def mean_torque(self) -> float:
        return float(self.torque[self.last_revolution()].mean())

    def cp(self) -> float:
        return float(power_coefficient(self.mean_torque(), self.tsr))

    def periodicity(self) -> float:
        """Change of the mean torque over the last revolution, relative to its amplitude.

        Rezaeiha et al. (2018) ask for less than 0.2 % change of the mean Cm between
        successive revolutions; the amplitude is used as the scale because the mean can
        be close to zero at low tip speed ratio.
        """
        means = self.per_revolution()
        if means.size < 2:
            return float("nan")
        amplitude = np.ptp(self.torque[self.last_revolution()])
        return float(abs(means[-1] - means[-2]) / amplitude)

    def blade_azimuth(self) -> NDArray[np.float64]:
        """Azimuth of blade 1 over the last revolution, 0 to 360 degrees.

        In the script theta = 0 is downwind (+x) with blade 1 starting at 90 degrees.
        The usual VAWT convention puts 0 at the top of the rotor, blade moving upwind,
        which is where blade 1 starts, so the azimuth is simply theta modulo 360.
        """
        return np.mod(self.theta[self.last_revolution()], 360.0)
