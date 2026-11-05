#!/usr/bin/env python
"""Report the SWI autotests on feat-swi that the notebooks do not match.

Compares christianlangevin/modflow6 feat-swi with the commit recorded in
notebooks-verification/feat-swi-commit.txt, and prints the report as Markdown.
Nothing is printed to standard output when the notebooks are up to date.
GITHUB_TOKEN is used if it is set.
"""

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks-verification"
COMMIT_FILE = NOTEBOOK_DIR / "feat-swi-commit.txt"
REPO = "christianlangevin/modflow6"
BRANCH = "feat-swi"
TEST_PATTERN = re.compile(r"^autotest/test_(.*swi.*)\.py$", re.IGNORECASE)
# notebooks of the tests that do not follow the test_<notebook>.py naming; this test
# supplies only the invalid configurations
NOTEBOOKS = {"autotest/test_gwf_swi_checks.py": "gwf_swi_invalid_input"}


def github(path: str) -> dict:
    """Get a GitHub API response."""
    request = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def report() -> str:
    """Report the tests without a notebook and those changed since the commit."""
    commit = COMMIT_FILE.read_text().strip()
    compare = github(f"compare/{commit}...{BRANCH}")
    tree = github(f"git/trees/{BRANCH}?recursive=1")["tree"]

    tests = [TEST_PATTERN.match(item["path"]) for item in tree]
    missing = [
        m.group(0)
        for m in tests
        if m
        and not (NOTEBOOK_DIR / f"{NOTEBOOKS.get(m.group(0), m.group(1))}.py").exists()
    ]
    changed = [
        f"{item['filename']} ({item['status']})"
        for item in compare["files"]
        if TEST_PATTERN.match(item["filename"]) and item["filename"] not in missing
    ]
    if not missing and not changed:
        return ""

    head = compare["commits"][-1]["sha"] if compare["commits"] else commit
    lines = [f"Compared `{commit[:8]}` with `{head[:8]}` on `{BRANCH}` of `{REPO}`."]
    for title, paths in (("No notebook", missing), ("Changed", changed)):
        if paths:
            lines += ["", f"{title}:", ""] + [f"- `{p}`" for p in paths]
    lines += ["", "See the SWI verification tests section of `AGENTS.md`."]
    return "\n".join(lines)


def main() -> int:
    text = report()
    if text:
        print(text)
    else:
        print("the verification notebooks are up to date", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
