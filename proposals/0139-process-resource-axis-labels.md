- Start Date: 2026-05-06
- Reference Issues: https://github.com/nf-core/proposals/issues/139
- Implementation PRs:
  - Template change: https://github.com/nf-core/tools/pull/4265
  - Documentation: https://github.com/nf-core/website/pull/4212

# Summary

The nf-core pipeline template ships a small set of bundled resource labels (`process_low`, `process_medium`, `process_high`, `process_high_memory`, `process_long`) that conflate CPU, memory and time. This makes common shapes like "many CPUs, little memory" awkward to express and leads to systematically over-provisioned defaults.

This RFC replaces the bundled labels with three orthogonal axes (`process_cpus_*`, `process_mem_*`, `process_time_*`) that are mixed and matched per process, with a documented deprecation path for the existing labels.

# Champion

[@pinin4fjords](https://github.com/pinin4fjords)

# Background & Motivation

The current label set was designed to be simple and to "just work" out of the box, with users expected to override values in their own configs. In practice:

- There is no way to express "many CPUs but little memory". Authors either pick `process_high` (which over-allocates memory by a large factor) or stack `process_high_memory` on top of `process_medium`, which is undocumented and counter-intuitive.
- Bundled labels tie CPU, memory and time together even though most tools scale on only one axis. Over-provisioning by hundreds of times is not unusual.
- Pipelines have already invented ad-hoc additions (`process_high_cpu` in nf-core/genomeassembler, `process_high_memory` in nf-core/scnanoseq). Without a community-wide convention this creep will continue and diverge across pipelines.
- Stacking labels does work (later labels win, definition order matters) but is not obvious or documented as the recommended pattern.

A short-term workaround was merged in [nf-core/tools#4264](https://github.com/nf-core/tools/pull/4264) (a single new `process_low_memory` label) so the rnaseq pipeline could ship Trim Galore v2.0 immediately. This RFC covers the larger structural change agreed in the Slack discussion and prototyped in [nf-core/tools#4265](https://github.com/nf-core/tools/pull/4265).

# Goals

- Define an orthogonal label scheme covering CPU, memory and time so any reasonable resource shape can be expressed by combining labels.
- Provide sensible defaults in the template `base.config` so processes adopting the new labels get appropriate resources without further tuning.
- Migrate nf-core/tools (template), nf-core/modules and nf-core/configs together, with a documented deprecation path for the existing bundled labels.

# Non-Goals

- Replacing per-process resource tuning. Labels are starting points, not final allocations.
- Auto-migrating user site configs that already pin `withLabel: process_high` etc. A documented migration is in scope; automated rewriting of third-party configs is not.
- Solving dynamic resource scaling. The existing `task.attempt` pattern continues to work and is orthogonal to this proposal.

# Detailed Design

## Label scheme

Three orthogonal axes. A process picks at most one label per axis:

| Axis   | Labels (low to high)                                                                            |
| ------ | ----------------------------------------------------------------------------------------------- |
| CPU    | `process_cpus_single`, `process_cpus_low`, `process_cpus_medium`, `process_cpus_high`           |
| Memory | `process_mem_low`, `process_mem_medium`, `process_mem_high`                                     |
| Time   | `process_time_short`, `process_time_medium`, `process_time_long`                                |

A process with no labels still gets the per-process defaults defined at the top of `base.config` (currently `1 cpu`, `6 GB`, `4 h`). The labels override one axis each.

## Template defaults (`base.config`)

Defaults proposed in [nf-core/tools#4265](https://github.com/nf-core/tools/pull/4265):

```groovy
withLabel:process_cpus_single  { cpus   = { 1                    } }
withLabel:process_cpus_low     { cpus   = { 2     * task.attempt } }
withLabel:process_cpus_medium  { cpus   = { 6     * task.attempt } }
withLabel:process_cpus_high    { cpus   = { 12    * task.attempt } }

withLabel:process_mem_low      { memory = { 1.GB  * task.attempt } }
withLabel:process_mem_medium   { memory = { 12.GB * task.attempt } }
withLabel:process_mem_high     { memory = { 72.GB * task.attempt } }

withLabel:process_time_short   { time   = { 1.h   * task.attempt } }
withLabel:process_time_medium  { time   = { 8.h   * task.attempt } }
withLabel:process_time_long    { time   = { 20.h  * task.attempt } }
```

The exact tier values are open to refinement, but the shape (4 CPU tiers, 3 memory tiers, 3 time tiers) is the contract this RFC asks the community to agree on.

## Semantics

- Labels are independent. `process_cpus_high` + `process_mem_low` + `process_time_short` is a valid combination, expresses a CPU-bound but memory-light short job, and yields the resources expected from each axis.
- A process with no resource labels still receives the per-process baseline (top-of-`base.config` defaults).
- A process with only one or two axis labels receives the baseline on the un-labelled axes. This is the recommended pattern when one axis truly does not need tuning.
- Mixing legacy and new labels on the same process is supported during the deprecation window but discouraged. The label evaluation order in `base.config` means later definitions win, so authors should not rely on overlap.

## Linting

- nf-core/modules and pipeline-local module linting will accept labels matching the new axis pattern and the existing bundled labels.
- A new lint warning (not error) fires when a module uses a deprecated bundled label, pointing to the migration guide.
- A separate lint check verifies that a process declares **at most one** label per axis. Two CPU labels on the same process is a hard error.
- Local (in-pipeline) modules are linted with the same rules as nf-core/modules. Pipelines may opt out per-process via the standard lint ignore mechanism; there is no blanket exemption for local modules.

## `nf-core modules create` dialogue

The current single "resource label" prompt is replaced with three prompts:

1. CPU axis: `single` / `low` / `medium` / `high` (default `single`)
2. Memory axis: `low` / `medium` / `high` (default `low`)
3. Time axis: `short` / `medium` / `long` (default `short`)

Each prompt accepts an empty answer to leave that axis unlabelled. The generated module `main.nf` emits `label 'process_cpus_x'` etc. for the chosen tiers.

## Migration

Phased rollout coordinated across three repos:

1. **nf-core/tools template** (this PR): adds the new axis labels alongside the existing bundled ones. Existing labels continue to work, no pipeline breakage.
2. **nf-core/modules**: a bulk PR (or a series of grouped PRs) replaces each module's bundled label with the equivalent axis combination. The mapping table below is the default; per-module judgment calls override it.
3. **nf-core/configs**: institutional configs that override `withLabel: process_*` get matching `withLabel: process_cpus_*` etc. overrides via a bulk PR per config. The script that produces these is part of the implementation deliverable.
4. **nf-core pipelines**: pipeline maintainers migrate their local modules at their own pace, but pipeline-template syncs land the new labels in `base.config` so new pipelines start on the new scheme by default.
5. **Deprecation window**: bundled labels remain functional but emit a lint warning for two minor template releases. After that they are removed from `base.config` and become an unrecognised-label lint error.

### Default mapping (legacy -> axis)

| Legacy label          | CPU                  | Memory              | Time                  |
| --------------------- | -------------------- | ------------------- | --------------------- |
| `process_single`      | `process_cpus_single`| (baseline)          | (baseline)            |
| `process_low`         | `process_cpus_low`   | `process_mem_medium`| (baseline)            |
| `process_medium`      | `process_cpus_medium`| `process_mem_medium`| `process_time_medium` |
| `process_high`        | `process_cpus_high`  | `process_mem_high`  | `process_time_long`   |
| `process_long`        | (unchanged)          | (unchanged)         | `process_time_long`   |
| `process_high_memory` | (unchanged)          | `process_mem_high`  | (unchanged)           |
| `process_low_memory`  | (unchanged)          | `process_mem_low`   | (unchanged)           |

Mapping `process_low` is the most opinionated call: the legacy value bundles 12 GB of memory which is closer to `process_mem_medium` than `process_mem_low`. Module maintainers should review the mapping during migration rather than mechanically applying it.

## Documentation

Drafted in [nf-core/website#4212](https://github.com/nf-core/website/pull/4212):

- [Component resource requirements spec](https://nf-co.re/docs/specifications/components/modules/resource-requirements) updated with the axis labels as the preferred pattern, bundled labels demoted to legacy with a migration link.
- New [Migrating to axis-decomposed resource labels](https://nf-co.re/docs/contributing/migrating-resource-labels) guide with the mapping table above, a `sed` recipe for site-config maintainers, and a deprecation timeline.
- User-facing [system configuration page](https://nf-co.re/docs/running/configuration/nextflow-for-your-system) example updated to use axis labels alongside an explainer of the legacy scheme.
- Pipeline template `base.config` comment block points new authors at the docs.

# Drawbacks

- **More labels to remember.** Three prompts instead of one when creating a module, and a longer list of labels in `base.config`. Mitigated by the `nf-core modules create` dialogue defaulting to sensible baseline tiers.
- **Mixed-state ecosystem during deprecation.** Pipelines, modules and site configs will sit on different label vocabularies for a while. Mitigated by keeping the bundled labels functional throughout the deprecation window and by lint warnings (not errors).
- **Bulk migration PRs are noisy.** Touching most modules and most configs in one go is a large review surface. Mitigated by grouping PRs by module category and by using a deterministic `sed` script so reviewers can spot-check rather than read every diff.

# Alternatives

- **Keep the status quo and add labels ad hoc** (`process_high_memory`, `process_low_memory`, `process_high_cpu` etc.). Rejected as the direction the community has already drifted, with the consequence that pipelines invent diverging vocabularies.
- **Allow free-form resource declarations in `meta.yml`** instead of labels. Rejected as a much larger change to the modules contract and not necessary to solve the immediate problem.
- **A single new "shape" label** (e.g. `process_cpu_bound`, `process_memory_bound`). Rejected because it still bundles axes and just renames the problem; the orthogonal scheme generalises cleanly.

# Adoption strategy

- [x] Prototype template change: [nf-core/tools#4265](https://github.com/nf-core/tools/pull/4265)
- [x] Drafted docs update: [nf-core/website#4212](https://github.com/nf-core/website/pull/4212) (component resource spec + migration guide + system-config example)
- [ ] Update `nf-core modules create` dialogue to ask three axis questions
- [ ] Update nf-core/modules linting to recognise the new labels and warn on bundled ones
- [ ] Bulk migration PR(s) against nf-core/modules
- [ ] Bulk migration PR(s) against nf-core/configs
- [ ] Bytesize talk announcing the new scheme and migration window
- [ ] Two-release deprecation window for bundled labels, then removal

# Unresolved Questions

- **Exact default values per tier.** The numbers in `base.config` above are a starting point; the community may want different CPU/memory/time tier values based on real-world usage data.
- **Should the bulk migration be a single PR per repo or per module category?** Trade-off between review-surface size and merge-conflict risk during the migration window.
- **Site-config migration tooling.** Should `nf-core/tools` ship a `nf-core configs migrate` helper that rewrites `withLabel: process_*` overrides for institutional configs, or is a documented `sed` recipe enough?
- **Interaction with `process_gpu` and the `error_*` labels.** These remain separate (they are not resource-shape labels) and are unchanged by this RFC, but the docs should make that explicit.

# References

- Original proposal issue: https://github.com/nf-core/proposals/issues/139
- Slack discussion (#core, May 2026): https://nfcore.slack.com/archives/C05AHQPA9A7/p1777982753023139
- Existing bundled labels in the template: https://github.com/nf-core/tools/blob/dev/nf_core/pipeline-template/conf/base.config
- Short-term `process_low_memory` addition: https://github.com/nf-core/tools/pull/4264
- Prototype of orthogonal restructure: https://github.com/nf-core/tools/pull/4265
- Documentation update: https://github.com/nf-core/website/pull/4212
- Pipelines inventing their own labels: nf-core/scnanoseq nanocomp (`process_medium` + `process_high_memory`), nf-core/genomeassembler medaka (`process_high_cpu` + `process_high_memory` + `process_long`)
