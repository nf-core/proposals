# GitHub Approval Automation

This module contains the `ApprovalManager` class and CLI scripts used by GitHub Actions workflows to automate the approval process for pipeline proposals, RFCs, and SIG proposals.

## Files

- `approval.py` - The main ApprovalManager class (Python)
- `scripts/` - Click-based CLI scripts for different proposal types
  - `sig_approval.py` - SIG proposal automation
  - `rfc_approval.py` - RFC proposal automation
  - `pipeline_approval.py` - Pipeline proposal automation
- `tests/` - Pytest test suite
  - `test_approval.py` - Unit tests for ApprovalManager class
  - `test_workflow_integration.py` - Integration tests for complete workflow scenarios
- `pyproject.toml` - Python package configuration with pytest setup
- `README.md` - This documentation file

## ApprovalManager Class

The `ApprovalManager` class handles:

- Fetching team members from GitHub organization teams
- Processing comments to track approvals and rejections via `/approve` and `/reject` commands
- Updating issue status and labels based on approval state
- Managing status comments on issues

### Usage Scenarios

#### SIG Proposals

- **Approval Criteria**: 2 core team members
- **Issue Title Pattern**: Must start with "New special interest group"
- **Team Roles**: Only core team members can vote

#### RFC Proposals

- **Approval Criteria**: Quorum of core team members (ceil(coreTeamMembers.length / 2))
- **Issue Title Pattern**: Must start with "New RFC"
- **Team Roles**: Only core team members can vote

#### Pipeline Proposals

- **Approval Criteria**: Either 2 core team members OR 1 core team member + 1 maintainer
- **Issue Title Pattern**: Must start with "New pipeline"
- **Team Roles**: Both core team and maintainers can vote

## CLI Scripts

Each proposal type has its own Click-based CLI script that can be run directly:

### SIG Approval Script

```bash
uv run python scripts/sig_approval.py \
  --github-token="<token>" \
  --org="nf-core" \
  --repo="proposals" \
  --issue-number=123 \
  --event-name="issue_comment" \
  --event-action="created"
```

### RFC Approval Script

```bash
uv run python scripts/rfc_approval.py \
  --github-token="<token>" \
  --org="nf-core" \
  --repo="proposals" \
  --issue-number=123 \
  --event-name="issue_comment" \
  --event-action="created"
```

### Pipeline Approval Script

```bash
uv run python scripts/pipeline_approval.py \
  --github-token="<token>" \
  --org="nf-core" \
  --repo="proposals" \
  --issue-number=123 \
  --event-name="issue_comment" \
  --event-action="created"
```

## Running Tests

### Prerequisites

Install Python 3.11+ and uv for dependency management:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### Test Commands

```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=. --cov-report=html

# Run tests in verbose mode
uv run pytest -v
```

## Test Suite

The test suite includes both unit tests and integration tests:

### Unit Tests (`test_approval.py`)

Tests individual methods and functionality of the ApprovalManager class.

### Integration Tests (`test_workflow_integration.py`)

End-to-end tests that simulate complete workflow scenarios as they would run in GitHub Actions.

## Test Coverage

The combined test suites cover:

### Core Functionality

- ✅ Constructor initialization
- ✅ Team member fetching from GitHub API
- ✅ Comment processing with `/approve` and `/reject` commands
- ✅ Status comment updates
- ✅ Issue label management

### SIG Proposal Scenarios

- ✅ Approval with 2 core members
- ✅ No approval with only 1 core member
- ✅ Ignoring maintainer votes (core-only)

### Pipeline Proposal Scenarios

- ✅ Approval with 2 core members
- ✅ Approval with 1 core + 1 maintainer
- ✅ No approval with only 1 core member
- ✅ No approval with only maintainers

### RFC Proposal Scenarios

- ✅ Approval with core team quorum
- ✅ No approval without quorum
- ✅ Quorum calculation for different team sizes
- ✅ Ignoring maintainer votes (core-only)

### Edge Cases

- ✅ Case-insensitive commands (`/APPROVE`, `/reject`)
- ✅ Commands only at start of line
- ✅ Multiple commands from same user
- ✅ Multiple commands within same comment
- ✅ Non-team member comments (ignored)
- ✅ Empty or malformed comments
- ✅ Mixed line endings
- ✅ Users in both core and maintainer teams

### Error Handling

- ✅ GitHub API errors
- ✅ Empty comment arrays
- ✅ Null/undefined comment bodies
- ✅ Malformed regex patterns

## Command Format

The approval system recognizes these commands when they appear at the start of a line in a comment:

- `/approve` - Approve the proposal
- `/reject` - Reject the proposal

Commands are case-insensitive and can include additional text after the command.

### Examples

```
/approve
```

```
/approve This looks good to me!
```

```
/reject
This needs more work before approval.
```

```
I have some concerns.
/reject
```

## Status Labels

The system manages these issue labels:

- `proposed` - Initial state for new proposals
- `accepted` - Proposal has sufficient approvals
- `turned-down` - Proposal was rejected
- `timed-out` - Proposal expired without sufficient votes
