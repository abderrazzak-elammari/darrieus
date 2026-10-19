"""Run the verification cases and the rotor, results go to results/.

    python scripts/run.py couette --N 48 96 192
    python scripts/run.py cylinder --n 16 32 64
    python scripts/run.py rotor --tsr 1.5 2 2.5 3 3.5 --revs 6
    python scripts/run.py rotor --tsr 2.5 --N 90 120 180       # time step / mesh study
    python scripts/run.py rotor --tsr 2.5 --snap 4             # vorticity frames

A case whose CSV already exists is skipped. Several cases run side by side with --jobs.
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from darrieus import freefem

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
LOGS = ROOT / "logs"
WORK = ROOT / "work"


def rotor_name(tsr: float, reynolds: float, n: int) -> str:
    return f"rotor_tsr{tsr:g}_Re{reynolds:g}_N{n}"


def job(script: str, name: str, **values) -> None:
    out = RESULTS / f"{name}.csv"
    if out.exists():
        print(f"{name}: already done")
        return
    tic = time.perf_counter()
    partial = out.with_suffix(".part")
    freefem.run(script, WORK / name, log=LOGS / f"{name}.log", out=partial, **values)
    partial.rename(out)
    print(f"{name}: {(time.perf_counter() - tic) / 60:.1f} min", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="case", required=True)

    c = sub.add_parser("couette")
    c.add_argument("--N", type=int, nargs="+", default=[48, 96, 192])
    c.add_argument("--tend", type=float, default=15.0)

    y = sub.add_parser("cylinder")
    y.add_argument("--n", type=int, nargs="+", default=[16, 32, 64])

    r = sub.add_parser("rotor")
    r.add_argument("--tsr", type=float, nargs="+", default=[2.5])
    r.add_argument("--Re", type=float, default=5000)
    r.add_argument("--N", type=int, nargs="+", default=[120])
    r.add_argument("--nblade", type=int, default=40)
    r.add_argument("--revs", type=float, default=6)
    r.add_argument("--snap", type=int, default=0, help="vorticity every k steps, last rev")

    p.add_argument("--jobs", type=int, default=1)
    args = p.parse_args()

    RESULTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    tasks = []
    if args.case == "couette":
        for n in args.N:
            tasks.append(("couette.edp", f"couette_N{n}", {"nIface": n, "tEnd": args.tend}))
    elif args.case == "cylinder":
        for n in args.n:
            tasks.append(("cylinder.edp", f"cylinder_n{n}", {"n": n}))
    else:
        for tsr in args.tsr:
            for n in args.N:
                name = rotor_name(tsr, args.Re, n)
                values = {
                    "lambda": tsr,
                    "Re": args.Re,
                    "nIface": n,
                    "nBlade": round(args.nblade * n / 120),
                    "revs": args.revs,
                }
                if args.snap:
                    frames = RESULTS / "frames" / name
                    frames.mkdir(parents=True, exist_ok=True)
                    values.update(snapEvery=args.snap, snapDir=frames)
                tasks.append(("darrieus.edp", name, values))

    with ThreadPoolExecutor(args.jobs) as pool:
        for future in [pool.submit(job, s, n, **o) for s, n, o in tasks]:
            future.result()


if __name__ == "__main__":
    main()
