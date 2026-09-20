# R04 capture-helper coverage correction

This is a guarded continuation of the three preserved R04 execution attempts, not an additional COMP feature batch. The original pinned execution found qa-paint-helper.js absent from the TypeScript program while its same-basename declaration was present.

The prepare job reproduces the configuration defect (8 tests: exactly one failure and one error), adds only explicit helper membership to produce_actual_paint, then requires all 8 tests and the unchanged assembly/canonical/post-DIR preservation checks to pass. It retains complete before-images and changes only the active canonical hashes in adoption ledgers. A new source commit is published by a non-forced update of validation/comp-r04-20260920, guarded by the exact expected parent and unchanged main. No merge is performed. Only the prepare job receives contents:write, and its token is passed only to the guarded publisher step.

Downstream read-only jobs check out the NEW source SHA. They run the existing canonical regression (at least 6,485 original + 8 new tests, no skips), and the existing checked compile/render validator with the retained dependency lock. The original driver remains byte-identical; run_candidate.py binds it explicitly to the new SHA/tree after verifying its Git blob identity. Historical dependency/render failures and acceptance flags are not rewritten.

Real TypeScript 5.9.3 language probes, actual-paint capture, smoke/full rendering, decode, all-frame extraction, and fresh-project replay are distinct gates. All failure artifacts are retained. A two-second synthetic tone fixture cannot establish spoken narration, textbook learning quality, cinematic quality, or product acceptance.
