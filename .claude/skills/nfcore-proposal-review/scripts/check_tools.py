#!/usr/bin/env python3
"""For each proposed tool: is it an nf-core module, and which pipelines install it?

Usage: python3 check_tools.py fastp trimgalore star
"""

import sys
import urllib.error
from concurrent.futures import ThreadPoolExecutor

from common import GhError, fetch_json, gh_json, indent, pipelines

MODULES_JSON_URL = "https://raw.githubusercontent.com/nf-core/{name}/{default_branch}/modules.json"


def nf_core_modules() -> list[str] | None:
    """Every module in nf-core/modules, e.g. fastp or samtools/sort, from the repo tree."""
    try:
        tree = gh_json("api", "repos/nf-core/modules/git/trees/master:modules/nf-core?recursive=1")
    except GhError:
        return None
    return sorted(e["path"].removesuffix("/main.nf") for e in tree["tree"] if e["path"].endswith("/main.nf"))


def installed_modules(pipeline: dict) -> set[str] | None:
    """nf-core modules listed in the pipeline's modules.json. Empty if it has none (older pipelines)."""
    try:
        data = fetch_json(MODULES_JSON_URL.format(**pipeline), timeout=20)
    except urllib.error.HTTPError as e:
        return set() if e.code == 404 else None
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None
    return {m for repo in data.get("repos", {}).values() for m in repo.get("modules", {}).get("nf-core", {})}


def modules_by_pipeline() -> tuple[dict[str, set[str]], list[str]]:
    """Installed modules per pipeline, plus the pipelines whose modules.json couldn't be read."""
    all_pipelines = pipelines()
    with ThreadPoolExecutor(16) as pool:
        results = list(pool.map(installed_modules, all_pipelines))
    found = {f"nf-core/{p['name']}": mods for p, mods in zip(all_pipelines, results) if mods is not None}
    failed = [f"nf-core/{p['name']}" for p, mods in zip(all_pipelines, results) if mods is None]
    return found, failed


def matching_modules(tool: str, modules: list[str]) -> list[str]:
    """Modules named after the tool, e.g. fastp, star/align or subread/featurecounts."""
    return [m for m in modules if m == tool or m.startswith(f"{tool}/") or m.endswith(f"/{tool}")]


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
    installed, unreadable = modules_by_pipeline()
    if unreadable:
        print(f"ERROR: could not read modules.json for {', '.join(unreadable)}, pipeline results are incomplete")
        failed = True

    for tool in tools:
        matches = matching_modules(tool.lower(), modules)
        print(f"### {tool}")
        print("nf-core/modules:")
        print(indent(matches, "(no module)"))
        # Match every module named after the tool, so samtools covers samtools/sort, samtools/index, ...
        wanted = set(matches) or {tool.lower()}
        users = sorted(p for p, mods in installed.items() if mods & wanted)
        print("Pipelines that install it (from their modules.json):")
        print(indent(users, "(none)"))
        print()

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
