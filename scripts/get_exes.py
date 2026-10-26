#!/usr/bin/env python
"""Install MODFLOW-2005 into the active pixi environment.

The mixed (mf2005) and double (mf2005dbl) precision executables come from the
latest MODFLOW-ORG/executables release via flopy's get-modflow, for rerunning
the data release models. Executables already installed are left alone; pass
``--force`` to reinstall them.
"""

import argparse
import sys
import tempfile
from pathlib import Path

from get_mf6 import bindir, conda_prefix

EXES = ("mf2005", "mf2005dbl")

# get-modflow installs the double precision build with its program
PROGRAMS = {"mf2005"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="Reinstall.")
    args = parser.parse_args()

    bdir = bindir(conda_prefix())
    suffix = ".exe" if sys.platform.startswith("win") else ""
    missing = [exe for exe in EXES if not (bdir / f"{exe}{suffix}").is_file()]
    if not args.force and not missing:
        print(f"{', '.join(EXES)} already installed in '{bdir}'")
        return 0

    from flopy.utils.get_modflow import run_main

    with tempfile.TemporaryDirectory() as tmpdir:
        run_main(
            bdir,
            repo="executables",
            subset=PROGRAMS,
            downloads_dir=Path(tmpdir),
            force=True,
        )
    missing = [exe for exe in EXES if not (bdir / f"{exe}{suffix}").is_file()]
    if missing:
        sys.exit(f"not installed: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
