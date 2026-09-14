# BIE DIR annotation and review windows — batch 013

This batch continues the original BIE director architecture after batch 012.
Original DIR 37/37 and all earlier hardening remain the baseline. DIR enterprise
implementation is incomplete and BIE is NOT ACCEPTED. The complete product still
requires high-quality video teaching and equally mandatory playable revision games
through the shared structured learning/game architecture.

## Implemented scope

`BIE-DIR-HARD-ANNOTATION-WINDOWS-001` adds complete-scene source annotation and a
complete spoken-lesson discourse reconciliation phase. `BIE-DIR-HARD-GLOBAL-REVIEW-001`
adds separately configured independent review for every source scene and the full
discourse scope. These are audit-derived additive implementation tasks, not entries
from the original 867-row ledger.

The existing registered `DirectorStageExecutor` uses the new behavior through the
annotation runtime's explicit policies:

```python
from bie.director.annotation_window_context import (
    WindowedAnnotationPolicy,
    WindowedAnnotationReviewPolicy,
)
from bie.director.annotated_directing import AnnotationRuntime

runtime = AnnotationRuntime(
    annotator, annotator_identity,
    reviewer, separate_reviewer_identity,
    policy=WindowedAnnotationPolicy(),
    review_policy=WindowedAnnotationReviewPolicy(),
)
```

The previous `AnnotationPolicy` and `AnnotationReviewPolicy` keep their original
single-request path. No automatic fallback changes an explicitly selected policy.

## Annotation phases

Each planned scene is an indivisible annotation unit. The request includes every
exact utterance in that scene, full relevant cited pages, source passages, original
PED/objectives/assessments, the actual RE closure and transitive prerequisite
support. The source view is derived from verified inputs and is never published as
an upstream artifact. It does not alter source bytes, the global plan or narration.

Local responses must partition every spoken word and every non-whitespace character
into claims and pacing records. Exact offsets, punctuation, math operators,
evidence/objective IDs and assessment response time are revalidated. Claim,
advisory, emphasis and pacing IDs use a scene-specific namespace. A local scene
cannot silently omit a source condition or collide with another scene's records.

After every scene succeeds, a separate global reconciliation request receives all
actual spoken utterances in their original order, the complete plan, all assessment
question/feedback bindings and the supplied structured concept/prerequisite context.
It produces every discourse record, adjacent scene transition, spoken domain term
and declared intentional repetition. The host then assembles the local and global
records and reruns the original full-script `validate_annotations` function.

The global request omits full source pages to stay focused on cross-scene speech.
It cannot establish factual entailment or page-level source completeness. Complete
scene source requests and the existing per-claim factual evaluator retain those
responsibilities. Structured concept definitions and conditions in the global
request remain source-bound upstream context; their presence does not prove they
were taught or understood.

## Independent review

Every source scene gets an independent review request with full relevant pages and
the annotation subjects that involve that scene. If an annotation references a
distant antecedent, question opening, term definition, transition or repeated span,
the scheduler includes the complete supporting scenes and their source context in
the review scope. It does not fabricate a summary of their wording.

A separate global review sees all spoken text and checks discourse, transitions,
questions/answers, terms/advisories, repetitions and supplied PED/prerequisite
consistency. Because its payload omits full pages, its source-consistency judgment
is limited to the supplied exact structured context and ordering. It does not
replace source-scoped review or factual QA.

Every annotation subject and all eight completeness dimensions receive one or more
scoped observations. Host aggregation is conjunctive:

| Scoped observations | Aggregate result |
| --- | --- |
| Any `ISSUE` | `ISSUE` |
| No issue, any `UNCERTAIN` or failed scope | `UNCERTAIN` |
| Every applicable scope supports the subject | `SUPPORTED` |

A failed source/global scope remains named in review evidence and contributes
`UNCERTAIN` judgments. Other scopes continue so observed errors remain visible.
Any failed scope keeps policy approval empty, including with a configured trusted
reviewer. Default reviewer trust remains empty. A model's `SUPPORTED` response is
reported evidence and never product acceptance.

## Evidence, persistence and repair

Each annotation/review call retains its scope ID, exact scene IDs, payload
fingerprint, response JSON, bounded attempt records and explicit failure. Known
frozen production/review result types are decoded by the restricted codec. JSON
cannot choose arbitrary classes. A window policy without its required scope
metadata fails at decoding; metadata cannot be stripped to obtain legacy behavior.

Revalidation reconstructs every request from actual source, input revision,
narration, local candidates, policies and retry feedback. It rejects missing,
extra, reordered or edited scope/attempt/response evidence. Downstream timing,
visual, animation and game-handoff consumers now revalidate persisted annotation
production and review before using the final speech/claims/timing result.

Existing phase repair can reuse the exact source-bound plan/narration when its
generation dependencies remain unchanged. It reruns factual QA, every annotation
scope, independent review and composed QA. Changing annotation policy creates a
new revision but does not regenerate valid unchanged speech. Source/context
invalidation still rejects old stage replay and all planning consumer descendants.

## Resource and failure boundaries

| Resource | Default behavior |
| --- | --- |
| Annotation request | Existing 180,000-character request and 140,000-character response limits |
| Review request | Existing 260,000-character request and 140,000-character response limits |
| Annotation scopes | At most 128 complete scenes |
| Review scopes | At most 256 source/global scopes |
| Global discourse | Every actual utterance must fit one complete reconciliation request |
| Source scope | Complete scene, supporting scenes and relevant full pages remain indivisible |

These configured character limits are resource guards, not provider token limits,
lesson-duration targets or demonstrated book capacity. A scene/source page/support
closure or full spoken discourse may remain too large. Such cases fail explicitly.
No truncation, synthetic summary, missing scene or partial annotation is published.
Review scopes can fail independently and retain uncertainty; a failed annotation
scope prevents production because full-script coverage cannot be assembled.

Global retrieval and hierarchical discourse reconciliation for arbitrarily long
spoken lessons remain implementation work. This batch establishes complete
all-speech reconciliation only while that indivisible payload fits. Production
provider token calibration, deadlines/cancellation and empirical evaluation also
remain open.

## Reproduce

```sh
python scripts/check_dir_annotation_windows.py
python examples/annotation_window_walkthrough.py --output verification/annotation_window_walkthrough.json
```

The controlled fixtures use authored UTF-8 sources and protocol responses. They
exercise registered generation, scoped annotation/review, full discourse,
phase repair, persistence, four planning consumers and invalidation. They are not
live-model quality, real PDF extraction, authenticated learner grading, rendered
media or playable game evidence. The separate canonical gate does not discover
staged DIR and neither gate establishes acceptance.

## Remaining implementation

Continue richer upstream codecs and grounded demonstration, inquiry/Socratic and
misconception-specific teaching, then scene-local generation/annotation correction
checkpoints, durable catalog/crash/lease recovery and production stage adoption.
Add hierarchical global discourse retrieval when lessons exceed the current full
spoken payload, independent real-source/provider benchmarks and calibrated live
quality evaluation. Re-audit required DIR implementation scope, then integrate
losslessly into canonical GitHub in this chat. No GitHub write occurs in batch 013.
