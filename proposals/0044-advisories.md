- Start Date: 2025-06-10
- Reference Issues: https://github.com/nf-core/proposals/issues/44
- Implementation PR: https://github.com/nf-core/website/pull/3366

# Summary

This proposal introduces a new "Advisories" content type for the nf-core website to provide structured, searchable documentation of major technical issues in pipelines, modules, subworkflows, or configurations. Unlike transient Slack discussions or informal blog posts, advisories will include metadata-rich YAML front matter and standardized UI components for consistent presentation and better findability. The aim is to enhance transparency, support regulatory needs, and reduce redundancy in troubleshooting known issues.

# Champion

[@MatthiasZepper](https://github.com/MatthiasZepper)

# Background & Motivation

Older versions of nf-core pipelines are widely used, yet once a pipeline version is released, it remains unchanged—even if critical bugs are later discovered. While such issues are sometimes discussed informally in Slack/GitHub or can be derived from a pipeline's changelog, there is currently no structured, persistent way to document and communicate them. This lack of visibility leads to repeated investigations and confusion among users. The proposed "Advisories" content type addresses this gap by offering a standardized, searchable format for recording major issues, improving both transparency and long-term maintainability.

# Goals

- Provide a standardized, persistent format for reporting and referencing major technical issues in nf-core components.
- Enable users and maintainers to quickly search, access, and link information pertaining to technical issues, including how they can potentially be avoided or solved.
- Support compliance and auditing processes for regulated environments through improved issue tracking.

# Non-Goals

- Replace blog posts or other communication channels, e.g. on Slack or [Seqera Community](https://community.seqera.io/) to communicate issues. Rather, it should supplement them.
- Supersede GitHub issues for bug reporting or monitoring.
- Suggest backporting bug fixes to older releases.
- Public blaming/shaming for faulty code that was released.

# Detailed Design

Advisories will be implemented as a separate content type (structured content collection) in Astro, with robust schema validation using Zod. Each advisory will be stored as a Markdown file with YAML frontmatter containing essential metadata: title, subtitle, category (pipelines, modules, subworkflows, configuration), type (known_regression, incompatibility, security, performance, data_corruption, scientific_advice, other), severity (low, medium, high, critical), publishedDate, reporter, and reviewer information.

The website will display advisories through several new components and routes: AdvisoryHeader for metadata and categorization, AdvisoryCard for grid-based listing, and AdvisoryLayout for the overall page structure (note: AdvisoryLayout implementation is pending discussion). The UI will feature visual indicators using badges and icons, with distinct color schemes and icons for each advisory type and severity level. The system will support dynamic routing with type-specific pages and include a sidebar navigation for easy access to different advisory categories.

The implementation will include basic filtering and search capabilities. Advisories published within the last three months will be automatically categorized as "current" and prominently displayed on the website.

# Drawbacks

- The YAML frontmatter structure is complex to accommodate diverse use cases and affected components, requiring authors to learn the available fields and which values are acceptable.
- The criteria for when to create an advisory versus resolving an issue through Slack or the Seqera community needs to be clearly defined.

# Alternatives

- Maintain the current approach of communicating issues through Slack and blog posts, without implementing a formal advisory system.

# Adoption Strategy

Initially, we will allow any nf-core maintainer and potentially users to submit advisories through pull requests to the website. The pull request reviewers should add themselves as advisory reviewers in the frontmatter. This process can be formalized later?

# Unresolved Questions

- [] Technical implementation details need to be resolved, including:
  - [x] Integration with existing Astro layouts without creating a separate layout for this content type (Request by @mashehu)
  - [] Implementation of search functionality with version range support (Request by @SPPearce)
  - [x] Integration into the pipeline pages for each affected revision (Subject to a separate pull request because of technical complexity?)
  - [] Integration into the module/subworkflow pages (Subject to discussion, whether desirable at all.)

# References

- [Slack discussion](https://nfcore.slack.com/archives/CE7DN1U7M/p1748117028217599)
- Original [GitHub issue/pull request](https://github.com/nf-core/website/pull/3366)
- [Prototype](https://deploy-preview-3366--nf-core-main-site.netlify.app/advisories)
