- Start Date: 2026-06-01
- Reference Issues: https://github.com/nf-core/proposals/issues/141
- Implementation PRs:
    - None yet

# Summary

AI agents are an increasingly used tool in software development, and Nextflow pipelines are no exception. As it stands, nf-core has some guidance on AI use, but no specific steering files for AI agents. This RFC proposes introducing a minimal `AGENTS.md` file to the template, as well as a larger remote steering file, to ensure agents have a basic understanding of nf-core best practices when working in template-based repositories.

# Champion

[@itrujnara](https://github.com/itrujnara)

# Background & Motivation

AI agents are systems that combine a Large Language Model with multiple deterministic tools to partially or fully automate software development. Apart from the user's prompts, they rely on several types of fixed input (*steering files*), including project instructions and skills. While there are differences in how agents from different vendors discover these files, `AGENTS.md` (https://agents.md/) has become a de facto standard. All popular agents are now set up to read this file before working in a directory.

nf-core currently has no specific `AGENTS.md` or other agent steering files. This requires extra work from developers to ensure that the agent output complies with nf-core standards, and creates room for divergence in practices. To promote uniformity and reduce the issue of non-compliant AI contributions, it would be prudent to introduce some basic guidance into the template, so that it affects every project automatically after the next update.

Concerns have been rightly raised about keeping the main steering file up to date, given the limited template release schedule and the dynamic nature of the AI sector. To address that, we propose to introduce a minimal `AGENTS.md`, consisting mostly of references to other, more updateable files.

Some community members have argued that `CONTRIBUTING.md` is a sufficient file to guide agents as well as human programmers. While this file is valuable, it is not automatically introduced into agent context, and thus should be explicitly included by reference. Furthermore, it is optimized for humans, so agent guidance should extend beyond this file.

There was previously an RFC on this topic, but it has gone stale months ago.

# Goals

- Add a minimal `AGENTS.md` to the template, with references to `CONTRIBUTING.md` and other steering files.
- Add a general `AGENTS_nfcore.md` to a public repository (website or otherwise), referenced by `AGENTS.md`.
- Add a pipeline-specific ~~`AGENTS_[pipeline].md`~~ **section** to the template, ~~initially near-empty, intended for pipeline-specific coding standards and referenced by~~ **within** the main `AGENTS.md`. \[Alteration by IT, introduced following discussion in the original proposal issue\]

# Non-Goals

- Overload the template with extensive agent steering (e.g. skills); this should be handled with an extension.
- Create lag and/or undue maintenance burden; all steering files should be updateable with a simple PR.

# Detailed Design

## `nf-core/agent-steering`

To create a dedicated, findable space for agent-related documents in nf-core, a new repository called `nf-core/agent-steering` \[name open to discussion - IT\] is created. Within this RFC, a single file called `AGENTS.md` (see *infra*) will be created in the repository, alongside a standard README and LICENSE. No other file should be created, unless called for by a future RFC.

## Template `AGENTS.md`

A new file called `AGENTS.md` is added to the nf-core pipeline template. This file contains 2 sections: the preamble and the pipeline section.

### Preamble

The preamble contains:
- a one-sentence reference to nf-core ("This repository was created with the nf-core pipeline template" or OWTTE),
- the instruction to consult `CONTRIBUTING.md`,
- the instruction to consult the remote steering file (*infra*).

The preamble does not contain any other information or instructions.

### Pipeline-specific section

The pipeline-specific section contains any standards and practices specific to a given pipeline. Developing it and keeping it up to date is the resposibility of the maintainers of the pipeline. This section should not recapitulate any general nf-core standards.

`nf-core/modules` may utilize this section to explain the specifics of the repository.

## Remote `AGENTS.md`

A new file called `AGENTS.md` is created inside `nf-core/agent-steering` (*supra*). This file contains ample guidance for AI agents about the template and nf-core coding practices. The file will be updated as agents evolve, with updates via PR as required.

This RFC does not specify a rigid structure or contents, but the following elements will tentatively be included (in some order):
- a treemap of the template with explanations of directories and files,
- a description of nf-core tools, list of commands, and examples for the most common operations in pipeline development,
- a description of nf-test and basic testing concepts,
- commit and PR discipline (scopes, message format),
- pre-commit routine (linting, tests, prek),
- self-disclosure rules for fully autonomous agents,
- references to nf-core documentation as required.

## Pipeline creation workflow

A new "Include AGENTS.md"/`include_agents_md` flag is added to the pipeline creation workflow. It is on by default, and is switchable in nf-core mode. `AGENTS.md` is only added to the pipeline directory if this flag is set.

## Pipeline linting tests

A new linting test is added to `nf-core pipelines lint`. This test verifies that the preamble of `AGENTS.md` exactly matches that in the template. 

## Documentation

- A paragraph about the `AGENTS.md` option is added to the documentation for `nf-core pipelines create`.
- A blog post about the changes will be published after the drafting and testing stages are concluded.
- Template `AGENTS.md` contains one-line comments for each section

# Drawbacks

- **More files in the template.** The pipeline template is heavy as it is. This RFC requires the addition of one extra top-level file, which may cause additional confusion, especially for newer contributors.

# Alternatives

- **Status quo: no centralized agent guidance.** This is the easiest solution to implement, but it is and will keep causing divergent development practices. It also increases the influx of low-quality PRs from developers who forget to include any nf-core guidance, often due to the lack of domain knowledge.
- **Delegate all agent guidance to an extension.** While this would prevent any template pollution, it has the significant drawback of requiring an additional manual step from the developer. Thus, it is not a complete solution to the problem of poorly curated AI contributions. A more comprehensive nf-core extension might be created in the future, but is out of scope of this RFC. 

# Adoption Strategy

## Drafting stage

- [ ] Creating `nf-core/agent-steering` (core team)
- [ ] Pipeline `AGENTS.md` first draft (anyone)
- [ ] Central `AGENTS.md` first draft (anyone)

## Testing stage

- [ ] Manual addition of `AGENTS.md` to:
    - [ ] `nf-core/modules` (maintainers)
    - [ ] at least 5 pipelines (volunteer pipeline maintainers)
- [ ] Testing by volunteers for at least 1 month (volunteer developers)

## Implementation stage

- [ ] Pipeline `AGENTS.md` second draft (anyone)
- [ ] Central `AGENTS.md` second draft (anyone) 
- [ ] Addition of `AGENTS.md` to the template (infrastructure team)
- [ ] Addition of relevant options to pipeline creation (infrastructure team)
- [ ] Addition of `AGENTS.md` lint test (infrastructure team)
- [ ] Addition of `AGENTS.md` documentation to the website (anyone)
- [ ] Blog post (anyone)
- [ ] Bytesize explaining the setup (Igor/Phil/Evangelos)

## Release stage

- [ ] tools release with the updated template (infrastructure team)
- [ ] Central `AGENTS.md` ready for swift updates (core team)

## Tentative timeline

Start of drafting: immediately
End of drafting and start of testing: by June 30, 2026
End of testing and start of implementation: by July 31, 2026
Tools release with new features: September-October 2026

# Unresolved Questions

- **Exact content of the central `AGENTS.md`.** This will develop progressively during drafting and testing.

# References
- Previous RFC: https://github.com/nf-core/proposals/issues/61
- Slack discussion 1 (#rfc-suggestions): https://nfcore.slack.com/archives/C08TXM0GGMT/p1779271876671859
- Slack discussion 2 (#team-maintainers): https://nfcore.slack.com/archives/C043UU89KKQ/p1779271926707799
- General information on AGENTS.md: https://agents.md/
- Module developer Claude extension: https://github.com/vagkaratzas/nf-core-module-dev
