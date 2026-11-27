#!/usr/bin/env python3
"""Replay already-decided proposals through the review skill and compare its scores with the decisions.

Each proposal is replayed as it looked before the decision: outcome labels removed and comments
cut at the first /approve or /reject vote. Proposals cited in references/examples.md are skipped.
Older proposals, decided before voting commands existed, may still contain the decision in the
discussion, so treat their results with care.

Usage:
    python3 .github/proposal-review/eval.py                  # newest 3 of each outcome
    python3 .github/proposal-review/eval.py 147 177          # specific proposals
    python3 .github/proposal-review/eval.py --per-outcome 5 --model opus

Uses your local Claude Code login, or Bedrock if CLAUDE_CODE_USE_BEDROCK is set.
Each review costs a few dollars.
"""

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REPO = "nf-core/proposals"
OUTCOMES = ["accepted", "merge-with-existing", "turned-down"]
VOTE_RE = re.compile(r"^\s*/(approve|reject)\b", re.MULTILINE)
CUTOFF_FILE = ROOT / ".proposal-review-cutoff"
ISSUE_FIELDS = "number,title,url,author,state,labels,body,comments"


def gh_json(*args: str):
    return json.loads(subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout)


def held_out() -> set[int]:
    examples = (ROOT / ".claude/skills/nfcore-proposal-review/references/examples.md").read_text()
    return {int(n) for n in re.findall(r"nf-core/proposals#(\d+)", examples)}


def outcome(issue: dict) -> str | None:
    """The single outcome label, or None if there's none or it's ambiguous."""
    found = [o for o in OUTCOMES if o in {label["name"] for label in issue["labels"]}]
    return found[0] if len(found) == 1 else None


def sample(per_outcome: int, skip: set[int]) -> list[int]:
    numbers = []
    for o in OUTCOMES:
        issues = gh_json(
            "issue", "list", "-R", REPO, "--state", "closed", "--label", "new-pipeline", "--label", o,
            "--limit", "100", "--json", "number,labels",
        )
        numbers += [i["number"] for i in issues if i["number"] not in skip and outcome(i) == o][:per_outcome]
    return numbers


def as_undecided(issue: dict) -> dict:
    comments = []
    for c in issue["comments"]:
        if VOTE_RE.search(c["body"]):
            break
        login = (c.get("author") or {}).get("login", "")
        if not login.endswith("bot") and login != "github-actions":
            comments.append(c)
    return {**issue, "state": "OPEN", "labels": [{"name": "new-pipeline"}], "comments": comments}


def review(number: int, model: str | None, out: Path) -> dict:
    issue_path = out / f"{number}.issue.json"
    issue_path.write_text(json.dumps(as_undecided(gh_json("issue", "view", str(number), "-R", REPO, "--json", ISSUE_FIELDS))))
    cmd = ["bash", str(HERE / "review.sh"), str(number), str(issue_path)] + (["--model", model] if model else [])
    CUTOFF_FILE.write_text(str(number))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        CUTOFF_FILE.unlink(missing_ok=True)
    (out / f"{number}.result.json").write_text(result.stdout)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": result.stderr[-500:]}


def fmt(score) -> str:
    return "?" if score is None else str(score)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("numbers", nargs="*", type=int, help="proposal issue numbers (default: a sample)")
    parser.add_argument("--per-outcome", type=int, default=3)
    parser.add_argument("--model")
    parser.add_argument("--out", type=Path, help="directory for results (default: a new temp dir)")
    args = parser.parse_args()

    out = args.out or Path(tempfile.mkdtemp(prefix="proposal-review-eval-"))
    out.mkdir(parents=True, exist_ok=True)
    numbers = args.numbers or sample(args.per_outcome, held_out())
    print(f"Reviewing {len(numbers)} proposals; results in {out}\n")
    print("| Proposal | Decided | Overall | Novelty | Specificity | Testability | Sustainability | Cost |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")

    by_outcome: dict[str, list[int]] = {}
    total_cost = 0.0
    for n in numbers:
        decided = outcome(gh_json("issue", "view", str(n), "-R", REPO, "--json", "labels")) or "unclear"
        res = review(n, args.model, out)
        total_cost += res.get("total_cost_usd") or 0
        r = res.get("structured_output")
        if res.get("is_error") or not r:
            print(f"| #{n} | {decided} | ERROR: {str(res.get('result', ''))[:80]} | | | | | |")
            continue
        c = r["criteria"]
        by_outcome.setdefault(decided, []).append(r["overall"])
        scores = " | ".join(fmt(c[k]["score"]) for k in ("novelty", "specificity", "testability", "sustainability"))
        print(f"| #{n} | {decided} | {r['overall']} | {scores} | ${res.get('total_cost_usd', 0):.2f} |", flush=True)

    print("\nMean overall score by decision (higher should mean more likely accepted):")
    for o, scores in by_outcome.items():
        print(f"  {o}: {sum(scores) / len(scores):.1f} (n={len(scores)})")
    print(f"\nTotal cost: ${total_cost:.2f}")


if __name__ == "__main__":
    main()
