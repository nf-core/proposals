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


def get(url: str) -> dict | None:
    try:
        return fetch_json(url, timeout=20)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


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

    for tool in tools:
        print(f"### {tool}")
        name = tool.lower()
        # The name goes into URLs.
        if not re.fullmatch(r"[a-z0-9._+-]+", name):
            print("  (skipped: not a plain package name)")
            continue
        print("bio.tools:")
        print("\n".join(f"  {line}" for line in biotools(name)))
        print("Conda:")
        print("\n".join(f"  {line}" for line in conda(name)))
        print()


if __name__ == "__main__":
    main()
