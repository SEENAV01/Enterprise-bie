# Runbook — Batch 005

Extract into a fresh directory, not over a checkout. Work from the extracted root.
Use Python 3.13.5 for the environment tested here. Runtime mathematics uses the standard
library and earlier packaged BIE modules. Schema tests need the separately pinned packages
in requirements-qa16-batch005-tests.txt. No service credentials are supplied. Pip packages
are not vendored or security-certified by this archive.

```sh
python -m pip install -r requirements-qa16-batch005-tests.txt
python -B scripts/verify_qa_section16_package.py
python -B scripts/verify_qa_math16_batch005.py --output ../qa005-replay
python -B scripts/verify_qa_math16_mutation_probes.py --output ../qa005-mutation-replay
python -B scripts/run_qa_math16_demo.py --output ../qa005-demo
```

Output directories must not already exist. Keep fresh receipts outside the extracted
package: its exact manifest intentionally rejects extra files, including caches.
The cumulative runner executes Batches 005,004,003,002,001 and the original release
contract; reruns do not increase unique test counts. Use `-B` to suppress caches.

The demo creates authored source/script text and clearly marked non-render/non-game
fixtures. It calls no model, provider or real book. It succeeds as a demonstration when
unsigned math reports require review and full release remains blocked. Its mathematical
counterexample illustrates loss of the negative root; domain cancellation remains unknown.

To inspect its unsigned report independently, from this package root:
```sh
python -B -m bie.qa.math_v2 \
  --request ../qa005-demo/request.json \
  --policy ../qa005-demo/policy.json \
  --artifact-root ../qa005-demo/assets \
  --as-of 1800000000 \
  --output ../qa005-unsigned-report.json
```

This example uses the fixture's fixed logical time, not a current clock. Expected exit
code is 3 (REVIEW_REQUIRED), not 0. Other exits: 2 BLOCKED; 4 invalid input/IO; 0 only when
the entire declared typed contract passes through the Python API with proper reviews.
The local CLI intentionally has no secret-loading feature and cannot self-authorize
operational reviews. Reports are written with exclusive creation and cannot overwrite
an existing file. Its --reviews input may carry records but never provisioning keys.

For a production caller, construct immutable MathRequest and an independently governed
MathPolicy; supply separately provisioned ReviewVerifier and source AssessmentVerifier
to evaluate(). Verify all returned report identities and retain actual report bytes.
Do not import test-fixture signing helpers into an application. Recompute through
verify_reports() or the bridge when binding release evidence. Never sign a partial text
report as a full rendered-media math pass.

Future integration: read latest HEAD, compare all existing dependency bytes, stage only
approved additive paths, review caller migration, run full repository regression, verify
remote readback after explicitly authorized integration. QA_SECTION16_CONTINUATION.json
is a lane checkpoint, never a replacement for task_registry/continuation.json.
