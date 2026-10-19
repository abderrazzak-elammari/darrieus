import numpy as np
import pytest

from darrieus.rotor import Run, moment_coefficient, power_coefficient, read_csv


def make_run(revs=4, n=60, tsr=2.0, drift=0.0):
    k = np.arange(revs * n)
    theta = 360.0 * (k + 1) / n
    torque = 0.02 + 0.05 * np.sin(np.radians(2 * theta)) + drift * k / n
    zeros = np.zeros_like(torque)
    return Run(tsr, 5000, n, theta, torque, torque / 2, torque / 2, zeros, zeros)


def test_power_coefficient_definition():
    # T omega over rho U^3 D / 2, with D = 1, U = 1, omega = tsr / R.
    assert power_coefficient(0.1, 2.0) == pytest.approx(0.1 * 4.0 / 0.5)
    assert moment_coefficient(0.1) == pytest.approx(0.4)


def test_mean_over_last_revolution_removes_harmonics():
    run = make_run()
    assert run.mean_torque() == pytest.approx(0.02)
    assert run.cp() == pytest.approx(power_coefficient(0.02, 2.0))


def test_periodicity():
    assert make_run().periodicity() == pytest.approx(0.0, abs=1e-12)
    assert make_run(drift=0.001).periodicity() == pytest.approx(0.001 / 0.1, rel=0.05)


def test_partial_revolution_ignored():
    run = make_run(revs=3)
    run.torque = np.append(run.torque, [9.0, 9.0])
    assert run.per_revolution().size == 3


def test_read_csv(tmp_path):
    path = tmp_path / "r.csv"
    path.write_text("step,t,torque\n1,0.1,0.5\n2,0.2,0.25\n")
    data = read_csv(path)
    assert data["torque"].tolist() == [0.5, 0.25]


def test_read_csv_single_row(tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("n,cD\n16,5.55\n")
    assert read_csv(path)["cD"].shape == (1,)
