# Calibration examples

These are real past decisions from nf-core/proposals. Use them to calibrate your scores against how the core team actually decides. They are examples, not rules: each decision depended on the details of that proposal and on what the existing pipelines covered at the time. Compare the reasoning, not the topic. A new proposal in the same field can deserve a different score.

## nf-core/proposals#165: taxmarker (accepted)

**Proposed:** a pipeline to find mislabelled sequences in marker-gene reference databases (e.g. 16S), using SATIVA-style leave-one-out phylogenetic placement.

**Decision:**

- Approved within two weeks with no objections. The comment that closed it: "there's no existing overlap and there's good adherence to guidelines + a community need."
- A working implementation already existed, built with nf-test, passing lint, with test data on nf-core/test-datasets.
- It had been discussed on the nf-core Slack since 2024. It sits upstream of nf-core/ampliseq and does not compete with it.

**Lesson:** a clean "no overlap" plus existing nf-core-style work and prior community discussion is what a clear accept looks like. Don't invent concerns to avoid a top score.

**Score:** 5/5. Specificity 5 (one data type, one analysis), Novelty 5 (no pipeline curates reference databases), Testability 5 (test data already hosted), Sustainability 4.

## nf-core/proposals#155: strcalling (accepted after debate)

**Proposed:** genome-wide short tandem repeat (STR) calling from short-read BAM/CRAM, with several callers, EnsembleTR consensus and tumour-normal support.

**Decision:**

- One reviewer asked whether it should be a subworkflow, because nf-core/raredisease and nf-core/longraredisease already run `stranger` and `trgt`.
- The proposer showed the difference: those tools are long-read or annotation-only, and rare-disease pipelines target a few known loci, not the whole genome.
- Others agreed it is a full pipeline "rather than trying to shoehorn it into sarek". It should accept sarek BAM/CRAM outputs.
- The solo-developer concern was raised on Slack. Approvals followed after the proposer recruited a student and other contributors.

**Lesson:** a tool name that also appears in another pipeline is not overlap if the data type or scope differs. Sustainability concerns are fixable and should lower the score, not decide it.

**Score:** 4/5. Novelty 4 (short-read, genome-wide, multi-caller), Specificity 4, Sustainability 3 at submission.

## nf-core/proposals#25: rsvrecon (merge-with-existing)

**Proposed:** an end-to-end RSV pipeline: QC, BWA alignment, consensus, genotyping, F-protein mutations, phylogenetics and clinical reports.

**Decision:**

- Reviewers found little that was RSV-specific apart from automated reference selection (KMA). Everything else is already in nf-core/viralrecon.
- The viralrecon developers were already working on RSV support and wanted the reference-selection step.
- A core member: "we can't do a separate viralrecon derivative for every major virus family."
- The proposer agreed to contribute the RSV-specific parts to viralrecon. Phylogenetics was noted as a better fit for its own pipeline.

**Lesson:** an organism-specific proposal where one step differs is a merge. "Designed specifically for X" is not evidence that the tooling differs.

**Score:** 2/5. Specificity 1 (organism-specific, generic tooling), Novelty 2 (one step), Testability 3 (code was not public at submission).

## nf-core/proposals#93: cosimflow (merge-with-existing)

**Proposed:** a small pipeline that computes cosine similarity matrices and heatmaps from gene expression tables.

**Decision:**

- Ewels: "a little on the small side for nf-core, though that need not be a blocker by itself."
- nf-core/rnaseq (DESeq2 sample clustering) and nf-core/differentialabundance (sample dendrograms) already do similar analyses. A filtering module already exists.
- Reviewers recommended a module or subworkflow first. jfy133 rejected it "as a full pipeline now as it's a little too small", and invited a new proposal if the scope grows.
- The proposer was new to Nextflow and working alone.

**Lesson:** one script plus a plot is a module, not a pipeline. A subworkflow is a good outcome to recommend, not a consolation prize.

**Score:** 2/5. Novelty 1 (subworkflow-sized, partly covered), Sustainability 2 (solo, first Nextflow project), Specificity 3.

## nf-core/proposals#138: PlastizymeFinder (merge-with-existing)

**Proposed:** metagenomics from raw reads to plastic-degrading enzyme candidates: QC, profiling, assembly, binning, annotation, MeTarENZ search and AlphaFold2 validation.

**Decision:**

- Reviewers saw most of the workflow as "a near-exact copy of mag", with the profiling part a slimmer nf-core/taxprofiler.
- The new part (MeTarENZ against a PET database) fits nf-core/funcscan or nf-core/proteinannotator. Structure prediction belongs in nf-core/proteinfold.
- jfy133: "really MOST functionality is already covered in separate pipelines". Chaining pipelines with downstream samplesheets covers the rest for now.
- The proposer agreed to add plastic-degradation subworkflows to the existing pipelines.

**Lesson:** when a proposal re-implements a long upstream workflow to reach one novel step, score it on the novel step alone. If that step fits an existing pipeline, it's a merge.

**Score:** 2/5. Specificity 2 (re-implements nf-core/mag), Novelty 2 (one subworkflow's worth), Testability 3 (AlphaFold2 is heavy for CI).

## nf-core/proposals#158: epigenomeanalyser (turned-down)

**Proposed:** one pipeline that processes RNA-seq and ChIP-seq/CUT&RUN/CUT&TAG from FASTQ, runs differential analysis on each, then merges results to link transcription factors to expression.

**Decision:**

- Reviewers were "wary about reimplementing three nf-core pipelines" (nf-core/rnaseq, nf-core/chipseq or nf-core/cutandrun, nf-core/differentialabundance) to save users from running three pipelines.
- nf-core is moving towards smaller modular pipelines joined by pipeline chaining, which is now official in Nextflow: "it's hard to justify separately maintained mega-pipelines like this."
- A large pipeline from a solo developer was seen as hard to maintain.
- The integration step or CUT&RUN differential binding could be proposed separately. The proposer agreed it was not a good fit.

**Lesson:** a "one-stop" pipeline that wraps existing nf-core pipelines fails specificity. Integration value belongs in a separate downstream step that takes their outputs.

**Score:** 1/5. Specificity 1 (several data types, duplicates three pipelines), Novelty 2 (only the merge step), Sustainability 2 (solo, large scope).
