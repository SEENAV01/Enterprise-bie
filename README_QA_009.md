# COMP QA Batch 009

Read `BIE_COMP_ORIGINAL_BATCH_009_RESULT.md`, `docs/QA_001_005_SPEC.md`, and the capability audit.

Run from this directory: `PYTHONPATH=app python -m unittest discover -s tests -v`.

Benchmark: `python scripts/run_compiler_qa.py --output /tmp/bie-qa-new-output`. Exit 2 means source expectations match but full compile evidence is blocked. Product acceptance remains false.
