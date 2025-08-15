# GitHub Approval Automation

This module contains the `ApprovalManager` class used by GitHub Actions workflows to automate the approval process for pipeline proposals and RFCs.

## Files

- `approval.js` - The main ApprovalManager class
- `approval.test.js` - Unit tests for ApprovalManager class
- `workflow-integration.test.js` - Integration tests for complete workflow scenarios
- `package.json` - Node.js package configuration with Jest setup
- `README.md` - This documentation file

## ApprovalManager Class

The `ApprovalManager` class handles:

- Fetching team members from GitHub organization teams
- Processing comments to track approvals and rejections via `/approve` and `/reject` commands
- Updating issue status and labels based on approval state
- Managing status comments on issues

### Usage Scenarios

#### Pipeline Proposals

- **Approval Criteria**: Either 2 core team members OR 1 core team member + 1 maintainer
- **Issue Title Pattern**: Must start with "New Pipeline"
- **Team Roles**: Both core team and maintainers can vote

#### RFC Proposals

- **Approval Criteria**: Quorum of core team members (Math.ceil(coreTeamMembers.length / 2))
- **Issue Title Pattern**: Must start with "New RFC"
- **Team Roles**: Only core team members can vote

## Running Tests

### Prerequisites

Install Node.js and npm, then install Jest:

```bash
npm install
```

### Test Commands

```bash
# Run all tests
npm test

# Run tests in watch mode (reruns on file changes)
npm test:watch

# Run tests with coverage report
npm test:coverage
```

## Test Suite

The test suite includes both unit tests and integration tests:

### Unit Tests (`approval.test.js`)

Tests individual methods and functionality of the ApprovalManager class.

### Integration Tests (`workflow-integration.test.js`)

End-to-end tests that simulate complete workflow scenarios as they would run in GitHub Actions.

## Test Coverage

The combined test suites cover:

### Core Functionality

- ✅ Constructor initialization
- ✅ Team member fetching from GitHub API
- ✅ Comment processing with `/approve` and `/reject` commands
- ✅ Status comment updates
- ✅ Issue label management

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
