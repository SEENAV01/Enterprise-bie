# Golden Benchmark Governance

## Change control
Golden cases are versioned test assets. Any change to expected truths, hard floors, forbidden claims or required representations must include:
- benchmark case id
- before/after diff
- reason
- reviewer
- date
- affected regression baseline
- version bump.

## Anti-gaming rule
Do not change benchmark expectations merely because the current implementation fails them.

## Evaluation evidence
Every metric result must record evaluator identity/version and evidence references. Model-based evaluators should be calibrated against human-reviewed samples.

## Expansion rule
The core suite starts with five domain families. Enterprise certification should expand toward multiple difficulty bands and textbook styles inside each domain rather than relying permanently on one case per domain.
