---
name: nfcore-proposal-review
description: >-
  Review an nf-core new pipeline proposal and produce a scored assessment.
  Use whenever given a link, issue number, or
  description from the nf-core/proposals repository, or when asked whether a
  proposed bioinformatics pipeline should be accepted into nf-core. Triggers on
  "review this proposal", "should we accept this", "nf-core/proposals#NNN", any
  github.com/nf-core/proposals link, "is this a good nf-core pipeline?", or any
  mention of evaluating a pipeline proposal against nf-core criteria. Always
  invoke this skill rather than doing an ad-hoc review — it handles the
  research, overlap checking, and structured output.
---

# nf-core New Pipeline Proposal Review

Proposals live at https://github.com/nf-core/proposals/issues (label:
`new-pipeline`). The goal is a structured, scored assessment that helps the
maintainer team reach a decision, posted as a comment on the proposal. The bot
scores and advises; the accept/reject decision is always the maintainers', never
the bot's. This is not a scientific peer review — even "I'm not familiar with the
area, but looks alright" is a useful contribution.

The triggering proposal is already provided: its body and every comment are
included in the user message. Start with the overlap research (Step 1) — do not
try to re-fetch the issue.

## Tooling

In the GitHub Action you can read files in this repository with the Read tool
(for `references/examples.md`), and run only these read-only commands through
Bash:

- The bundled scripts in `scripts/` alongside this file. Run each one with its
  full path, as `python3 <skill-dir>/scripts/<name>.py …` (or
  `bash <skill-dir>/scripts/fetch_proposal.sh …`), from the current
  directory. Don't `cd` first and don't pipe their output into other commands:
  both get the command blocked.
  - `check_tools.py <tool1> [tool2 ...]`: nf-core module presence, and which
    pipelines install each tool.
  - `tool_info.py <tool1> [tool2 ...]`: bio.tools and Bioconda / conda-forge
    entries: description, licence, publications.
  - `list_pipelines.py <term1> [term2 ...]`: nf-core pipelines matching any of
    the terms in their name, description or topics, with their status, description and
    topics.
  - `maintainers.py <pipeline>`: code owners, top contributors and recent
    committers.
  - `similar_proposals.py <term1> [term2 ...]`: earlier proposals matching any
    of the terms, with their outcome labels.
  - `fetch_proposal.sh [NUMBER]`: another proposal in full. The one you are
    reviewing is already in the user message.
- `gh issue view|list`, `gh search …`, `gh repo view|list` and `gh pr view|list`.
  Use `--jq` to filter JSON output; there is no standalone `jq`.

Everything else, including writes, `gh api` and other binaries, is blocked.

## Step 1: Tool inventory, then pipeline overlap

Pull the proposed tool list, purpose, data type, organism scope, and proposer
handle from the provided proposal. Then do **all** of the following before you
score. Each one is cheap, and a review that skips one is guessing:

1. `check_tools.py` and `tool_info.py` on the proposed tools.
2. `list_pipelines.py` with several terms, then `gh repo view nf-core/<name>` per candidate.
3. `similar_proposals.py` with a few search terms.
4. `maintainers.py` for the main overlapping pipeline, if there is one.
5. Read `references/examples.md`.

The sections below explain how to use each result.

### Tool inventory

```bash
python3 <skill-dir>/scripts/check_tools.py <tool1> [tool2 ...]
python3 <skill-dir>/scripts/tool_info.py <tool1> [tool2 ...]
```

`check_tools.py` shows whether each tool is an nf-core module and which
pipelines install it. If several proposed tools are already used together in an
existing pipeline, that's a strong overlap signal. An `ERROR` line means the
result is unknown, not that the tool is missing: say so rather than treating it
as novel.

`tool_info.py` gives each tool's licence and packaging, which is evidence for
testability (restrictive licences, tools not on Bioconda) and for novelty
(whether there is a published method).

Map the overlap pattern to a scoring hint:

| Tool overlap pattern                                              | What it suggests                                                  |
| ----------------------------------------------------------------- | ----------------------------------------------------------------- |
| All tools in nf-core modules, already used together in a pipeline | Extend that pipeline; don't create a new one                      |
| Tools in nf-core but not combined this way                        | Possibly a subworkflow worth adding to an existing pipeline       |
| Tools not yet in nf-core + genuinely novel combination            | New pipeline more justified                                       |
| Standard tools + one novel algorithm                              | New pipeline only if the novel algorithm is the load-bearing part |

### Check existing pipelines directly

```bash
python3 <skill-dir>/scripts/list_pipelines.py <term1> [term2 ...]
```

Look specifically for:

- Pipelines handling the same data type or analysis
- Pipelines using overlapping tool sets even if differently framed
- Archived pipelines that cover the space (may be revivable)

For each candidate overlap, read what the pipeline actually does with
`gh repo view nf-core/<name>`, which prints its README. A one-line description is
not enough to judge overlap.

When you find a strong overlap, look up that pipeline's maintainers' GitHub
usernames now — you'll need them for the `reviewers` field. See "Find and
name the overlapping pipeline's maintainers" in the pitfalls section.

### Check earlier proposals

```bash
python3 <skill-dir>/scripts/similar_proposals.py <term1> [term2 ...]
```

Search with a few terms: the data type, the analysis and the main tools. If an
earlier proposal covered similar ground, read it with
`gh issue view <n> --repo nf-core/proposals --comments` and see what was decided
and why. Put every overlapping proposal in `related_proposals`, whatever its
outcome, unless it already became a pipeline you listed in `overlap`. That
includes accepted proposals that don't have a pipeline repository yet, and open
proposals that duplicate this one.

Then read `references/examples.md` alongside this file and compare your
assessment with those past decisions, to keep your scores in line with how the
core team actually decides.

## Step 2: Apply the four criteria

Evaluate each and note your evidence — a short phrase is fine, you don't need
prose.

### A. Workflow specificity (primary gate)

The nf-core requirement at
https://nf-co.re/docs/specifications/pipelines/requirements/workflow_specificity:

- One pipeline per data + analysis type
- No organism-specific pipelines unless the tooling genuinely can't generalise
- Prefer extending an existing pipeline over creating a new one

This is the most common rejection reason. The key test: **is this a novel
tooling combination, or is it a different organism/tissue/sample type running
through tools that already exist in nf-core?**

"Field deployment" or "our community needs it" arguments don't make a workflow
distinct. "The biological problem is structurally different and requires
different algorithms" does.

### B. Testability

- Can this run in nf-core CI with open test data?
- Does it require proprietary tools, licensed software, or hardware-bound
  executors (DRAGEN is the canonical example)?
- "Stubs only" are only acceptable in exceptional circumstances — nf-core's Megatests and results comparison
  convention typically require real execution.

### C. Novelty — what's the genuine gap?

- What does this bring that nothing in nf-core currently covers?
- Is the novel part a whole pipeline's worth, or one or two
  modules/subworkflows?
- Is there a published method being implemented, or is it "standard tools run in
  order"?

The test: if you could achieve 90% of the value by adding a module or
subworkflow to an existing pipeline, that's probably the right path.

### D. Sustainability

- Solo author or a team?
- Does the proposer have existing nf-core experience (check their GitHub for
  merged modules/PRs)?
- Starting from bash scripts vs. existing Nextflow code?
- Niche, solo-authored pipelines are nf-core's main abandonment failure mode.
  This is a risk factor, not a hard reject, but it should prompt a "do you have
  collaborators?" question before approval.

## Step 3: Score the proposal

Give an **overall score out of 5**, plus a score out of 5 for each of the four
criteria. The score is advice for the maintainer team — it is not a decision, and
you never "accept" or "reject" anything yourself.

| Overall | Emoji | Meaning                                                                                |
| ------- | ----- | -------------------------------------------------------------------------------------- |
| 5/5     | 🟢    | Strong fit — clear novel gap, passes specificity, testable, sustainable                |
| 4/5     | 🟢    | Good fit — minor points to discuss, no blockers                                        |
| 3/5     | 🟡    | Borderline — real merit but notable scope or sustainability concerns; needs discussion |
| 2/5     | 🔴    | Weak fit — significant overlap or specificity problems; salvageable only by reframing  |
| 1/5     | 🔴    | Poor fit — fails specificity with no salvage path, or untestable in CI                 |

If a criterion can't be assessed without an answer from the proposer, score it
`—/5` and state the question rather than guessing.

## Step 4: Fill in the review

The review is posted as a comment on the proposal issue, so the proposer reads
it too. Its layout, emoji and disclaimer come from `scripts/render.py`: your job
is only the content, as a JSON object matching `review.schema.json` (alongside
this file). The schema's field descriptions say what goes where.

- In the GitHub Action, Claude Code runs with that schema as its output format,
  so just fill it in.
- Run interactively without a schema, write the same JSON object to a temporary
  file and show the user the output of
  `python3 <skill-dir>/scripts/render.py < that-file`.

Content rules:

- **Be brief.** Every field is a short phrase or one sentence, not a paragraph.
  Cut anything a maintainer doesn't need to decide.
- Scores follow the Step 3 table. Don't add emoji; the renderer picks them from
  the score.
- Always write pipeline names in full as `nf-core/<name>` and Slack channels as
  `#<name>`, not in backticks. The renderer links them.
- Only call something `nf-core/<name>` if `list_pipelines.py` lists it or it is
  an nf-core proposal. Name tools and pipelines from elsewhere with their real
  owner, e.g. `genomic-medicine-sweden/tomte`, never as nf-core ones.
- In `next_steps`, separate blockers (would need resolving before the proposal
  could be accepted) from points to discuss and optional suggestions. Keep the
  tone suggestive: the whole review is advice. If the scores point to a poor fit,
  add a suggestion with a concrete path forward where one exists (a subworkflow
  PR to an adjacent pipeline, a SIG consultation, etc.).
- **Never write `/approve` or `/reject` anywhere.** Those commands are the
  maintainers' decision, not the bot's.
- Tone: direct and constructive, not corporate.
- If you're not familiar with the domain, say so in `why`. Flagging an apparent
  overlap from a non-expert perspective is still valuable.

## Common patterns and pitfalls

**The subworkflow/module test** (most important redirect signal): If the unique
functionality fits within 1-2 new subworkflows added to an existing pipeline,
reviewers will redirect rather than accept. The overlap threshold is low — even
60-70% coverage by an existing pipeline is enough to trigger "merge with
existing." Ask explicitly: could this be a subworkflow PR to an adjacent
pipeline?

**Organism-specific arguments that don't work**: "our community needs this,"
"it's for field deployment," "the audience is different." These are not
workflow-distinctness arguments. The exception is when the biological problem
structurally requires different algorithms (e.g., Plasmodium multiclonal
infection deconvolution has no human analogue).

**SIG consultation as a positive signal**: Proposals that mention having
discussed scope with the relevant nf-core SIG (meta-omics, single-cell, spatial,
etc.) or related pipeline maintainers move much faster. A proposal with no
community consultation mentioned should be flagged — it likely needs a
round-trip to the SIG before a decision can be reached. Suggest it in the
comment.

**Late-stage engagement penalty**: If the proposer has already built a
near-complete pipeline before proposing, the core team treats this as social
friction — the team has sunk costs that make merging harder. This is an explicit
anti-pattern. The right framing is early community co-design, not "here's what
we built, please accept it." Flag it and note the core team has been blunt about
this: "nf-core isn't a pipeline publishing warehouse."

**Crowded domains**: In domains with multiple existing pipelines (spatial
transcriptomics, single-cell, metagenomics), the question is not "does this
cover different tools" but "does the underlying data format or biological
question require a fundamentally different processing approach?" A new assay
type with different segmentation requirements (spatial) justifies a new
pipeline; a different organism processed with the same tools does not.

**The mega-pipeline shape nf-core resists**: "Run pipeline A, then run pipeline
B, then add one novel module." The question becomes: can the novel module stand
alone in an existing pipeline? nf-core prefers smaller pipelines chained
together over one that re-implements several to save users a step. The
integration step can be its own downstream pipeline that takes their outputs.

**Regulatory/compliance pipelines**: Legitimate but unusual — value is the
execution context (GxP audit trails, Seqera Platform provenance) rather than
novel computational steps. These face higher scrutiny and need more approvers.
Advise proposers to spell out the compliance rationale explicitly; reviewers
will otherwise ask whether a plugin would suffice.

**Name collisions**: A proposed name clashing with a well-known tool (e.g.
"midas" = famous metagenomics database) is a point to discuss, not a blocker.

**The overlapping pipeline's maintainers often decide**: The core team usually
asks the maintainers of the overlapping pipeline and follows their view. If they
want to take the feature on, it becomes a merge. An existing pipeline with little
recent development is a reason to merge into it and revive it, not to start a new
one. So name the pipeline to merge into and the people to ask.

**Publication plans don't justify a separate pipeline**: Proposers often want
their own pipeline so they can publish it. The core team has not accepted this
as a reason. A significant new release of an existing pipeline can be published
instead.

**Going quiet**: Note if the proposer hasn't responded to the most recent
feedback round. This affects the realistic approval timeline and can justify a
softer close.

**Find and name the overlapping pipeline's maintainers**: When the proposal
overlaps an existing pipeline, don't just say "ping the leads" — actually look up
their GitHub usernames and put them in `reviewers` so they are @-mentioned.

**Tag at most three people, and only the ones who genuinely drive the pipeline.**
Every nf-core pipeline has a small core of heavy contributors plus a long tail of
people with one or two commits — the long tail must NOT be tagged.

```bash
python3 <skill-dir>/scripts/maintainers.py <pipeline>
```

Start from the code owners, which are exactly this short list. If there are
none, take the clear leaders among the top contributors, and drop anyone whose
count is a small fraction of the top contributor's. For an older pipeline whose
original authors have moved on, prefer whoever is active in the recent commits.

Put the resulting **one to three** people in `reviewers`. Tagging them is far
more effective than waiting for them to find the proposal thread. If you
genuinely can't resolve a handle, leave them out and name the pipeline in
`overlap` rather than inventing or over-tagging.
