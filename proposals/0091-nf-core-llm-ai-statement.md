- Start Date: 2025-10-15
- Reference Issues: https://github.com/nf-core/proposals/issues/91
- Implementation PR: [https://github.com/nf-core/website/pull/3367](https://github.com/nf-core/website/pull/3705)

# Summary

nf-core should have a clear policy on when it is OK/not OK, and how to use LLMS for generating new code and PRs.

# Champion

[@jfy133](https://github.com/jfy133)

# Background & Motivation

Derived from the proposal here: https://github.com/nf-core/proposals/issues/61, some members of the core team and community were not comfortable to immediately start 'blindly' allowing LLM associated code within the nf-core ecosystem, primarily due to:

- Quality of code in some PRs
- Concerns about the legality/lack of attribution
- Adding a lot of extra cruft to the template purely to try and make sure AI agents 'do the right thing' being a bad thing

with particularly the first point ending up putting more work on community coordinators/managers.

Generally there was an agreement that LLMs are here to stay, and we cannot avoid them. 

But there was a feeling we need to at least make a statement on our stance on them and possibly a policy document.

# Goals

- Make clear when LLM code or related things are (generally) acceptable  within nf-core
- Make clear what the consequences of abusing these guidelines are

# Non-Goals

- To enforce AI usage on the community
- To ban AI usage 
- To implement mechanisms for the use of AI

# Detailed Design

The discusson on the initial RFC issue pointed towards a general statement as a blog post, that can be called out in various documents - where required.

A blog post acts as a position piece, but also allows a bit of flexibility as a non-static thing (can change over time), as new blog posts can be made with justification about changing stances (if required).

# Drawbacks

None noted.

# Alternatives

None noted.

# Adoption strategy

- [x] Made a blog post statement: https://github.com/nf-core/website/pull/3705
- [ ] Link to contribution documentation (e.g.: https://nf-co.re/docs/contributing/how_to_contribute_to_nf-core, and `CONTRIBUTING.md` on github repo)

# Unresolved Questions

- Any other places we should link to in the documentation?

# References

- https://github.com/nf-core/proposals/issues/61
- https://github.com/nf-core/website/pull/3705
