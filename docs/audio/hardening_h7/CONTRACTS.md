# AUDIO Hardening H7 Contracts

Scope: segment-level durable cache lifecycle and deterministic bounded long-book planning using the existing canonical CAS, idempotency and lease contracts.

This batch does **not** claim neural-provider live acceptance, pronunciation calibration, paid-provider recovery, canonical DIR/ANI/COMP handoff, actual video render, real-book E2E or product acceptance.

Key invariants:
- cache identity is content/configuration-bound and excludes run/job IDs for governed cross-run reuse;
- source refs, script/utterance/segment identity, provider/catalog/profile identity, preparation profile, stem identity and policy revision participate in cache identity;
- stored segment media is CAS-verified on read and paired with a receipt bound to identity and media hash;
- stale/abandoned claims require a new canonical lease epoch;
- orphan cleanup is bounded to the dedicated segment-cache CAS root;
- long-book batches preserve source order and never silently truncate segments;
- resume accepts only known completed segment identities;
- selective invalidation is by segment identity; global profile/stem/policy changes invalidate affected identities;
- no second BIE orchestrator is introduced.
