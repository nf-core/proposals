<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/nfcore-proposals_logo_dark.png">
    <img alt="nf-core/proposals" src="docs/images/nfcore-proposals_logo_light.png">
  </picture>
</h1>

This repository is used to track all community proposals for nf-core.

## Proposer Documentation

To make a new proposal, please create a new issue in the repository following the appropriate template:

- [New pipeline](https://github.com/nf-core/proposals/issues/new?template=new_pipeline.yml)
- [New RFC](https://github.com/nf-core/proposals/issues/new?template=new_rfc.yml)
- [New special interest group](https://github.com/nf-core/proposals/issues/new?template=new_special_interest_group.yml)

## Curator Documentation

### Pipelines

**Automated workflow:**

- [x] Issue creation triggers automation that:
  - Adds the 'proposed' label
  - Creates a status comment tracking approvals
- [x] Team members use `/approve` or `/reject` commands in comments
- [x] Automation updates status comment and labels based on approvals
- [x] Acceptance requires either:
  - Two core team members
  - One core team member + one maintainer

**Manual steps required:**

- [ ] Facilitate discussion following [guidance here](https://nf-co.re/docs/checklists/community_governance/core_team#new-pipeline-proposals-and-onboarding)
- [ ] If accepted: Close issue as 'completed'
- [ ] If rejected: Close issue as 'not planned'
- [ ] For timed-out proposals (after 1 year): Add 'timed-out' label and close as 'not planned'
- [ ] Complete remaining onboarding tasks listed [here](https://nf-co.re/docs/checklists/community_governance/core_team#new-pipeline-proposals-and-onboarding)

### RFCs

**Automated workflow:**

- [x] Issue creation triggers automation that:
  - Adds the 'proposed' label
  - Creates a status comment tracking approvals
- [x] Team members use `/approve` or `/reject` commands in comments
- [x] Automation updates status comment and labels based on approvals
- [x] Acceptance requires core team quorum (majority of core team members)

**Manual steps required:**

- [ ] Facilitate discussion on the Issue thread
- [ ] If accepted: Close issue as 'completed'
- [ ] If rejected: Close issue as 'not planned'
- [ ] For timed-out proposals (after 1 year): Add 'timed-out' label and close as 'not planned'

### Special Interest Groups

**Manual workflow:**

- [ ] Once a issue is made, update the 'Project' status to 'proposed' (right hand side bar, under 'new-<TYPE>-proposals')
- [ ] Facilitate discussion on the the Issue thread, following the guidance [here](https://nf-co.re/blog/2024/special_interest_groups).
- [ ] Acceptance requires a minimum of OKs from:
  - Two members of the core team.
- [ ] If a proposal is accepted, update both the label AND status to 'accepted', and when closing select 'Close as completed'
- [ ] If a proposal is turned down, update both the label AND status to 'turned-down', and when closing select 'Close as not planned'
- [ ] If a proposal is not completed or abandoned after a year, update both the label AND status to 'timed-out', and when closing select 'Close as not planned'

### Request for Comment (RFC)

The curator workflow is as follows:

- [ ] Once a issue is made, update the 'Project' status to 'proposed' (right hand side bar, under 'new-<TYPE>-proposals')
- [ ] Facilitate discussion on the the Issue thread, following the guidance [here](https://nf-co.re/docs/contributing/project_proposals).
- [ ] Acceptance requires quorum from the nf-core core team, done via voting in comments with `/accept` or `/reject`
- [ ] If a proposal is turned down, update both the label AND status to 'turned-down', and when closing select 'Close as not planned'
- [ ] If a proposal is accepted, update both the label AND status to 'accepted', and ask the champion to write a formal RFC and begin initial development.
- [ ] When the PR is opened the corresponding issue can be closed.
- [ ] Verify that feedback has been provided to the champion.
- [ ] Propose an optional Bytesize talk about the proposal.
- [ ] Finally merge the PR when the development is complete.

## Developer Documentation

### Approval Automation Testing

The repository includes automated testing for the approval workflows to ensure reliability and correctness.

#### Test Suite

The approval automation is thoroughly tested with:

- **Unit Tests** (`approval.test.js`) - Tests individual ApprovalManager class methods
- **Integration Tests** (`workflow-integration.test.js`) - End-to-end workflow scenario testing

#### Automated Testing on PRs

A GitHub Actions workflow (`.github/workflows/test-approval-automation.yml`) automatically runs on pull requests that modify:

- `.github/workflows/lib/**` (approval automation code)
- `.github/workflows/pipeline_proposals.yml` (pipeline approval workflow)
- `.github/workflows/rfc_approval.yml` (RFC approval workflow)

The workflow includes:

1. **Test Execution** - Runs the full test suite
2. **Coverage Reporting** - Generates and uploads coverage reports
3. **PR Comments** - Posts coverage summary on pull requests
4. **Workflow Linting** - Validates GitHub Actions syntax
5. **Logic Validation** - Verifies approval logic correctness

#### Running Tests Locally

```bash
cd .github/workflows/lib

# Install dependencies
npm install

# Run tests
npm test

# Run with coverage
npm test:coverage

```
