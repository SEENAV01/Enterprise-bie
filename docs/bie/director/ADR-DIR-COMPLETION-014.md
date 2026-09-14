# ADR DIR 014 — close Director implementation scope without weakening acceptance

## Status

Accepted for implementation. Product acceptance remains open.

## Context

Batch 013 supported complete-scene source annotation and one bounded global
spoken-discourse reconciliation. The capability audit still identified rich
teaching codecs, authenticated grade provenance, hierarchical long-discourse
review, scene-local correction, durable worker recovery, production composition
and external calibration as Director-side implementation gaps.

## Decision

Extend the existing registered `DIRECTOR` stage and existing artifacts rather
than introduce a parallel pipeline. Use typed source-bound rich obligations;
provider-neutral grade and benchmark verifiers; hierarchical leaf, boundary and
retrieval scopes; named-scene correction with global revalidation; SQLite/CAS
durability with epoch fencing; and one strict production composition root.

Preserve the original full validators after decomposition. Preserve exact source,
RE, PED, assessment, scene and revision identities. Allow reuse only for unchanged
local evidence under identical policy/identity. Execute global discourse/review
fresh after a scene edit. Treat all model/verifier outputs as review evidence,
never automatic mastery, release or acceptance.

## Consequences

The DIR implementation scope can exit with downstream typed preview handoffs and
explicit empirical acceptance gates. Full BI/OCR quality, live provider quality,
expert benchmark sufficiency, rendered video/audio and playable-game execution
remain separate evidence owned by their production/acceptance stages. Resource
overflow and missing external evidence remain named failures or `NOT_RUN`; no
content truncation or synthetic success is permitted.

