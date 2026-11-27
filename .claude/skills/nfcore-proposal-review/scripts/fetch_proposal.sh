#!/usr/bin/env bash
# Fetch a proposal by issue number, or list all open proposals.
# Usage: bash fetch_proposal.sh 147     → fetch issue #147
#        bash fetch_proposal.sh          → list all open proposals

set -uo pipefail

if [[ $# -ge 1 ]]; then
    gh issue view "$1" --repo nf-core/proposals
else
    gh issue list --repo nf-core/proposals --label new-pipeline --state open --limit 50
fi
