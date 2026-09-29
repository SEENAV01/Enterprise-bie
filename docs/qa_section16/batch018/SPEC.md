# REPRO001–003 bounded reproduction contract, version1

## Inputs and trust
`ReproPolicy` is operator-owned and supplied separately from `ReproRequest` and the
source snapshot. It pins the complete input snapshot, producer bytes, canonical
parameters, seed/epoch, observed environment profile and all required output paths.
The producer is a trusted Python script already inside that snapshot. It receives
exactly two positional arguments: the generated job JSON path and a new output
directory. No shell or candidate-supplied command list is accepted.

The job JSON contains `schema_version`, `job_id`, `seed`, `source_date_epoch`,
`parameters`, `input_directory` and `source_digest`. The input directory is private
and differs across reruns: embedding it in an output is a real byte difference,
not a permitted normalization. Use explicit seeds in random libraries and avoid
wall-clock-dependent outputs when exact determinism is required.

## Public Python API
1. `capture_environment(python=base_python, seed=17, source_date_epoch=0)` actually
   creates a disposable stdlib-only environment and returns canonical profile JSON.
   An operator must independently approve that profile; candidate assertions are
   not authority. The API neither downloads nor installs dependency packages.
2. Build `ReproPolicy` from verified `Snapshot` / `ArtifactRef` input identities and
   `OutputSpec` entries. Optional golden hashes should come from independent review.
3. `collect(job_id, source, source_root, new_evidence_root, policy, as_of=clock)`
   recreates and runs the approved producer in fresh environments, publishing an
   immutable execution manifest and actual produced files. It returns `ReproRequest`.
4. `evaluate(request, source_root, evidence_root, policy, as_of=clock)` rechecks the
   evidence bytes. Default trust is empty: unsigned healthy evidence requires review.
5. Separate operator-provisioned `ReviewVerifier` / `Review` records may authorize
   inventory and execution for this exact request/policy. Synthetic test keys must
   never be installed in production. Authentication does not prove rater correctness.

## Evidence and outcomes
The execution manifest binds the source, policy, producer, collector and probe code.
Each run has a unique execution ID, actual environment-build/probe/producer process
records, non-overlapping ordered wall clocks, environment snapshots, original venv
configuration, lossless log bytes in a JSON envelope and output artifact references.
The manifest is unsigned, not remotely attested. All evidence must reside in the new
root; hidden files, links, partial inventories and reused execution IDs are rejected.

`CHECKS_PASSED` means only the bounded profile checks passed with authorized reviews.
`REVIEW_REQUIRED` means evidence/trust remains insufficient. `BLOCKED` means a known
failure. No status sets `product_accepted` or `full_product_reproduced` true.
The unsigned release bridge emits FAIL for blocked checks and NOT_RUN otherwise.

## Limits
POSIX; base Python supporting `-P`; repeated trusted producer scripts2–5; phase
execution1–60seconds; bootstrap30seconds; probe10seconds; one output<=16MiB and
all outputs<=64MiB per run; snapshot limits inherited. Workers have CPU/address-
space/file-descriptor/file-size limits. These are not hostile-code or network
isolation. Selected stdlib hashes do not attest shared libraries, the kernel,
containers, fonts, GPUs, remote models or the full imported dependency closure.

## Read-only CLI
```
python -B -m bie.qa.reproducibility_v2 \
 --request request.json --policy policy.json --source-root source \
 --evidence-root evidence --as-of 1801000000 --output audit.json
```
Use the appropriate actual evaluation clock, not the diagnostic example clock.
Output must be new and outside the source/evidence trees. Exit0=bounded checks,
2=blocked,3=review required,4=invalid input/IO. This CLI does not execute producers,
load signing keys, install environments or mutate any repository.

## Tests and delivery
```
python -B scripts/verify_qa_repro18_batch018.py --output /absolute/new/test-results
python -B scripts/verify_qa_repro18_mutations.py --output /absolute/new/probes
python -B scripts/demo_qa_repro18.py --output /absolute/new/diagnostics
python -B scripts/recheck_qa_repro18_diagnostics.py evidence/qa_section16/executed_run_018/diagnostics
python -B scripts/verify_qa_section16_package.py
```
Diagnostic rechecking reads stored files; it is not fresh producer execution.
