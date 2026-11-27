#!/usr/bin/env python3
"""For each proposed tool: is it an nf-core module, and which pipelines install it?

Usage: python3 check_tools.py fastp trimgalore star
"""

import sys
import time

from common import GhError, gh_json, indent

# GitHub code search allows 10 requests a minute.
SEARCH_INTERVAL_SECONDS = 7
NOT_PIPELINES = {"nf-core/modules", "nf-core/tools"}


def nf_core_modules() -> list[str] | None:
    """Every module in nf-core/modules, e.g. fastp or samtools/sort, from the repo tree."""
    try:
        tree = gh_json("api", "repos/nf-core/modules/git/trees/master:modules/nf-core?recursive=1")
    except GhError:
        return None
    return sorted(e["path"].removesuffix("/main.nf") for e in tree["tree"] if e["path"].endswith("/main.nf"))


def matching_modules(tool: str, modules: list[str]) -> list[str]:
    """Modules named after the tool, e.g. fastp, star/align or subread/featurecounts."""
    return [m for m in modules if m == tool or m.startswith(f"{tool}/") or m.endswith(f"/{tool}")]


def pipelines_installing(module: str) -> list[str]:
    hits = gh_json(
        "search", "code", f'"{module}"', "--owner", "nf-core", "--filename", "modules.json",
        "--limit", "100", "--json", "repository",
    )
    return sorted({h["repository"]["nameWithOwner"] for h in hits} - NOT_PIPELINES)


def main() -> None:
    tools = sys.argv[1:]
    if not tools:
        sys.exit("Usage: check_tools.py tool1 [tool2 ...]")

    # A failed lookup exits non-zero so the workflow can refuse a review built without it.
    failed = False
    modules = nf_core_modules()
    if modules is None:
        print("ERROR: could not list nf-core/modules, module results below are unknown")
        modules = []
        failed = True

    for i, tool in enumerate(tools):
        matches = matching_modules(tool.lower(), modules)
        print(f"### {tool}")
        print("nf-core/modules:")
        print(indent(matches, "(no module)"))

        if i > 0:
            time.sleep(SEARCH_INTERVAL_SECONDS)
        # Search for the module path when it is unambiguous, so subread/featurecounts is found.
        query = matches[0] if len(matches) == 1 else tool.lower()
        print(f"Pipelines that install '{query}' (from their modules.json):")
        try:
            print(indent(pipelines_installing(query), "(none)"))
        except GhError as e:
            print(f"  ERROR: search failed, result unknown: {e}")
            failed = True
        print()

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
