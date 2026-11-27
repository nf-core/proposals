#!/usr/bin/env python3
"""Check the review's overlap claims against nf-core before it is posted.

- Overlap pipelines must exist in nf-co.re/pipelines.json. One that doesn't, but matches a
    pipeline proposal (e.g. accepted, no repository yet), moves to related_proposals.
- Related proposals must be pipeline proposals in nf-core/proposals, and not one that already
    became a listed overlap pipeline. Title, author and status are filled in for the renderer.
- Reviewers must have contributed to their pipeline, or have written the overlapping proposal.

Usage: verify.py [current-issue-number] < review.json > verified.json
Anything dropped or moved is reported on stderr.
"""

import json
import re
import sys

from common import PROPOSALS_REPO, GhError, gh_json, pipelines

OUTCOMES = ["accepted", "merge-with-existing", "turned-down", "withdrawn", "timed-out"]


def log(msg: str) -> None:
    print(f"verify: {msg}", file=sys.stderr)


def pipeline_name(title: str) -> str | None:
    """nf-core/<name> from a proposal title such as "New pipeline: nf-core/<name>"."""
    m = re.search(r"nf-core/([A-Za-z0-9_-]+)", title)
    return f"nf-core/{m.group(1).lower()}" if m else None


def status(issue: dict) -> str:
    labels = {label["name"] for label in issue["labels"]}
    outcome = next((o for o in OUTCOMES if o in labels), None)
    return outcome or ("under discussion" if issue["state"] == "OPEN" else "closed")


def fetch_proposal(number: int) -> dict | None:
    try:
        issue = gh_json("issue", "view", str(number), "--repo", PROPOSALS_REPO, "--json", "number,title,state,labels,author")
    except GhError:
        return None
    return issue if "new-pipeline" in {label["name"] for label in issue["labels"]} else None


def find_proposal_for(pipeline: str) -> int | None:
    try:
        hits = gh_json(
            "search", "issues", pipeline, "--repo", PROPOSALS_REPO, "--label", "new-pipeline",
            "--json", "number,title", "--limit", "10",
        )
    except GhError:
        return None
    return next((h["number"] for h in hits if pipeline_name(h["title"]) == pipeline.lower()), None)


def check_overlap(review: dict, known: set[str]) -> None:
    kept = []
    for o in review["overlap"]:
        if o["pipeline"].lower() in known:
            kept.append(o)
        elif (number := find_proposal_for(o["pipeline"])) is not None:
            log(f"moved {o['pipeline']} to related proposals as #{number}")
            review["related_proposals"].append({"number": number, "note": o["note"]})
        else:
            log(f"dropped overlap {json.dumps(o)}")
    review["overlap"] = kept


def check_related_proposals(review: dict, current: int | None) -> None:
    listed = {o["pipeline"].lower() for o in review["overlap"]}
    seen, kept = {current}, []
    for p in review["related_proposals"]:
        if p["number"] in seen:
            continue
        seen.add(p["number"])
        issue = fetch_proposal(p["number"])
        if not issue:
            log(f"dropped related proposal {json.dumps(p)}")
        elif (name := pipeline_name(issue["title"])) in listed:
            log(f"dropped related proposal #{p['number']}: {name} is already listed as a pipeline")
        else:
            details = {"title": issue["title"], "pipeline": name, "author": issue["author"]["login"], "status": status(issue)}
            kept.append({**p, **details})
    review["related_proposals"] = kept


def check_reviewers(review: dict, contributors: dict[str, set[str]]) -> None:
    proposers = {(p["pipeline"], p["author"].lower()) for p in review["related_proposals"] if p["pipeline"]}
    kept = []
    for r in review["reviewers"]:
        pipeline, login = r["pipeline"].lower(), r["login"].lower()
        if login in contributors.get(pipeline, set()) or (pipeline, login) in proposers:
            kept.append(r)
        else:
            log(f"dropped reviewer {json.dumps(r)}")
    review["reviewers"] = kept


def main() -> None:
    current = int(sys.argv[1]) if len(sys.argv) > 1 else None
    review = json.load(sys.stdin)
    contributors = {f"nf-core/{p['name']}".lower(): {c["name"].lower() for c in p["contributors"]} for p in pipelines()}

    check_overlap(review, set(contributors))
    check_related_proposals(review, current)
    check_reviewers(review, contributors)
    json.dump(review, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
