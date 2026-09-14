# ADR DIR 013 — complete scene source review with global discourse reconciliation

Status: implemented and tested for the bounded scope in
ANNOTATION_WINDOW_CONTRACTS.md. Original DIR checkpoint remains BIE-DIR-QA-007
(37/37); broader DIR implementation and BIE acceptance remain open. Canonical
baseline remains `bc3147db408fc5a5d54017c8b907f580477ff2c3`.

## Problem

Batch 012 can generate larger lessons through complete source/PED decision
windows. Annotation still sent all pages, plan and speech in one request. A valid
eight-scene input exceeded its 180,000-character transport limit. Independent
review could approach or exceed its own 260,000-character limit. Dividing source
analysis must not lose exact spoken text, source conditions, assessment identities,
cross-scene questions, antecedents, transitions or repetition.

## Decision

Annotate each complete scene against full relevant source pages and prerequisite/
RE context. Keep exact utterances and offsets. Produce local claims, advisories,
emphasis and pacing under per-scene ID namespaces. Reconcile discourse,
transitions, terms and repetition once against every actual spoken utterance and
the complete assessment/plan/structured-context record. Assemble the two result
sets and run the original full-script validator.

Review every source scene independently and retrieve complete supporting scenes
when annotation relations cross boundaries. Review all speech separately for
global discourse and completeness. Aggregate each subject conservatively: ISSUE
dominates, then UNCERTAIN, and SUPPORTED requires support from every applicable
scope. Continue remaining scopes after a review failure and retain that failure as
uncertainty. A failed annotation scope blocks assembly because complete speech
coverage is mandatory.

Persist compiled-in scoped production/review types and reconstruct their request
fingerprints from actual inputs, source, speech, policies, local candidates and
retry feedback. Revalidate them in existing downstream consumers. Preserve the
registered executor, base generation, revision/repair and candidate APIs.

## Consequences

The documented larger fixture can pass annotation and review without cutting
pages or speech. Cross-scene question/reference and transition checks remain
global. Source factual truth remains with complete scene source review and the
existing per-claim evaluator; the no-page global discourse request cannot claim
that evidence role. All outputs stay review-required and acceptance remains false.

One complete scene/source/support scope or the complete spoken lesson can still
exceed configured budgets. Those conditions fail explicitly. Hierarchical global
discourse retrieval, partial scene checkpoints, selective correction/review reuse,
production recovery/adoption and empirical live-model quality remain future work.

The change adds annotation_window_context.py, windowed_annotations.py and
windowed_annotation_review.py. It extends narration_annotations.py,
annotation_review.py, recovery_codec.py and director_consumers.py with documented
before/after provenance. Default policies keep their earlier behavior. Original
archives, prior hardening and canonical files remain preservation authorities.

No UI questionnaire, fixed lesson duration, universal scene template, alternate
Book-to-LLM path or reduced video/playable-game requirement is introduced.
