# Batch001 audit and scope decision

The five demonstrated code issues in BATCH001_AUDIT_FINDINGS.json were first reproduced (three assertions failed and two typed-rejection tests errored), repaired in their owning original tasks, and included in the final 254-test passing run. Before-images and failed execution logs are retained. These are development repairs, not five extra completed atomic tasks.

The initial domain test run also exposed three test-authoring mistakes: a helper called reference_output without its separate task_id/inputs arguments; a hand-written assertion for 1 + 2(-2) + 3(-2)^2 incorrectly said 7 rather than 9; and a Boolean input assertion expected the wrong typed error code. They were corrected to the documented API and independently checked arithmetic, not by changing scientific fixtures or weakening the production evaluator. One repair iteration omitted a field import; that failed run is retained. A unit-test SQLite setup handle was explicitly closed to remove its ResourceWarning.

Decision: release a recoverable **Batch001 local scoped implementation checkpoint**. Do not certify the whole section, hidden benchmark quality, complete domain coverage, canonical compatibility, native output quality or the BIE product. The six source-linked packs have 60 authored development cases, with manually authored expected calculations/rejections and derivations. They are useful for testing evaluation machinery and seeded defects; they are not independent real-book or learner evidence.

The remaining 40 original tasks, golden corpus work, bounded-leakage scale adapter when required, later metric/rater/floor implementation and exact native integration remain open. Read the gap ledger. No material acceptance condition is silently deleted or converted into PASS.
