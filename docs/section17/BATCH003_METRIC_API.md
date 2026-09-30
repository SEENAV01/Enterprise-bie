# Candidate-driven metric API, shared by METRIC001..006

## Trusted boundaries
The evaluator, pinned reference/rubric, hashes, captured source bytes and campaign identity must be controlled outside the candidate. Bundled fixtures are public DEVELOPMENT diagnostics. Passing them does not establish holdout performance, security or real-book quality. References and candidate content use strict JSON; canonical SHA256 binds exact serialized values. Owner/evaluator IDs are labels, not authentication.

## Measure an actual structured candidate
Run this Python snippet from `combined_source/` to materialize one demonstration in a new external folder; edit only candidate.json for candidate experiments and use a fresh governed campaign when changing the rubric. The reference SHA must be selected by a trusted evaluator, not taken as proof just because the same candidate submitted it.
```python
import json
from pathlib import Path
from bie.evaluation.benchmarks.models import digest
f=json.loads(Path('bie/evaluation/benchmarks/metrics/fixtures/BIE-EVAL-METRIC-001.json').read_text())
out=Path('../metric-input-new');out.mkdir(exist_ok=False)
for name,obj in [('reference',f['reference']),('candidate',f['cases'][0]['candidate']),('artifacts',f['source_artifacts'])]:
    (out/(name+'.json')).write_text(json.dumps(obj,indent=2))
print('PINNED_REFERENCE_SHA=',digest(f['reference']))
print('CANDIDATE_SHA=',digest(f['cases'][0]['candidate']))
```
Then run the CLI shown in every metric task SPEC with these actual hashes. All file paths are chosen by the operator, not executable instructions embedded in candidate text. METRIC001 requires actual source_artifacts; other metrics accept no artifact map beyond empty. No network/provider calls are made.

## Result semantics
MEASURED+PASS: complete declared weighted credit and no defects. MEASURED+FAIL: one or more omissions, mismatches or invalid extra assertions; score remains diagnostic, never a release authorization. BLOCKED: malformed/unsupported inputs or missing/tampered evidence; no numeric score. The persistent store retains accepted blocked attempts. Inputs with invalid candidate/reference snapshot pins are rejected before registration rather than attached to an unbound identity.

The denominator is trusted. Omitted candidate items remain zero-credit terms. Unrecognized IDs/extra schema fields are rejected, not silently skipped. Some metrics can have score_exact=1 with outcome=FAIL (for example all goals derived plus an unsupported extra step); outcome/defects must always be consumed alongside score.

## Persistence and reproducibility
MetricRunStore uses SQLite transactions, one run identity, duplicate candidate prevention within a campaign+metric, reference/evaluator-code pinning, recorded receipt identity and receipt hashes. Repeated identical attempts do not become a better score. Cross-campaign governance, off-host immutable anchoring, identities, signatures and secure database/filesystem custody are deployment responsibilities. Existing symlink preflight is not race-proof; untrusted processes must not share evaluator-writable directories. An attacker able to rewrite both receipt and receipt hash can defeat local hash-only custody.

The calculation result is deterministic for fixed inputs/code and does not include wall-clock timestamps. Packaging timestamps/log times may vary across separately executed tests; deterministic ZIP rebuild means identical bytes from the same fixed evidence snapshot, not identical timing across fresh runs.

## References and model validity
Metric formulas and profiles here are local design choices, not claims of compliance with a validated published benchmark or an official W3C grading standard. Source-reference metadata records basis identifiers/links. Captured grounding text is original authored fixture text. Concept, prerequisite, proof and causal references require independent subject validation before golden usage. Reference model validity and measured learner benefit remain open gates.
