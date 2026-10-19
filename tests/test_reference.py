import numpy as np
import pytest

from darrieus.reference import TaylorCouette


def test_couette_velocity_matches_walls():
    tc = TaylorCouette(r1=0.4, r2=1.3, omega=2.0)
    assert tc.u_theta(0.4) == pytest.approx(0.8)
    assert tc.u_theta(1.3) == pytest.approx(0.0, abs=1e-14)


def test_couette_torque_from_wall_shear():
    tc = TaylorCouette(nu=0.05)
    r = tc.r1
    h = 1e-6
    dudr = (tc.u_theta(r + h) - tc.u_theta(r - h)) / (2 * h)
    shear = tc.nu * (dudr - tc.u_theta(r) / r)
    assert tc.torque() == pytest.approx(2 * np.pi * r * r * shear, rel=1e-6)


def test_couette_torque_opposes_rotation():
    assert TaylorCouette(omega=1.0).torque() < 0
    assert TaylorCouette(omega=-1.0).torque() > 0
