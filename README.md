<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/nfcore-proposals_logo_dark.png">
    <img alt="nf-core/proposals" src="docs/images/nfcore-proposals_logo_light.png">
  </picture>
</h1>

This repository is used to track all community proposals for nf-core.

## Proposer Documentation

To make a new proposal for a pipeline, please create a new issue in the repository following the template provided:

- [New pipeline](https://github.com/nf-core/proposals/issues/new?template=new_pipeline.yml)

To make a new proposal for a special interest group, please create a new issue in the repository following the template provided:

- [New special interest group](https://github.com/nf-core/proposals/issues/new?template=new_special_interest_group.yml)

## Curator Documentation

### Pipelines

The curator workflow is as follows:

- [ ] Once a issue is made, a Github Actions workflow will:
  - Add the 'proposed' label
  - Create a status comment tracking approvals
- [ ] Facilitate discussion on the the Issue thread, following the guidance [here](https://nf-co.re/docs/checklists/community_governance/core_team#new-pipeline-proposals-and-onboarding).
- [ ] Acceptance requires a minimum of OKs from:
  - Two members of the core team.
  - One member of the core team and one member of the maintainers team.
- [ ] Core and maintainer members can use the following commands in comments:
  - `/approve` - to approve the proposal
  - `/reject` - to reject the proposal
- [ ] The automation will:
  - Track approvals and rejections
  - Update the status comment
  - Update labels based on the current status
- [ ] If a proposal is accepted:
  - Update the status to 'accepted'
  - Close the issue as 'completed'
- [ ] If a proposal is turned down:
  - Update the status to 'turned-down'
  - Close the issue as 'not planned'
- [ ] If a proposal is not completed or abandoned after a year:
  - Add the 'timed-out' label
  - Close the issue as 'not planned'
- [ ] Complete the remaining new-pipeline onboarding tasks listed [here](https://nf-co.re/docs/checklists/community_governance/core_team#new-pipeline-proposals-and-onboarding)

### Special Interest Groups

The curator workflow is as follows:

- [ ] Once a issue is made, update the 'Project' status to 'proposed' (right hand side bar, under 'new-<TYPE>-proposals')
- [ ] Facilitate discussion on the the Issue thread, following the guidance [here](https://nf-co.re/blog/2024/special_interest_groups).
- [ ] Acceptance requires a minimum of OKs from:
  - Two members of the core team.
- [ ] If a proposal is accepted, update both the label AND status to 'accepted', and when closing select 'Close as completed'
- [ ] If a proposal is turned down, update both the label AND status to 'turned-down', and when closing select 'Close as not planned'
- [ ] If a proposal is not completed or abandoned after a year, update both the label AND status to 'timed-out', and when closing select 'Close as not planned'
