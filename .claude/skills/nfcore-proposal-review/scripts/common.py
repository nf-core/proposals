"""Helpers shared by the proposal-review scripts."""

import json
import subprocess
import urllib.request
from functools import cache

PROPOSALS_REPO = "nf-core/proposals"
PIPELINES_JSON = "https://nf-co.re/pipelines.json"


class GhError(Exception):
    """A gh command failed; the message is its stderr."""


def gh(*args: str) -> str:
    """Run a gh command and return its stdout."""
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise GhError(out.stderr.strip() or out.stdout.strip())
    return out.stdout


def gh_json(*args: str):
    return json.loads(gh(*args))


def fetch_json(url: str, timeout: int = 30):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.load(resp)


@cache
def pipelines() -> list[dict]:
    """Every nf-core pipeline, as listed on the nf-core website."""
    return fetch_json(PIPELINES_JSON)["remote_workflows"]


def is_bot(login: str) -> bool:
    return login.endswith("bot") or login.endswith("[bot]")


def indent(lines: list[str], empty: str) -> str:
    """Lines indented by two spaces, or `empty` if there are none."""
    return "\n".join(f"  {line}" for line in lines) if lines else f"  {empty}"
