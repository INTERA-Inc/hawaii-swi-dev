#!/usr/bin/env python
"""Convert the SWI notebooks to .ipynb in the documentation source.

The jupytext notebooks in notebooks-verification/ are written to
docs/source/notebooks/, executed first with ``--execute``, and listed in an
index page there. ``--skip-if-exist`` leaves notebooks already in place, such as
the executed notebooks Read the Docs downloads from the docs workflow.
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks-verification"
DOCS_NOTEBOOK_DIR = ROOT / "docs" / "source" / "notebooks"


def prepare_notebooks(execute: bool, skip_if_exist: bool) -> list[Path]:
    DOCS_NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    if not skip_if_exist:
        for f in DOCS_NOTEBOOK_DIR.glob("*.ipynb"):
            f.unlink()

    for src in sorted(NOTEBOOK_DIR.glob("gwf_swi*.py")):
        dst = DOCS_NOTEBOOK_DIR / f"{src.stem}.ipynb"
        if skip_if_exist and dst.exists():
            continue
        cmd = ["jupytext", "--to", "ipynb", "--output", str(dst), str(src)]
        if execute:
            cmd += ["--execute", "--run-path", str(NOTEBOOK_DIR)]
        subprocess.run(cmd, check=True)

    return sorted(DOCS_NOTEBOOK_DIR.glob("*.ipynb"))


def write_index(notebooks: list[Path]) -> None:
    lines = [
        "SWI Package tests",
        "=================",
        "",
        "Notebooks ported from the SWI Package autotests.",
        "",
        ".. toctree::",
        "   :maxdepth: 1",
        "",
    ]
    for nb in notebooks:
        lines.append(f"   {nb.stem}")
    lines.append("")
    (DOCS_NOTEBOOK_DIR / "index.rst").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--execute", action="store_true", help="Execute the notebooks.")
    parser.add_argument(
        "--skip-if-exist",
        action="store_true",
        help="Leave notebooks already in the documentation source.",
    )
    args = parser.parse_args()
    write_index(prepare_notebooks(args.execute, args.skip_if_exist))
    return 0


if __name__ == "__main__":
    sys.exit(main())
