#!/usr/bin/env python
"""Download the Rotzoll and Izuka (2023) MODFLOW-2005 SWI2 data release.

Rotzoll, K., and Izuka, S.K., 2023, MODFLOW-2005 and SWI2 models for assessing
groundwater availability scenarios in volcanic aquifers on Kauai, Oahu, and
Maui, Hawaii: U.S. Geological Survey data release,
https://doi.org/10.5066/P97CPK5C.

The release files are cached in data/pp1876/downloads/ and downloaded only when
missing or when their MD5 checksum on ScienceBase has changed. The input and
output of the requested island models (all three by default) are extracted
into data/pp1876/model/ and data/pp1876/output/, which restores the original
archive structure. Pass ``--force`` to download and extract everything again.
"""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ITEM_ID = "644355fbd34ee8d4ade9d748"
ITEM_URL = f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json"

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "pp1876"
DOWNLOAD_DIR = DATA_DIR / "downloads"

ISLANDS = ("kauai", "maui", "oahu")

# zip files holding every island, extracted one island at a time; each island's
# directories are named <prefix>.<island>.<scenario>
ISLAND_ZIPS = {"model.zip": "input", "output.zip": "output"}

# release files that are not needed
SKIP = {"pp2023_1876_thumbnail.jpg"}

# MD5 checksums of the zip files each extracted item came from
MANIFEST_NAME = ".manifest.json"


def item_files() -> list[dict]:
    with urllib.request.urlopen(ITEM_URL, timeout=60) as response:
        item = json.load(response)
    return [f for f in item["files"] if f["name"] not in SKIP]


def md5sum(pth: Path) -> str:
    md5 = hashlib.md5()
    with pth.open("rb") as f:
        while chunk := f.read(1 << 20):
            md5.update(chunk)
    return md5.hexdigest()


def fetch(f: dict, force: bool) -> Path:
    """Download a release file unless the cached copy matches its checksum."""
    pth = DOWNLOAD_DIR / f["name"]
    md5 = f["checksum"]["value"]
    if not force and pth.is_file() and md5sum(pth) == md5:
        return pth
    print(f"{f['name']}: downloading {f['size'] / 1e6:.1f} MB")
    tmp = pth.with_suffix(pth.suffix + ".part")
    with (
        urllib.request.urlopen(f["url"], timeout=120) as response,
        tmp.open("wb") as out,
    ):
        shutil.copyfileobj(response, out, 1 << 20)
    if md5sum(tmp) != md5:
        tmp.unlink()
        sys.exit(f"{f['name']}: checksum does not match ScienceBase")
    tmp.replace(pth)
    return pth


def extract(zpth: Path, prefix: str | None = None, island: str | None = None) -> None:
    """Extract a zip file into a directory of the same name.

    With ``prefix`` and ``island``, only that island's directories are extracted.
    """
    dst = DATA_DIR / zpth.stem
    pattern = f"{prefix}.{island}.*" if island else "*"
    for d in dst.glob(pattern):
        shutil.rmtree(d) if d.is_dir() else d.unlink()
    dst.mkdir(exist_ok=True)
    with zipfile.ZipFile(zpth) as zipf:
        members = zipf.namelist()
        if island:
            members = [n for n in members if n.startswith(f"{prefix}.{island}.")]
        zipf.extractall(dst, members=members)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "islands",
        nargs="*",
        help=f"Island models to extract ({', '.join(ISLANDS)}); default is all.",
    )
    parser.add_argument("--force", action="store_true", help="Download again.")
    args = parser.parse_args()
    islands = args.islands or list(ISLANDS)
    unknown = set(islands) - set(ISLANDS)
    if unknown:
        parser.error(f"unknown island(s): {', '.join(sorted(unknown))}")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    mpth = DATA_DIR / MANIFEST_NAME
    manifest = json.loads(mpth.read_text()) if mpth.is_file() else {}
    try:
        files = item_files()
    except OSError as err:
        if manifest:
            print(f"could not reach ScienceBase ({err}); keeping the local copy")
            return 0
        sys.exit(f"could not reach ScienceBase: {err}")

    for f in files:
        name, md5 = f["name"], f["checksum"]["value"]
        pth = fetch(f, args.force)
        if name in ISLAND_ZIPS:
            prefix = ISLAND_ZIPS[name]
            for island in islands:
                key = f"{name}:{island}"
                present = any((DATA_DIR / pth.stem).glob(f"{prefix}.{island}.*"))
                if args.force or manifest.get(key) != md5 or not present:
                    print(f"{name}: extracting {island}")
                    extract(pth, prefix, island)
                    manifest[key] = md5
        elif name.endswith(".zip"):
            if (
                args.force
                or manifest.get(name) != md5
                or not (DATA_DIR / pth.stem).exists()
            ):
                print(f"{name}: extracting")
                extract(pth)
                manifest[name] = md5
        elif args.force or manifest.get(name) != md5 or not (DATA_DIR / name).exists():
            shutil.copy2(pth, DATA_DIR / name)
            manifest[name] = md5
        mpth.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"data release ({', '.join(islands)}) is in '{DATA_DIR}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
