- Start Date: 2025-09-01
- Reference Issues: https://github.com/nf-core/proposals/issues/46
- Implementation PR: https://github.com/nf-core/website/pull/XXX

# Summary

Topic channels are now (as of Nextflow 25.04) stable.
This would greatly simplify the way we can handle versions collection in the scripts.
We should migrate to use them in the nf-core/modules, TEMPLATE, etc.

# Champion

[@maxulysse](https://github.com/maxulysse)

# Background & Motivation

All started with this issue:

- https://github.com/nextflow-io/nextflow/issues/4222

Topic channels are an even simpler way to handle version collection that I initially envisioned.
We just need to output a `topic`, and no need to mix the versions channels anymore, we can just use a single topic versions channel that will automatically collect all the versions.

# Goals

- Provide a simpler way to handle versions collection at every level
  - modules
  - subworkflows
  - pipelines
  - tests

# Non-Goals

- Migrate everything

# Detailed Design

At the modules level:

```nextflow
    output:
    tuple val(meta), path('*.bam'), emit: bam
    path "versions.yml", emit: versions

    script:
    my_command.py ${input} -> file.bam

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
```

becomes:

```nextflow
    output:
    tuple val(meta), path('*.bam'), emit: bam
    tuple val("${task.process}"), val('python'), eval("python --version | sed 's/Python //g'"), topic: versions

    script:
    my_command.py ${input} -> file.bam
```

With current latest nf-test [0.9.2](https://github.com/askimed/nf-test/releases/tag/v0.9.2), there is no real support for topic channels (cf [this issue](https://github.com/askimed/nf-test/issues/258)).
That being said, when did that stopped anyone from finding a workaround?

nf-test does capture every output from the modules, but since there is no emit for the versions anymore, we have to rely on the index of the process.out to get the versions.

So

```groovy
  assert snapshot(process.out).match()
```

becomes:

````groovy
  assert snapshot(
      process.out.bam,
      ['versions', process.out[1]]
  ).match()```

````

Which in the snapshot translate to:

```text
"content": [
    {
        "0": [
            [
                {
                    "id": "file.bam"
                },
                "file.bam.exon.bed:md5,d41d8cd98f00b204e9800998ecf8427e"
            ]
        ],
        "1": [
            "versions.yml:md5,4e809973b78e4e60b7134a81a1eb592b"
        ],
        "bed": [
            [
                {
                    "id": "file.bam"
                },
                "file.bam.exon.bed:md5,d41d8cd98f00b204e9800998ecf8427e"
            ]
        ],
        "versions": [
            "versions.yml:md5,4e809973b78e4e60b7134a81a1eb592b"
        ]
    }
],
```

```text
"content": [
    [
        [
            {
                "id": "file.bam"
            },
            "file.bam.exon.bed:md5,d41d8cd98f00b204e9800998ecf8427e"
        ]
    ],
    [
        "versions",
        [
            [
                "THE_PROCESS_NAME",
                "python",
                "3.8.3"
            ]
        ]
    ]
],
```

So on one side, we loose the ability to simply use `process.out` to get the versions, but on the other side, we have cleaner snapshots.

For the subworkflows level, it is quite similar.

Every modules that has already migrated to use topic channels can have the versions collection deleted from the subworkflow script.

```nextflow
ch_versions = ch_versions.mix(THE_PROCESS_NAME.out.versions)
```

To still allow for capture of versions, we can add a `topic_versions` to the emit block.

```nextflow
    versions         = ch_versions
    topic_versions   = channel.topic('versions')
```

If all modules have been migrated to use topic channels, we can remove the `versions` channel from the subworkflow emit block.

On the subworkflow level test side, we would capture both of these outputs.
And when nf-test will support topic channels, we could simplify the tests and remove this temporary `topic_versions` channel.

And we capture either `versions` and `topic_versions`, or just the `topic_versions` in the test.

At the pipeline level, using the nf-core-utils pipeline, we can allow mixing of legacy `versions` channels and topic `versions` channels.

The underlying logic is in these two functions:

```nextflow
// Get channel of software versions used in pipeline in YAML format using nf-core-utils plugin
def softwareVersionsToYAML(ch_versions_legacy, ch_versions_topic, ch_versions_workflow) {
    def versions_legacy = ch_versions_legacy.unique().map { version -> processVersionsFromFile([version.toString()]) }
    def versions_topic = ch_versions_topic
        .unique()
        .groupTuple(by: 0)
        .map { topic -> topicVersionToYAML(topic[0], topic[1], topic[2]) }

    def versions_workflow = ch_versions_workflow

    return versions_legacy.mix(versions_topic, versions_workflow)
}

// Process versions from topic channel
def topicVersionToYAML(taskProcess, tools, versions) {
    def toolsVersions = [tools, versions]
        .transpose()
        .collect { k, v -> "${k}: ${v}" }
    return """
    |${taskProcess.tokenize(':').last()}:
    |  ${toolsVersions.join('\n|  ')}
    """.stripMargin().trim()
}
```

And could be used in the pipeline script like this:

```nextflow
    def collated_versions = softwareVersionsToYAML(
        NFCORE_PIPELINE.out.versions,
        channel.topic('versions'),
        channel.of(workflowVersionToYAML()),
    ).collectFile(storeDir: "${params.outdir}/pipeline_info", name: 'nf_core_pipeline_software_mqc_versions.yml', sort: true, newLine: true)
```

Nothing needs to be done on the test side (apart from updating the snapshots to capture updated content), since we were already capturing the versions from the `nf_core_pipeline_software_mqc_versions.yml` published file only.

# Drawbacks

- Need to migrate the syntax once nf-test support topic channels

# Alternatives

- Add some topic handling in the nft-utils plugin.

# Adoption strategy

- Initial "meta-RFC" for the RFC process itself
- Several upcoming projects have already been flagged as being suitable for an RFC
- Core team nurture these initial RFCs and monitor process, adapt protocol as necessary
- Blog post + message on `#announcements` when the website documentation is complete.

# Unresolved Questions

- Whether the multi-step process (especially issue + PR) is suitable.
- Whether people understand the differences between steps and what is expected.

# References

- Slack discussion ([core-team channel](https://nfcore.slack.com/archives/C08TKFDUNHG/p1756395096777469))
- Reference Issues: https://github.com/nf-core/proposals/issues/46
- nf-test issue: https://github.com/askimed/nf-test/issues/258
- nf-core-utils plugin: https://github.com/nf-core/nf-core-utils
