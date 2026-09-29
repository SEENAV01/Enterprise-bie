# Reproduce Batch 007 locally

Run commands from the extracted package root. Test execution here used Python 3.13.5
and the exact installed packages listed in `requirements-qa16-batch007-tests.txt`.
No package installation, network, live model or renderer is needed by the evaluator.
Install the test-only dependencies in a controlled environment before the full suite.
The requirements record tested versions; a lock with downloaded package hashes and
cross-platform environment reproduction is still a deployment obligation.

```sh
python -B scripts/verify_qa_section16_package.py
python -B -m unittest discover -s tests/qa_director16 -v
python -B scripts/verify_qa_director16_batch007.py --output /absolute/new/evidence
python -B scripts/verify_qa_director16_mutation_probes.py --output /absolute/new/probes
python -B scripts/run_qa_director16_demo.py --output /absolute/new/demo
```

Each evidence folder must be new; no overwrite is allowed. Keep generated receipts
outside the extracted tree when checking the package manifest before/after execution.
The full runner separately executes all inherited batch suites and preserves their
individual counts. Fixed test timestamps and explicitly synthetic positive assessment
keys are test fixtures, never current-time production approval.

The package includes an unsigned authored example:

```sh
python -B -m bie.qa.director_v2 \
  --request examples/qa_section16/director_checks/request.json \
  --policy examples/qa_section16/director_checks/policy.json \
  --artifact-root examples/qa_section16/director_checks/artifacts \
  --as-of 1800000000
```

Expected CLI result: REVIEW_REQUIRED, exit 3. Exit 0 means only local checks passed;
exit 2 is BLOCKED, exit 4 invalid input/filesystem error. The CLI does not load trust
keys. Programmatic callers supply independently governed `ReviewVerifier` and
`AssessmentVerifier` instances, assessments, a trusted evaluation clock and an
operator-controlled policy. Never promote fixture keys into a production trust store.

For a trusted, independently checksum-verified ZIP, the archive verifier performs
safe extraction, before/after manifest checks, all batch regressions, frozen-input
reconstruction and optional corruption probes. Review code before executing it.

```sh
python -B scripts/verify_qa_director16_archive.py \
  --archive /absolute/delivery.zip --sha256 ACTUAL_PUBLISHED_CHECKSUM \
  --output /absolute/new/archive-check --corruptions
```

Checksums establish byte identity, not publisher authenticity. Byte-identical ZIP
reconstruction only concerns the same frozen files and compression environment.
