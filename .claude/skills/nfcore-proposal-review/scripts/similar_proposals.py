#!/usr/bin/env python3
"""Find earlier pipeline proposals matching any of the given search terms, with their outcome.

Usage: python3 similar_proposals.py proteomics olink "targeted panel"
"""

import sys
from pathlib import Path

from common import PROPOSALS_REPO, GhError, gh_json

# eval.py writes this file so a replayed proposal can't see its own outcome or later decisions.
CUTOFF_FILE = Path(".proposal-review-cutoff")


def cutoff() -> float:
    try:
        return int(CUTOFF_FILE.read_text().strip())
    except (OSError, ValueError):
        return float("inf")


def main() -> None:
    terms = sys.argv[1:]
    if not terms:
        sys.exit("Usage: similar_proposals.py term1 [term2 ...]")

    found, failed = {}, False
    for term in terms:
        try:
            hits = gh_json(
                "search", "issues", term, "--repo", PROPOSALS_REPO, "--label", "new-pipeline",
                "--limit", "15", "--json", "number,title,state,labels",
            )
        except GhError:
            print(f"ERROR: search for '{term}' failed")
            failed = True
            continue
        found.update({h["number"]: h for h in hits if h["number"] < cutoff()})

    for number, h in sorted(found.items()):
        labels = ", ".join(label["name"] for label in h["labels"] if label["name"] != "new-pipeline")
        print(f"#{number} [{h['state']}] {h['title']} (labels: {labels})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
