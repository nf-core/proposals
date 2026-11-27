#!/usr/bin/env python3
"""List nf-core pipelines with status, description and topics.

With search terms, only pipelines whose name, description or topics contain any of
them (case-insensitive). The full list is too long for the agent to read in one go.

Usage: python3 list_pipelines.py [term1 term2 ...]
"""

import sys

from common import pipelines


def describe(p: dict) -> str:
    if p["archived"]:
        status = " [archived]"
    elif not p["releases"]:
        status = " [in development]"
    else:
        status = ""
    topics = f" (topics: {', '.join(p['topics'])})" if p["topics"] else ""
    return f"nf-core/{p['name']}{status}: {p['description'] or ''}{topics}"


def main() -> None:
    terms = [t.lower() for t in sys.argv[1:]]
    lines = [describe(p) for p in sorted(pipelines(), key=lambda p: p["name"])]
    matches = [line for line in lines if not terms or any(t in line.lower() for t in terms)]
    print("\n".join(matches) if matches else f"(no pipelines match: {' '.join(sys.argv[1:])})")


if __name__ == "__main__":
    main()
