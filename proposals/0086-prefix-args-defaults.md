- Start Date: 2025-09-24
- Reference Issues: https://github.com/nf-core/proposals/issues/86
<!-- - Implementation PR: TODO add PR -->

# Summary

nf-core modules currently define defaults for `ext.prefix` and `ext.args` inside both the `script` and `stub` blocks, leading to code duplication. This RFC proposes moving those defaults to the process `ext` directive, which is a native Nextflow feature. This eliminates redundant definitions and reduces the risk of mismatches between the `script` and `stub` blocks. Output block references and in-script variable usages are updated to use `task.ext.prefix` and `task.ext.args` directly. nf-core linting will be updated to enforce this new convention across all modules.

# Champion

[@nvnieuwk](https://github.com/nvnieuwk)

# Background & Motivation

All nf-core modules have support for at least two custom process variables via the [`ext`](https://docs.seqera.io/nextflow/reference/process#ext) directive:

- `ext.prefix`: This is used to set the prefix of any output file in the process. It's usually set to the `meta.id` as default.
- `ext.args`, `ext.args2`...: These are used to set specific arguments for the tools used in the process. The first tool uses `ext.args` for its arguments, the second tool uses `ext.args2` and so on.

Currently the defaults of these ext variables are set in the `script` and `stub` block of the process like this:

```groovy
def prefix = task.ext.prefix ?: "${meta.id}"
def args = task.ext.args ?: ''
```

This system was fine when the processes only consisted of the `script` block. When the `stub` block has been added, the definition of these variables was duplicated into that block. No issues have arisen yet, but the duplication introduces a risk of inconsistency between blocks.

However, Nextflow does support setting default directly as a process directive (at the top of the process declaration), like so:

```groovy
ext prefix: "${meta.id}", args: ''
```

> [!NOTE]
> nf-core modules also use a third ext variable, namely `ext.when`. During testing we noticed some weird behaviour for ext variables where the default is set using the above method. For that reason we decided to not set the `ext.when` default with this method. Support for the `when` block will be removed when migrating pipelines to strict syntax so this behaviour will not be used for much longer. This can thus be ignored for now.

# Goals

- Reduce code duplication in processes by only stating the ext variables defaults once
- Use a more Nextflow-native approach of the `ext` directive
- Update nf-core linting to this new system

# Non-Goals

- Break the current way we use modules. This system should be completely backwards compatible for all DSL2 pipelines.
- Update `ext.when` since this does not work with the suggested implementation

# Detailed Design

A proof-of-concept [PR](https://github.com/nf-core/modules/pull/8808) has been created in the modules repository. This detailed design will be based on the work done there.

The following diff shows the important parts that need to change for this RFC, followed by a step-by-step explanation:

```diff groovy
process SAMTOOLS_SORT {
    tag "${meta.id}"
    label 'process_medium'
+   ext prefix: "${meta.id}", args: ''

    input:
    ...

    output:
-   tuple val(meta), path("${prefix}.bam"), emit: bam, optional: true
+   tuple val(meta), path("${task.ext.prefix}.bam"), emit: bam, optional: true
-   tuple val(meta), path("${prefix}.cram"), emit: cram, optional: true
+   tuple val(meta), path("${task.ext.prefix}.cram"), emit: cram, optional: true
-   tuple val(meta), path("${prefix}.sam"), emit: sam, optional: true
+   tuple val(meta), path("${task.ext.prefix}.sam"), emit: sam, optional: true
    ...

    when:
    task.ext.when == null || task.ext.when

    script:
-   def args = task.ext.args ?: ''
-   prefix = task.ext.prefix ?: "${meta.id}"
    ...
    """
    samtools sort \\
-       ${args} \\
+       ${task.ext.args} \\
-       -T ${prefix} \\
+       -T ${task.ext.prefix} \\
        ...
    """

    stub:
-   def args = task.ext.args ?: ''
-   prefix = task.ext.prefix ?: "${meta.id}"
    ...
    """
-   touch ${prefix}.${extension}
+   touch ${task.ext.prefix}.${extension}
    """
}
```

1. Add `ext prefix: "${meta.id}", args: ''` as a directive to the process declaration.
2. Update any mentions of `prefix` in the `output` block to `task.ext.prefix`.
3. Remove the definitions of `prefix` and `args` from the `script` and `stub` block. If prefix or args appear multiple times, assign them to local variables for readability.
4. Update all mentions of `prefix` and `args` to `task.ext.prefix` and `task.ext.args` respectively in the `script` and `stub` blocks.

Whether this is feasible as a bulk PR remains to be investigated.

The linting in nf-core/tools should also be updated. Ideally it would just check if `ext prefix: "${meta.id}", args: ''` is defined and check if there are no lines containing the following strings: `prefix = task.ext.prefix ?:` and `args = task.ext.args ?:`.

# Drawbacks

There are no known drawbacks to this migration as of the writing of this RFC.

# Alternatives

Except for sticking to the current system, there is no better alternative to remove code duplication.

# Adoption strategy

1. A gradual migration of some modules to make sure this does not break anything.
2. Implement linting support
3. Migrate all other modules (ideally in a bulk update)

# Unresolved Questions

No unresolved questions have been identified at this time.
