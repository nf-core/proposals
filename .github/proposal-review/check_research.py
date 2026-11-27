#!/usr/bin/env python3
"""Fail unless each core research script ran successfully at least once during the review.

A review written without this research is guesswork, so the workflow stops before posting it.
Reads Claude Code's `--output-format stream-json` log. A run counts as successful if the command
exited zero and its output has no ERROR line or traceback (an agent may pipe the output through
`head`, which hides the script's exit code).

Usage: check_research.py stream.jsonl
"""

import json
import sys

REQUIRED = ["check_tools.py", "tool_info.py", "list_pipelines.py", "similar_proposals.py"]
FAILURE_MARKERS = ["ERROR:", "Traceback (most recent call last)"]


def result_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content)
    return content or ""


def main() -> None:
    commands: dict[str, str] = {}
    succeeded: set[str] = set()
    with open(sys.argv[1]) as log:
        for line in log:
            message = json.loads(line).get("message")
            content = message.get("content") if isinstance(message, dict) else None
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "tool_use" and block.get("name") == "Bash":
                    commands[block["id"]] = block["input"].get("command", "")
                elif block.get("type") == "tool_result" and block.get("tool_use_id") in commands:
                    text = result_text(block)
                    if not block.get("is_error") and not any(m in text for m in FAILURE_MARKERS):
                        succeeded.update(s for s in REQUIRED if s in commands[block["tool_use_id"]])

    missing = [s for s in REQUIRED if s not in succeeded]
    if missing:
        print(f"::error::These research scripts never ran successfully: {', '.join(missing)}. Not posting the review.")
        sys.exit(1)
    print("All research scripts ran successfully.")


if __name__ == "__main__":
    main()
