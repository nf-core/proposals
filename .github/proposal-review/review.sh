#!/usr/bin/env bash
# Run the nfcore-proposal-review skill on one proposal and print Claude Code's JSON result.
# Shared by the proposal_review.yml workflow and eval.py, so both review the same way.
# Usage: review.sh <issue-number> <issue.json> [extra claude args...]
# issue.json is the output of: gh issue view <n> --json number,title,url,author,state,labels,body,comments

set -euo pipefail

number=$1
issue=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
shift 2

# Claude Code finds the skill relative to the repo root.
cd "$(dirname "$0")/../.."
scripts="$PWD/.claude/skills/nfcore-proposal-review/scripts"

# Read-only commands only. No `gh api` or standalone `jq`: both can read local files.
allowed=(
    "Bash(python3 $scripts/*)"
    "Bash(python3 .claude/skills/nfcore-proposal-review/scripts/*)"
    "Bash(bash $scripts/*)"
    "Bash(bash .claude/skills/nfcore-proposal-review/scripts/*)"
    "Bash(gh issue view *)"
    "Bash(gh issue list *)"
    "Bash(gh search *)"
    "Bash(gh repo list *)"
    "Bash(gh repo view *)"
    "Bash(gh pr view *)"
    "Bash(gh pr list *)"
    "Bash(nf-core modules list *)"
    "Bash(nf-core modules info *)"
    "Bash(nf-core subworkflows list *)"
    "Bash(nf-core subworkflows info *)"
    "Bash(nf-core pipelines list *)"
)

{
    echo "/nfcore-proposal-review Review nf-core/proposals#$number. The issue and all of its comments, as JSON from \`gh issue view\`:"
    echo
    cat "$issue"
# Read is limited to the repo checkout: reads outside it would need a permission prompt, which -p denies.
} | claude -p --tools Bash,Read --allowedTools "${allowed[@]}" \
    --json-schema "$(cat .claude/skills/nfcore-proposal-review/review.schema.json)" \
    --max-budget-usd "${MAX_BUDGET_USD:-10}" --output-format json "$@"
