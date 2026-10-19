"""Figures and tables of the README, from the CSV files in results/.

python scripts/figures.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from darrieus.reference import CYLINDER_2D1
from darrieus.rotor import Run, moment_coefficient, read_csv

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIG = ROOT / "docs" / "figures"
ROTOR = re.compile(r"rotor_tsr(?P<tsr>[\d.]+)_Re(?P<re>\d+)_N(?P<n>\d+)\.csv")


def couette() -> list[dict]:
    rows = []
    for path in RESULTS.glob("couette_N*.csv"):
        d = read_csv(path)
        n = int(path.stem.split("N")[1])
        rows.append(
            {
                "N": n,
                "torque": float(d["torque"][-1]),
                "exact": float(d["torque_exact"][-1]),
                "torque_error": float(abs(d["torque"][-1] / d["torque_exact"][-1] - 1)),
                "l2_error": float(d["l2_error"][-1]),
            }
        )
    rows.sort(key=lambda r: r["N"])
    if len(rows) < 2:
        return rows

    n = np.array([r["N"] for r in rows])
    fig, ax = plt.subplots(figsize=(5, 3.8))
    ax.loglog(n, [r["torque_error"] for r in rows], "o-", label="torque on inner cylinder")
    ax.loglog(n, [r["l2_error"] for r in rows], "s-", label=r"velocity, relative $L^2$")
    ref = rows[-1]["l2_error"] * (n / n[-1]) ** -2.0
    ax.loglog(n, ref, "k:", lw=1, label=r"slope $-2$")
    ax.set_xlabel("nodes on the sliding interface")
    ax.set_ylabel("relative error")
    ax.set_xticks(n, [str(k) for k in n])
    ax.minorticks_off()
    ax.legend(fontsize=8)
    ax.set_title("Taylor–Couette flow across the sliding interface", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "couette_convergence.png", dpi=150)
    plt.close(fig)
    return rows


def cylinder() -> list[dict]:
    rows = []
    for path in RESULTS.glob("cylinder_n*.csv"):
        d = read_csv(path)
        rows.append({k: float(d[k][-1]) for k in ["n", "cells", "dofs", "cD", "cL", "dp"]})
    rows.sort(key=lambda r: r["n"])
    for r in rows:
        r["n"] = int(r["n"])
        r["cells"] = int(r["cells"])
        r["dofs"] = int(r["dofs"])
        r["cD_error"] = abs(r["cD"] / CYLINDER_2D1["cD"] - 1)
        r["dp_error"] = abs(r["dp"] / CYLINDER_2D1["dp"] - 1)
    return rows


def load_rotor() -> dict[tuple[float, float, int], Run]:
    runs = {}
    for path in RESULTS.glob("rotor_*.csv"):
        m = ROTOR.fullmatch(path.name)
        if m is None:
            continue
        tsr, re_, n = float(m["tsr"]), float(m["re"]), int(m["n"])
        runs[tsr, re_, n] = Run.load(path, tsr, re_, n)
    return dict(sorted(runs.items()))


def torque_azimuth(runs: list[Run]) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for run in runs:
        last = run.last_revolution()
        az = run.blade_azimuth()
        order = np.argsort(az)
        cm = moment_coefficient(run.blade1[last])
        ax.plot(az[order], cm[order], label=rf"$\lambda$ = {run.tsr:g}")
    ax.axhline(0, color="k", lw=0.6)
    ax.axvspan(0, 180, color="0.92", zorder=0)
    for az, side in [(90, "upwind"), (270, "downwind")]:
        ax.annotate(
            side,
            (az, 0.03),
            xycoords=("data", "axes fraction"),
            ha="center",
            fontsize=8,
            color="0.4",
        )
    ax.set_xlim(0, 360)
    ax.set_xticks(range(0, 361, 45))
    ax.set_xlabel("azimuth of blade 1 [deg]")
    ax.set_ylabel(r"$C_m$, blade 1")
    ax.legend(fontsize=8)
    ax.set_title("Moment of one blade over the last revolution", fontsize=10)
    fig.savefig(FIG / "blade_moment.png", dpi=150)
    plt.close(fig)




def revolutions(runs: list[Run]) -> None:
    fig, ax = plt.subplots(figsize=(5, 3.6))
    for run in runs:
        means = run.per_revolution()
        ax.plot(np.arange(1, means.size + 1), means / 0.25, "o-", label=rf"$\lambda$ = {run.tsr:g}")
    ax.set_xlabel("revolution")
    ax.set_ylabel(r"mean $C_m$ of the rotor")
    ax.legend(fontsize=8)
    ax.set_title("Approach to a periodic regime", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "revolutions.png", dpi=150)
    plt.close(fig)


def resolution(runs: dict[tuple[float, float, int], Run]) -> list[dict]:
    """Runs that differ only by N: time step and rotor mesh refined together."""
    rows = []
    groups: dict[tuple[float, float], list[Run]] = {}
    for (tsr, re_, _), run in runs.items():
        groups.setdefault((tsr, re_), []).append(run)
    for group in groups.values():
        if len(group) < 2:
            continue
        fig, ax = plt.subplots(figsize=(6.4, 3.6))
        for run in sorted(group, key=lambda r: r.steps_per_rev):
            last = run.last_revolution()
            az = run.blade_azimuth()
            order = np.argsort(az)
            dtheta = 360 / run.steps_per_rev
            label = rf"N = {run.steps_per_rev}, $\Delta\theta$ = {dtheta:.1f}°"
            ax.plot(az[order], moment_coefficient(run.torque[last])[order], label=label)
            rows.append({"tsr": run.tsr, "N": run.steps_per_rev, "Cp": run.cp(), "dtheta": dtheta})
        ax.set_xlim(0, 360)
        ax.set_xticks(range(0, 361, 45))
        ax.set_xlabel("azimuth of blade 1 [deg]")
        ax.set_ylabel(r"$C_m$, rotor")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_title(rf"Resolution study, $\lambda$ = {group[0].tsr:g}", fontsize=10)
        fig.tight_layout()
        fig.savefig(FIG / "resolution.png", dpi=150)
        plt.close(fig)
    return rows


def vorticity_animation(frames: Path, path: Path) -> None:
    files = sorted(frames.glob("vort_*.txt"), key=lambda p: int(p.stem.split("_")[1]))
    if not files:
        return
    data = []
    for f in files:
        with open(f) as fh:
            theta = float(fh.readline())
            data.append((theta, np.loadtxt(fh)))
    extent = (-1.5, 4.5, -1.2, 1.2)
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    
    image = ax.imshow(data[0][1], origin="lower", extent=extent, cmap="turbo", vmin=-12, vmax=12, interpolation="bilinear")


    ax.add_patch(plt.Circle((0, 0), 0.5, fill=False, ls=":", lw=0.6, color="0.3"))
    ax.set_aspect("equal")
    ax.set_xlabel("x / D")
    ax.set_ylabel("y / D")
    label = ax.text(0.01, 0.92, "", transform=ax.transAxes, fontsize=9)
    fig.colorbar(image, ax=ax, label=r"$\omega_z D / U$", shrink=0.8)
    fig.tight_layout()

    def draw(i):
        theta, w = data[i]
        image.set_data(w)
        label.set_text(f"azimuth {np.mod(theta, 360):.0f}°")
        return image, label

    FuncAnimation(fig, draw, frames=len(data)).save(path, writer=PillowWriter(fps=12))
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    summary: dict = {"couette": couette(), "cylinder": cylinder()}

    runs = load_rotor()
    if runs:
        reynolds = max({k[1] for k in runs}, key=lambda r: sum(k[1] == r for k in runs))
        base = {}
        for (tsr, re_, n), run in runs.items():
            if re_ == reynolds and (tsr not in base or n == 120):
                base[tsr] = run
        sweep = [base[t] for t in sorted(base)]
        torque_azimuth(sweep)
        revolutions(sweep)
        summary["rotor"] = [
            {
                "tsr": r.tsr,
                "Re": r.reynolds,
                "N": r.steps_per_rev,
                "revolutions": r.revolutions,
                "Cp": r.cp(),
                "periodicity": r.periodicity(),
            }
            for r in sweep
        ]
        summary["resolution"] = resolution(runs)

    frames = RESULTS / "frames"
    if frames.exists():
        for folder in sorted(frames.iterdir()):
            vorticity_animation(folder, FIG / "darrieus_vortex.gif")

    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
