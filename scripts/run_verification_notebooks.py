#!/usr/bin/env python
"""Run the SWI verification notebooks and report their run times.

Each jupytext notebook in notebooks-verification/ runs as a script in its own
process, from that directory, with the non-interactive matplotlib backend. A
notebook fails if it raises or takes longer than the time limit. Pass notebook
paths to run specific ones.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

NOTEBOOK_DIR = Path(__file__).parents[1] / "notebooks-verification"

# maximum run time of a notebook, in seconds
TIME_LIMIT = 30.0


def notebooks(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p).resolve() for p in paths]
    return sorted(NOTEBOOK_DIR.glob("gwf_swi*.py"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("notebooks", nargs="*", help="Notebooks to run.")
    parser.add_argument(
        "--time-limit",
        type=float,
        default=TIME_LIMIT,
        help=f"Maximum run time of a notebook, in seconds; default {TIME_LIMIT}.",
    )
    args = parser.parse_args()

    env = os.environ | {"MPLBACKEND": "Agg"}
    failed = []
    for nb in notebooks(args.notebooks):
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, nb.name],
            cwd=nb.parent,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        elapsed = time.perf_counter() - t0
        if proc.returncode != 0:
            status = "FAILED"
            print(proc.stdout + proc.stderr)
        elif elapsed > args.time_limit:
            status = f"TOO SLOW (limit {args.time_limit:.0f} s)"
        else:
            status = "ok"
        if status != "ok":
            failed.append(nb.name)
        print(f"{nb.name:32s} {elapsed:7.1f} s  {status}", flush=True)

    if failed:
        print(f"\n{len(failed)} notebook(s) failed: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
