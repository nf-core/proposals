- Start Date: 2025-09-09
- Reference Issues: https://github.com/nf-core/proposals/issues/89
- Implementation PR: https://github.com/nf-core/website/pull/3718

# Summary

nf-core pipelines widely adopted in the community should adhere more strictly to the best practices promoted by nf-core, as they serve as templates and references for the development of the other pipelines.

# Champion

[@JoseEspinosa](https://github.com/joseespinosa)

# Background & Motivation

Derived from the proposal here: https://github.com/nf-core/proposals/issues/61, some members of the core team and community were not comfortable to immediately start 'blindly' allowing LLM associated code within the nf-core ecosystem, primarily due to:

- Quality of code in some PRs
- Concerns about the legality/lack of attribution
- Adding a lot of extra cruft to the template purely to try and make sure AI agents 'do the right thing' being a bad thing

with particularly the first point ending up putting more work on community coordinators/managers.

Generally there was an agreement that LLMs are here to stay, and we cannot avoid them.

But there was a feeling we need to at least make a statement on our stance on them and possibly a policy document.

### Goals

- Increase visibility of nf-core pipelines that are widely adopted in the community.
- Promote best development practices and enforce recommended guidelines for popular pipelines.
- Provide a model for other pipelines to align with and adopt these practices.

### Non-Goals

- The tier system is not meant to devalue or discourage work on less widely adopted pipelines.
- Standard nf-core practices still apply to all pipelines; VIP adds extra expectations, not new requirements for everyone.
- Criteria (e.g. stars, PRs, forks) are indicative, not strict thresholds, and may evolve organically.

# Detailed Design

## Naming

The name of the tier could be **VIP (Very Important Pipelines)**

## Selection

There are no strict thresholds. Selection will be based on an overall assessment by the nf-core core team, considering factors such as:

- Number of pull requests and contributors
- Repository stars and forks
- Pipeline age and stability
- Issue volume and responsiveness
- Website traffic and usage indicators

Selection is expected to evolve organically as pipelines grow and mature.

## Recommendations

### Team and governance

Very Important Pipelines should demonstrate shared ownership and active governance.

Recommended practices:

- A team of active co-developers
- A dedicated GitHub team
- Defined code owners using CODEOWNERS
- Regular development meetings, open to the community
- Use of milestones to plan and track releases
- A developer focused Slack channel, separate from user support

### Development and maintenance

Very Important Pipelines should maintain a high standard of technical quality and currency.

Recommended practices:

- Regular review of default configuration usage
- Pipeline template and tool versions kept within two releases of current
- Automated testing coverage above eighty percent
- Clear issue advisories when known problems are identified
- Participation in an nf-core bytesize talk

### Documentation and user experience

Very Important Pipelines should set the standard for clarity and usability.

Recommended practices:

- A pipeline logo and associated visual assets
- A pipeline metro map
- Extended documentation beyond the minimum requirements
- All outputs fully described in the documentation
- Practical usage tutorials for common workflows

# Drawbacks

None noted.

# Alternatives

None noted.

# Adoption strategy

- [x] Update pipelines documentation: https://github.com/nf-core/website/pull/3718
- [ ] Made a blog post to announce the VIP tier

# Unresolved Questions

None noted.

# References

- https://github.com/nf-core/proposals/issues/89
- https://github.com/nf-core/website/pull/3718
