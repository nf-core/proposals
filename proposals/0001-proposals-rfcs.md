- Start Date: 2025-05-26
- Reference Issues: https://github.com/nf-core/proposals/issues/30
- Implementation PR: https://github.com/nf-core/website/pull/3367

> [!NOTE]
> This is the first ever nf-core RFC and a bit of a special case. This issue comes after discussion with the @nf-core/core and some initial drafting work in Google Docs. I have copied out relevant chunks of what we have written into this issue and will port over the rest of the details into a PR once the issue is approved - as per the new proposed RFC procedure!

# Summary

The nf-core ‘Request for Comment’ (RFC) process is designed to give the community a voice and visibility to large projects that affect the entire community.

<dl><dt>RFC (Request for Comment):</dt>
<dd>A formal proposal submitted for discussion, typically involving significant changes or new features. An RFC outlines the motivation, requirements, and steps necessary for implementation, and invites feedback and collaboration from the community before a final decision is made.</dd>

<dt>Proposal champion:</dt>
<dd>An individual who takes ownership of advancing a proposal through the RFC process. This role is self-nominated and open to anyone, including both project maintainers and other community members. The champion may be the original author of the proposal or someone who joins later. Responsibilities include drafting the detailed RFC, managing and integrating community feedback, and helping to guide the implementation of the proposal.</dd>
</dl>

# Champion

[@ewels](https://github.com/ewels)

# Background & Motivation

Until now, major nf-core projects have been discussed and agreed upon by the @nf-core/core team, sometimes reaching out to @nf-core/maintainers and other groups as necessary. Once approved, work proceeds and in some cases those who are affected in the community only find out about projects once the changes go live.

We want to improve visibility and transparency around such projects so that community members are aware of potential upcoming projects and have the ability to comment, contribute and shape them before they come into effect.

Not every project in nf-core requires an RFC. The process should only be used for efforts that will affect a significant proportion of community members. For example:

- Changes to established development / code standardisation
- Creation of new nf-core fundamental product / initiative
- Changes to base dependencies and requirements that span many pipelines

As a rule of thumb, if a proposal will require changes across two or more different repositories, it is a good candidate for an RFC. Projects that are smaller in scope should typically be raised as a new issue on the relevant GitHub repository instead.

# Goals

- Improve visibility of upcoming nf-core projects that affect much of the community
- Provide venue for open feedback and discussion before implementation of projects

# Non-Goals

- Excess bureaucracy where it is not warranted
- Increased barriers for contribution

# Detailed Design

Should be implemented primary as documentation in the nf-core/website repository.
Proposals themselves will need two new slack channels: `#rfc-suggestions` for informal early discussion,
and `#new-rfcs` for notification about issues submitted in the nf-core/proposals repository.

In the case of this RFC, the rest of the detailed design is in the documentation.
In order to not duplicate efforts, please read and comment directly in https://github.com/nf-core/website/pull/3367

# Drawbacks

- More process and bureaucracy can create additional work
- Additional formality may put people off from suggesting ideas

# Alternatives

- Continue as we are informally, though this approach is already showing signs of not scaling well

# Adoption strategy

- Initial "meta-RFC" for the RFC process itself
- Several upcoming projects have already been flagged as being suitable for an RFC
- Core team nurture these initial RFCs and monitor process, adapt protocol as necessary
- Blog post + message on `#announcements` when the website documentation is complete.

# Unresolved Questions

- Whether the multi-step process (especially issue + PR) is suitable.
- Whether people understand the differences between steps and what is expected.

# References

- Slack discussion (core-team channel)
- Reference Issues: https://github.com/nf-core/proposals/issues/30
