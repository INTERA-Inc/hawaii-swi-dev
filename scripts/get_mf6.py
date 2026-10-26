#!/usr/bin/env python
"""Install the MODFLOW 6 SWI preview release into the active pixi environment.

The mf6 executables come from the latest jdhughes-dev/modflow6-feat-swi-preview
release via flopy's get-modflow, the release DFN files are extracted to dfn/,
and the flopy MODFLOW 6 classes are regenerated from those DFN files.

Pass ``--if-missing`` (used by the activation hook) to do nothing, without
network access, when mf6, the DFN files, and the generated classes are present.
Pass ``--force`` to reinstall even when the latest release is installed.
"""

import argparse
import os
import sys
import tempfile
import urllib.request
import zipfile
from importlib.util import find_spec
from pathlib import Path

OWNER = "jdhughes-dev"
REPO = "modflow6-feat-swi-preview"

# installed release tag, written to the environment prefix
STAMP_NAME = "mf6-swi-release.txt"


def conda_prefix() -> Path:
    prefix = os.environ.get("CONDA_PREFIX")
    if not prefix:
        sys.exit("CONDA_PREFIX is not set; run this with `pixi run get-mf6`.")
    return Path(prefix)


def project_root() -> Path:
    return Path(os.environ.get("PIXI_PROJECT_ROOT", Path(__file__).parents[1]))


def bindir(prefix: Path) -> Path:
    if sys.platform.startswith("win"):
        return prefix / "Library" / "bin"
    return prefix / "bin"


def dfndir() -> Path:
    return project_root() / "dfn"


def stamp_path(prefix: Path) -> Path:
    return prefix / "share" / STAMP_NAME


def mf6_installed(prefix: Path) -> bool:
    exe = "mf6.exe" if sys.platform.startswith("win") else "mf6"
    return (bindir(prefix) / exe).is_file()


def swi_classes_generated() -> bool:
    spec = find_spec("flopy")
    if spec is None or spec.origin is None:
        return False
    return (Path(spec.origin).parent / "mf6" / "modflow" / "mfgwfswi.py").is_file()


def installed_tag(prefix: Path) -> str | None:
    pth = stamp_path(prefix)
    return pth.read_text().strip() if pth.is_file() else None


def is_complete(prefix: Path) -> bool:
    return (
        mf6_installed(prefix)
        and installed_tag(prefix) is not None
        and any(dfndir().glob("*.dfn"))
        and swi_classes_generated()
    )


def install_dfns(release: dict, downloads: Path, quiet: bool) -> None:
    from flopy.utils.get_modflow import download

    for asset in release["assets"]:
        if asset["name"].endswith("_dfns.zip"):
            break
    else:
        raise ValueError(f"no DFN asset in release {release['tag_name']!r}")

    pth = downloads / asset["name"]
    if not quiet:
        print(f"downloading '{asset['browser_download_url']}'")
    download(urllib.request.Request(asset["browser_download_url"]), pth, quiet=quiet)

    # replace, rather than merge, so DFN files dropped upstream do not linger
    dst = dfndir()
    dst.mkdir(exist_ok=True)
    for f in dst.glob("*.dfn"):
        f.unlink()
    with zipfile.ZipFile(pth) as zipf:
        for name in zipf.namelist():
            if name.endswith(".dfn"):
                (dst / Path(name).name).write_bytes(zipf.read(name))
    if not quiet:
        print(f"extracted DFN files to '{dst}'")


def generate_classes(quiet: bool) -> None:
    from contextlib import redirect_stdout

    from flopy.mf6.utils import generate_classes as generate

    with (
        open(os.devnull, "w") as devnull,
        redirect_stdout(devnull if quiet else sys.stdout),
    ):
        generate(dfnpath=str(dfndir()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="Reinstall.")
    parser.add_argument(
        "--if-missing",
        action="store_true",
        help="Do nothing if the installation is complete.",
    )
    parser.add_argument("--quiet", action="store_true", help="Show fewer messages.")
    args = parser.parse_args()

    prefix = conda_prefix()
    if args.if_missing and not args.force and is_complete(prefix):
        return 0

    from flopy.utils.get_modflow import get_release, run_main

    release = get_release(OWNER, REPO, "latest", quiet=args.quiet)
    tag = release["tag_name"]
    if not args.force and tag == installed_tag(prefix) and is_complete(prefix):
        if not args.quiet:
            print(f"{OWNER}/{REPO} release {tag!r} is already installed")
        return 0

    with tempfile.TemporaryDirectory() as tmpdir:
        downloads = Path(tmpdir)
        run_main(
            bindir(prefix),
            owner=OWNER,
            repo=REPO,
            release_id=tag,
            downloads_dir=downloads,
            force=True,
            quiet=args.quiet,
        )
        install_dfns(release, downloads, args.quiet)

    generate_classes(args.quiet)

    pth = stamp_path(prefix)
    pth.parent.mkdir(parents=True, exist_ok=True)
    pth.write_text(f"{tag}\n")
    if not args.quiet:
        print(f"installed {OWNER}/{REPO} release {tag!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
