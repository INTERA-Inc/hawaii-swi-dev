#!/usr/bin/env python
"""Build the HTML documentation in docs/_build/html.

Pass ``--execute`` to execute the SWI notebooks before they are rendered.
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "docs" / "source"
BUILD_DIR = ROOT / "docs" / "_build" / "html"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--execute", action="store_true", help="Execute the notebooks.")
    args = parser.parse_args()

    cmd = [sys.executable, str(ROOT / "scripts" / "sphinx_prepare_notebooks.py")]
    if args.execute:
        cmd.append("--execute")
    subprocess.run(cmd, check=True)
    subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", str(SOURCE_DIR), str(BUILD_DIR)],
        check=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
