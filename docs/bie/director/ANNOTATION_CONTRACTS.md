# DIR narration annotation and review — batch 009

Current additive checkpoint: **BIE-DIR-HARD-ANNOTATION-QA-001**. New tasks are
BIE-DIR-HARD-ANNOTATIONS-001 and BIE-DIR-HARD-ANNOTATION-QA-001. Original checkpoint
BIE-DIR-QA-007 remains 37/37 original entries. The original 867-row roadmap and
recovered vision are unchanged. **DIR section implementation is incomplete;
BIE is NOT ACCEPTED.**

## Implemented execution

The existing grounded director produces the source/RE/PED-bound lesson and its
whole-utterance factual evidence. An injected `AnnotationRuntime` now extends the
same `DirectorStageExecutor`; there is no second orchestration framework.
Applications configure canonical ModelProvider objects for the annotator and a
separately identified reviewer, then register the executor using the existing
`register_director_stage` function. The combined walkthrough demonstrates this route.
The base constructor without annotations remains supported and is regression-tested;
it retains the earlier annotation-missing review behavior.

The annotator is actually invoked with the exact script, complete cited source
pages, actual RE/PED objects, concept IDs, existing assessment bindings, character
positions and pacing obligations. It produces:

| Output | Enforced boundary |
| --- | --- |
| Claims | Exact quote/character spans; every spoken word and every non-whitespace character, including punctuation and operators, appears exactly once in the partition; source citations remain within the utterance |
| Discourse | Every utterance has actual concept introduction/requirements, prior-reference and question/answer records; concept IDs come from the supported upstream objectives |
| Transitions | Every actual scene boundary has a literal cue in the entering utterance, or an explicit unresolved record; no invented transition speech |
| Terms and advisories | Literal narrated terms/definitions or explicit missing definitions; advisories attach to actual spans; no inferred learner age or grade |
| Repetition purposes | Two complete ordered sentences, shared evidence/objectives and a declared learning purpose; no deletion |
| Emphasis | Exact nonoverlapping word anchors with source/concept bindings and bounded strength |
| Pacing | Complete text partition, actual teaching mode and assessment response-time obligations; no arbitrary lesson-duration cap |

Canonical DIR types are reused: ScriptClaim, DiscourseBeat, NarratedTransition,
TermRequirement, ContentAdvisory, RepeatPurpose, EmphasisAnchor and PacingBeat.
Raw outputs are retained with request/response fingerprints, bounded attempts and
revision bindings. Parsed objects are checked against their retained response so
later mutation cannot silently reuse old review evidence.

## Independent review and QA

A separate configured model identity executes annotation review. Its payload has
the actual source, narration, decisions, proposed annotations and exact subject
IDs. Every annotation and all eight completeness dimensions must receive a
revision-bound judgment. The reviewer checks omitted facts and presuppositions,
concept foundations, antecedents, questions, causal bridges, definitions,
term/advisory omissions, repetition, emphasis and pacing. Labels alone do not
establish those interpretations.

Default reviewer trust is empty. Reported ISSUE judgments block; uncertain,
low-confidence, incomplete, refused or unlisted review remains REVIEW_REQUIRED.
An explicitly policy-listed reviewer can authorize scoped repetition exceptions
or audience annotation-completion status only for the corresponding supported
subjects and completeness checks. A model cannot supply that policy or completion
flag itself. Separate identity means separate configuration, not proof of statistical
independence, factual truth or calibrated teaching quality.

BIE then recomputes actual coherence, repetition, audience and pacing QA using the
produced contracts. Fine claim factual review executes through the existing critic.
The previous whole-utterance factual guard remains in the result: changing every
fine claim to QUESTION/INSTRUCTION cannot erase an earlier contradiction or evade
implicit-fact review. Missing foundations, forward references, explicit response-time
shortfalls and review issues are represented as real QA findings.

Emphasis recomposes the existing estimated TIME events and scene timeline. Actual
narration, source bindings, assessment questions/answers/criteria and pause contracts
remain unchanged. This is planned timing, not a modified or verified audio waveform.
A model-requested reflection shortfall is reported; this batch does not silently
rewrite text or perform selective repair to make QA pass.

## Audience policy boundary

AudienceTarget and term-level/advisory-age rules are optional application-supplied
curriculum policies. They are not answers to a mandatory learner questionnaire or
model predictions. Without a target, AUDIENCE_TARGET_UNSPECIFIED remains. Terms
without a declared level or narrated scaffold remain under review. An advisory
without an explicit age rule uses the existing contract's neutral integer zero
and carries ADVISORY_AGE_POLICY_UNSPECIFIED; zero is not a claim of suitability
for all ages. Consumers must respect the review metadata and explicit policy.

The controlled advisory test uses a fictional declared curriculum age boundary to
verify the contract; it is not an empirical age recommendation. Non-English lexical
and sentence heuristics retain their existing uncalibrated-language review.

## Artifact lifecycle and replay

The original director base candidate is persisted as evidence.director_base_execution
before annotations execute. If annotation production fails, that actual lesson,
its factual evidence and a CAS failure receipt remain available; completed failure
replay does not call the providers again. Successful annotation evidence includes
both original and current QA, raw annotation/review responses, identities, policies
and exact fingerprints. Source, narration or annotation changes invalidate old
bindings. Corrupt ancestor bytes fail replay before regeneration.

New payload versions are `bie.dir.annotated_execution/1.0.0` and
`bie.dir.annotated_plan/1.0.0`, within the existing canonical artifact envelope
schema. The enclosing output type remains director.plan. The original base payload
versions remain supported for the mode without annotations. Idempotency includes
the annotation/reviewer policies and identities; changing them cannot reuse an
incompatible cached result under the same key.

An annotation QA blocker persists evidence and fails the stage without publishing
a director.plan. Review candidates remain requires_review=true, release_ready=false,
accepted=false. Generic orchestration success is component completion only. Actual
VIS/ANI/compiler/game consumer review gates and selective invalidation/repair are
still required. No exactly-once external model-service guarantee, cross-store
transaction or durable catalog-index recovery is claimed.

## Reproduce the verified batch

```bash
python scripts/check_dir_annotations.py
python examples/annotated_director_walkthrough.py --output verification/annotated_director.json
```

429 tests in 50 files pass: 286 original DIR tests, 98 earlier hardening tests,
18 annotation producer tests, 18 review/composition tests and 9 new stage integration
tests. No earlier test was edited, deleted or skipped. The separate pinned canonical
gate passes 2,160 tests in 551 files; it still does not discover staged DIR.

The walkthrough uses three authored source domains and actual canonical RE/PED
functions, including temporal event_order in history. Across two, one and three
scenes it produces 15, 13 and 14 finer claim spans, respectively. There are nine
planning/narration calls, three annotation calls, three annotation-review calls and
53 factual-critic calls (15 original whole-utterance plus 38 finer FACT spans).
All providers are explicit preauthored protocol fixtures. All cases remain
REVIEW_REQUIRED. No live model, real PDF pipeline, audio/video render, simulation
runtime or playable game executed. These results verify contracts, execution and
failure handling; they do not measure teaching or annotation accuracy.

Both atomic ZIPs declare dependencies and are tested in fresh extraction directories.
The combined ZIP contains a ready-to-run workspace, all 37 original DIR ZIPs,
all six additive hardening ZIPs, exact before/after evidence and current documents.
Apply original dependency closures before additive overlays in order. Original ZIPs
must never overwrite earlier contract corrections. The one intentional prior-source
change extends director_executor.py; its exact previous bytes are retained.
All other prior source/tests and all copied canonical dependencies remain unchanged.

## Remaining implementation and evaluation

These producers and review wiring now exist; do not redo their tasks. Current
concept annotations use the supported upstream objective concept IDs. Rich KI/math/
prerequisite/mastery bridge codecs, broader teaching modes, long-context segmentation,
selective repair/invalidation, recovery and typed consumer review contracts remain
concrete implementation work. General nonspoken directing/visual intent requires its
own downstream checks; this batch annotates actual speech.

Annotation/definition/discourse correctness, pedagogical quality, multilingual
behavior and audience policies require independent real-source evaluation and
live-provider calibration. Prompts and protocol fixtures do not close those gaps.
Re-audit required DIR capability before section-end canonical GitHub integration
in this chat. No GitHub write is made in this batch.

Keep the original video AND playable revision-game paths, structured IR, evidence
provenance, replaceable providers/tools, uncertainty and governed cumulative PDF
learning. No mandatory questionnaire, fixed universal scene template, arbitrary
lesson-length limit or direct Book-to-LLM-to-Remotion shortcut is introduced.
