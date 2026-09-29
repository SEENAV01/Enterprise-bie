# Pedagogy QA API and local verification

Runtime: Python standard library plus the included preserved BIE contracts.
Tested environment and exact test-dependency versions are in the execution receipt;
`requirements-qa16-batch006-tests.txt` records the versions used. The pins are not a
claim that arbitrary platforms or clean dependency installation were verified.

From a fresh extracted package, use an external, new evidence directory:

```bash
python -B scripts/verify_qa_section16_package.py
python -B scripts/verify_qa_pedagogy16_batch006.py --output ../pedagogy-verification
python -B scripts/run_qa_pedagogy16_demo.py --output ../pedagogy-demo
python -B scripts/verify_qa_pedagogy16_mutation_probes.py --output ../pedagogy-mutations
```

The demo exits successfully when expected failures/review results are observed;
it is not a product acceptance demo. The test runner refuses to overwrite existing
evidence directories. Keep generated receipts outside the frozen extracted tree
so exact manifest verification still works afterward.

## Unsigned CLI

```bash
python -B -m bie.qa.pedagogy_v2 \
  --request ../pedagogy-demo/request.json \
  --policy ../pedagogy-demo/policy.json \
  --artifact-root ../pedagogy-demo --as-of 1800000000
```

That timestamp is the deterministic synthetic fixture time, not the current time.
CLI returns 0 for local checks passed, 2 blocked, 3 review required, 4 invalid input
or filesystem error. The shipped CLI provisions no trust keys. Its normal healthy
unsigned plan requires review. Optional `--output` is create-only, never overwrite.

## Programmatic integration

`load_request`, `load_policy`, `load_reviews` live in `.codec`. `evaluate` accepts
`request`, `artifact_root`, `policy`, explicit `as_of`, and optional externally
provisioned review/source-assessment verifier objects. Policy and trust belong to
the operator, not candidate JSON. Use independently managed reviewers; never
provision the public synthetic fixture keys. `evaluate_objectives`,
`evaluate_sequence`, `evaluate_cognitive_load`, and `evaluate_assessment` return
individual reports while still recomputing all shared evidence checks.

`check_mastery_scores(points, requirement)` accepts complete criterion scores and
returns a deterministic score decision, not an observed mastery record.

`.bridge.prepare_release_evidence` returns unsigned evidence plus actual report
bytes. Store/report hashes exactly, authenticate only with an independently
controlled evaluator integration, and retain the full-media gate at NOT_RUN until
all relevant media evidence exists. Merely signing a partial report is not enough.

## Adapters and packaging

The native objective adapter requires explicit source spans, citations and policy
category. Native load, sequencing and blueprint adapters recompute native results
but return REVIEW_REQUIRED. The wrapper rejects an empty load scope even though
the pinned native loop alone can return a pass for no entries.

The integrated package is cumulative Section16 only. Each atomic archive contains
the same shared tested implementation with a primary-task designation. Do not
count their code/tests repeatedly and do not bulk-copy these snapshots into main.
Read QA_SECTION16_INTEGRATION_PLAN.json before eventual governed integration.
