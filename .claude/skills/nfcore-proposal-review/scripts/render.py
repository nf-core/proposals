#!/usr/bin/env python3
"""Render a review JSON object (see review.schema.json) on stdin as the GitHub comment Markdown."""

import json
import re
import sys
from pathlib import Path

HEADER = (Path(__file__).parent.parent / "templates" / "header.md").read_text().strip()

NEXT_STEP_LABELS = {"blocker": "🚧 Blocker", "discuss": "💬 To discuss", "suggestion": "💡 Suggestion"}

# Both skip names already inside a link, URL or code span. Slack channels must
# start with a letter so issue refs (#193) and headings (## ) are left alone.
PIPELINE_RE = re.compile(r"(?<![\w/\[`])nf-core/([A-Za-z0-9_-]+)(?![\w-]*[\]`])")
SLACK_RE = re.compile(r"(?<![\w/\[`&#])#([a-z][a-z0-9_-]*)(?![\w-]*[\]`])")


def link_names(text: str) -> str:
    text = PIPELINE_RE.sub(r"[nf-core/\1](https://github.com/nf-core/\1)", text)
    return SLACK_RE.sub(r"[#\1](https://nfcore.slack.com/channels/\1)", text)


def point(title: str, details: list[str]) -> list[str]:
    return [f"- {title}", *(f"    - {d}" for d in details)]


def scale(score: int) -> str:
    return "🟢" if score >= 4 else "🟡" if score == 3 else "🔴"


def row(name: str, score: str, text: str) -> str:
    """A table row; model text is flattened and escaped so it can't break out of its cell."""
    text = " ".join(text.split()).replace("|", "\\|")
    return f"| **{name}** | {score} | {text} |"


def related_proposal(p: dict) -> str:
    """verify.py adds pipeline and status; without it, fall back to the bare number."""
    url = f"https://github.com/nf-core/proposals/issues/{p['number']}"
    label = p.get("pipeline") or f"nf-core/proposals#{p['number']}"
    detail = ", ".join(filter(None, [f"proposal #{p['number']}", p.get("status")]))
    return f"- [{label}]({url}) ({detail}) — {p['note']}"


def criterion(name: str, c: dict) -> str:
    if c["score"] is None:
        return row(name, "❓ —/5", c["note"])
    return row(name, f"{scale(c['score'])} {c['score']}/5", c["note"])


def render(r: dict) -> str:
    c = r["criteria"]
    lines = [
        HEADER,
        "",
        f"## Review score: {scale(r['overall'])} {r['overall']}/5",
        "",
        "| Criterion | Score | Notes |",
        "| --- | --- | --- |",
        criterion("Novelty", c["novelty"]),
        criterion("Specificity", c["specificity"]),
        criterion("Testability", c["testability"]),
        criterion("Sustainability", c["sustainability"]),
        "",
        "### Overlap",
        "",
        *(f"- {o['pipeline']} — {o['note']}" for o in r["overlap"]),
        *(related_proposal(p) for p in r["related_proposals"]),
        *([] if r["overlap"] or r["related_proposals"] else ["None identified."]),
        "",
        "## Summary",
        "",
        r["summary"],
        "",
        "## Why",
        "",
    ]
    for w in r["why"]:
        lines += point(f"**{w['title']}**", w["details"])

    if r["reviewers"]:
        by_pipeline: dict[str, list[str]] = {}
        for p in r["reviewers"]:
            by_pipeline.setdefault(p["pipeline"], []).append(f"@{p['login']}")
        lines += ["", "## Suggested reviewers", ""]
        lines += [f"- {', '.join(logins)} ({pipeline})" for pipeline, logins in by_pipeline.items()]

    if r["next_steps"]:
        lines += ["", "## Next steps", ""]
        for s in sorted(r["next_steps"], key=lambda s: list(NEXT_STEP_LABELS).index(s["kind"])):
            lines += point(f"**{NEXT_STEP_LABELS[s['kind']]}:** {s['title']}", s["details"])

    return link_names("\n".join(lines)) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render(json.load(sys.stdin)))
