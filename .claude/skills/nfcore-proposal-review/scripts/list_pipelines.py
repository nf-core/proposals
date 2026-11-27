#!/usr/bin/env python3
"""List all nf-core pipelines with status, description and topics.

Usage: python3 list_pipelines.py
"""

from common import pipelines


def main() -> None:
    for p in sorted(pipelines(), key=lambda p: p["name"]):
        if p["archived"]:
            status = " [archived]"
        elif not p["releases"]:
            status = " [in development]"
        else:
            status = ""
        topics = f" (topics: {', '.join(p['topics'])})" if p["topics"] else ""
        print(f"nf-core/{p['name']}{status}: {p['description'] or ''}{topics}")


if __name__ == "__main__":
    main()
