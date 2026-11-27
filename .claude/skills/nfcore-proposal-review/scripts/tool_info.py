#!/usr/bin/env python3
"""Look up proposed tools on bio.tools and Bioconda / conda-forge: description, licence, publications.

Usage: python3 tool_info.py fastp star
"""

import re
import sys
import urllib.error

from common import fetch_json

BIOTOOLS_URL = "https://bio.tools/api/tool/{}?format=json"
CONDA_URL = "https://api.anaconda.org/package/{}"
# Tried in order; R and Bioconductor packages are prefixed on conda.
CONDA_PACKAGES = ["bioconda/{}", "conda-forge/{}", "bioconda/bioconductor-{}", "conda-forge/r-{}", "bioconda/r-{}"]


class FetchError(Exception):
    """A lookup failed for a reason other than "not found"."""


def get(url: str) -> dict | None:
    """The JSON at *url*, or None if it doesn't exist (404)."""
    try:
        return fetch_json(url, timeout=20)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise FetchError(f"HTTP {e.code} from {url}") from e
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise FetchError(f"{url}: {e}") from e


def biotools(tool: str) -> list[str]:
    entry = get(BIOTOOLS_URL.format(tool))
    if not entry:
        return [f"(no bio.tools entry with id '{tool}')"]
    dois = [p["doi"] for p in entry.get("publication") or [] if p.get("doi")]
    operations = sorted({op["term"] for f in entry.get("function") or [] for op in f.get("operation") or []})
    return [
        f"{entry['name']}: {(entry.get('description') or '')[:300]}",
        f"licence: {entry.get('license') or 'not stated'}",
        f"homepage: {entry.get('homepage') or 'none'}",
        f"publications: {', '.join(dois) or 'none listed'}",
        f"operations: {', '.join(operations)}",
    ]


def conda(tool: str) -> list[str]:
    for pattern in CONDA_PACKAGES:
        package = pattern.format(tool)
        if info := get(CONDA_URL.format(package)):
            return [
                f"{package} {info['latest_version']}, licence: {info.get('license') or 'not stated'}",
                info.get("summary") or "",
            ]
    return [f"(not on bioconda or conda-forge as '{tool}', 'r-{tool}' or 'bioconductor-{tool}')"]


def main() -> None:
    tools = sys.argv[1:]
    if not tools:
        sys.exit("Usage: tool_info.py tool1 [tool2 ...]")

    failed = False
    for tool in tools:
        print(f"### {tool}")
        name = tool.lower()
        # The name goes into URLs.
        if not re.fullmatch(r"[a-z0-9._+-]+", name):
            print("  (skipped: not a plain package name)")
            continue
        for section, lookup in (("bio.tools", biotools), ("Conda", conda)):
            print(f"{section}:")
            try:
                lines = lookup(name)
            except FetchError as e:
                lines = [f"ERROR: lookup failed, result unknown: {e}"]
                failed = True
            print("\n".join(f"  {line}" for line in lines))
        print()

    # A failed lookup exits non-zero so the workflow can refuse a review built without it.
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
