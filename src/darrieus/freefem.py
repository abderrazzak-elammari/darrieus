"""Run the FreeFEM scripts in freefem/ with chosen parameters.

Each script sets its own defaults and then includes override.idp. To run one with other
values, the scripts are copied to a working directory, an override.idp with the new
values is written there, and FreeFem++ is started in that directory. No command line
parsing on the FreeFEM side, so the scripts also run unchanged from FreeFem++-cs.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "freefem"


def executable() -> str:
    """FreeFem++ binary, from FREEFEM if set, otherwise from the path."""
    name = os.environ.get("FREEFEM") or shutil.which("FreeFem++") or shutil.which("FreeFem++.exe")
    if not name:
        raise RuntimeError("FreeFem++ not found: install FreeFEM or set FREEFEM to the binary")
    return name


def override(**values: float | str | Path) -> str:
    """Contents of override.idp: one assignment per parameter."""
    lines = []
    for name, value in values.items():
        if isinstance(value, (str, Path)):
            text = '"' + str(value).replace("\\", "/") + '"'
        else:
            text = repr(value)
        lines.append(f"{name} = {text};")
    return "\n".join(lines) + "\n"


def stage(workdir: Path, **values: float | str | Path) -> None:
    workdir.mkdir(parents=True, exist_ok=True)
    for script in SCRIPTS.glob("*.?dp"):
        shutil.copy(script, workdir / script.name)
    (workdir / "override.idp").write_text(override(**values))


def run(script: str, workdir: Path, log: Path | None = None, **values: float | str | Path) -> None:
    """Run one script with the given parameter values, in its own directory."""
    stage(workdir, **values)
    cmd = [executable(), "-nw", "-v", "0", script]
    with open(log, "w") if log else open(os.devnull, "w") as out:
        done = subprocess.run(cmd, cwd=workdir, stdout=out, stderr=subprocess.STDOUT, check=False)
    if done.returncode != 0:
        where = f", see {log}" if log else ""
        raise RuntimeError(f"{script} failed with exit code {done.returncode}{where}")
