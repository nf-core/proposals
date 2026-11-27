#!/usr/bin/env python3
"""Show who drives a pipeline: code owners, top contributors, and recent committers.

Usage: python3 maintainers.py rnaseq   (or nf-core/rnaseq)
"""

import re
import sys
from collections import Counter

from common import GhError, gh, gh_json, indent, is_bot, pipelines


def code_owners(pipeline: str) -> str:
    try:
        text = gh("api", "-H", "Accept: application/vnd.github.raw", f"repos/nf-core/{pipeline}/contents/.github/CODEOWNERS")
    except GhError:
        return indent([], "(none)")
    rules = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    return indent(rules, "(empty)")


def top_contributors(pipeline: str) -> str:
    match = next((p for p in pipelines() if p["name"] == pipeline), None)
    if match is None:
        return indent([], "(pipeline not found)")
    people = [c for c in match["contributors"] if not is_bot(c["name"])][:10]
    return indent([f"{c['name']}: {c['count']}" for c in people], "(none)")


def recent_committers(pipeline: str) -> str:
    try:
        commits = gh_json("api", f"repos/nf-core/{pipeline}/commits?per_page=100")
    except GhError:
        return "  ERROR: could not list commits"
    logins = [c["author"]["login"] for c in commits if c.get("author") and not is_bot(c["author"]["login"])]
    ranked = sorted(Counter(logins).items(), key=lambda item: (-item[1], item[0]))[:8]
    return indent([f"{login}: {n}" for login, n in ranked], "(none)")


def main() -> None:
    pipeline = (sys.argv[1] if len(sys.argv) > 1 else "").removeprefix("nf-core/")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", pipeline):
        sys.exit("Usage: maintainers.py <pipeline>")

    print("CODEOWNERS:")
    print(code_owners(pipeline))
    print("Top contributors (commits, all time):")
    print(top_contributors(pipeline))
    print("Most active in the last 100 commits:")
    print(recent_committers(pipeline))


if __name__ == "__main__":
    main()
