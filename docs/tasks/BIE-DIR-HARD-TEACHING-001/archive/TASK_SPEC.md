# BIE DIR batch 011: grounded context and explicit teaching

Original checkpoint: **BIE-DIR-QA-007 (37/37)**. Additive checkpoint:
**BIE-DIR-HARD-TEACHING-001**. DIR implementation scope remains incomplete;
the product is **NOT ACCEPTED**. This extends the recovered BIE design and the
same registered DIR stage. Video and playable revision games remain equally mandatory.

| Additive task | Supported execution |
| --- | --- |
| BIE-DIR-HARD-CONTEXT-001 | Source-bound concept definitions/conditions, prerequisite edges, supplied algebraic steps and optional reported assessment events, using existing canonical KI/PR/MATH/PED functions; explicit existing PED bridge selection |
| BIE-DIR-HARD-TEACHING-001 | Required bridge and derivation coverage/order in actual model planning and spoken narration; typed persistence/revalidation, annotation/repair and current consumer compatibility |

## Upstream contract

The optional `pedagogy.teaching_context` artifact has envelope version `1.0.0`
and payload schema `bie.dir.teaching_context/1.0.0`. It is a parent of the existing
`pedagogy.plan`; the DIRECTOR stage still receives exactly the original RE/PED
references. Source, context and scored-event ancestry use the existing CAS,
envelopes, provenance, run IDs and reference validation.

```python
from bie.director.teaching_context import publish_teaching_context
from bie.director.director_inputs import publish_pedagogy

context_ref = publish_teaching_context(
    io, run_id, source_catalog_ref,
    concepts, prerequisite_edges, source_derivations, reported_assessment_refs,
)
ped_ref = publish_pedagogy(
    io, run_id, source_catalog_ref, reasoning_ref,
    actual_ped_plan, actual_objectives, actual_teaching_bindings,
    teaching_context_ref=context_ref,
)
```

These inputs are supplied structured upstream records, not a new extraction or
grading system. See `tests/director/context_fixtures.py` for complete executable
examples using the actual canonical builders. A production BI/KI/PR/MATH/PED
assembly must provide the corresponding verified artifacts.

| Record | Binding and behavior |
| --- | --- |
| `KnowledgeConcept` | Stable concept ID, label and one or more exact `SourceExcerpt` definitions; optional exact applicability conditions |
| `SourceExcerpt` | Evidence ID and character offsets **relative to that SourcePassage's quote**, with exact matching quoted text |
| `GroundedPrerequisite` | Original PR `Edge`, with source evidence IDs; no dangling, self, duplicate or cyclic edges |
| `GroundedDerivation` | Stable derivation/RE/concept IDs, actual canonical `DerivationStep` records and bounded variable names |
| Reported assessment | Actual typed `evidence.pedagogy_assessment` event; schema, source ref/parent, one opaque learner key, concept/item IDs, response text, reported score/reliability/age and score origin |

The adapter calls original knowledge graph construction/validation, definition and
condition attachment, PR graph/order, derivation chain/probe/teaching-step tools,
uncertainty-aware mastery, bridge planning and bridge scope functions. Loading
recomputes these results and rejects edited outputs or removed review flags.
Exact quote-binding confidence does not certify the concept interpretation or
the semantic truth of a prerequisite edge. Context always retains review.

Assessment events are optional. No observations means the original unknown
mastery interval [0, 1], confidence zero and review. Supplied observations retain
actual event IDs as evidence; book text never pretends a learner answered. The
codec rejects mixed learners, unknown concepts, missing response/origin and invalid
numeric values. It does not authenticate identity, execute grading or calibrate
reported scores. Conflicting scores retain the original uncertainty report.
Even high reported mastery does **not** waive a prerequisite or its assessment.

## Prerequisite bridge selection

DIR computes the selected lesson's actual PED decision and PR concept dependency
closure. An out-of-lesson prerequisite must have an explicit, unambiguous existing
PED binding/objective/assessment. The adapter selects those original records and
projects their binding lesson ID into the current teaching scope. The full PED
plan and all original decision/objective/item IDs remain unchanged; explicit
bridge IDs record why the earlier content is included. Missing or ambiguous
bridges fail instead of inventing curriculum or assuming mastery.

The original bridge planner contributes remediation goals and reported urgency.
The original PR topological order controls teaching precedence. A prerequisite
decision must finish before the dependent decision starts. Dependencies within
one multi-concept decision still need broader semantic teaching review.

Each selected bridge has a host-owned teaching obligation. Its scene must bind
the exact decision, objective and evidence, declare EXPLAIN, retain the original
assessment and realize an actual EXPLAIN spoken span naming the prerequisite.
This structural guard alone does not prove a substantive or effective explanation;
the existing factual, annotation, discourse and separate review phases still run.

## Supplied mathematical derivations

The corresponding existing RE decision must have type `mathematical_derivation`,
the same concept as subject and the exact structured selected option returned by
`context_bridges.derivation_decision_value(derivation)`. Its PED binding must select
DERIVATION. Every before/after expression, rule and justification must occur in
the cited source passage. No new mathematical solution is synthesized here.

The numerical probe adapter accepts a deliberately bounded arithmetic AST: no
calls, attributes, containers, unbound variables or compound power bases; at most
eight named variables, 256 expression characters and 128 AST nodes. Powers have
literal integer exponents 0..12; constants and probe outputs must be finite and
bounded as documented in code. Unsupported forms require another math adapter.
Resource limits fail explicitly; educational content is never silently truncated.

The original finite probes can disprove a candidate at sampled points but cannot
establish symbolic equivalence. A regression deliberately supplies a polynomial
that collides at all four sample points and verifies **NOT_PROVEN_REVIEW_REQUIRED**.
Domain-wide proof, richer notation/units, constraints and all mathematics are not
claimed. These are required future codec/tool integration and evaluation work.

Host-owned step obligations preserve source order. Each step must appear once in
the plan, use DERIVE and receive a separate actual DERIVE beat with exact evidence,
objectives and a matching text-span realization. Source expression checks respect
symbol case and identifier boundaries. Omission, reassignment, changed symbols,
reordering or merging all steps into one paragraph fails. Multiple steps may share
a scene when separate ordered beats remain. Prompts require natural explanations
of the supplied reasons and conditions; semantic review is still required.

## Model, persistence and downstream behavior

The model receives selected grounded graph nodes, conditions, prerequisite order,
math reports, reported mastery, bridge plan and teaching obligations, with complete
cited pages and actual RE/PED records. Context-free inputs keep their original
serialization and schemas. Context-aware scenes add `teaching_obligation_ids`;
narrated scenes add exact `teaching_realizations`. Only compiled-in frozen record
variants decode from persistence; JSON cannot select an arbitrary Python class.

`verify_base` reruns the actual input, plan, narration and compilation validators.
The existing annotation producer gets the context and selected concept IDs.
Original whole-utterance factual coverage remains, including assessment questions,
answers and criteria. No model-supplied quality verdict can replace those phases.

The unchanged batch 010 executor/revision/consumer implementations handle the new
artifact through ancestry. Exact context retains phase repair eligibility. Changed
context or scored-event evidence changes the input fingerprint and regenerates.
Explicit invalidation of a context/event ancestor rejects stale replay and all
descendant timing/sync/game-handoff planning candidates. Production upstream owners
must still call the invalidation API when replacing artifacts.

Consumers remain review-only planning entry points, not rendered media or playable
games. Scene-local repair, annotation caching, catalog/crash/lease recovery, full
downstream stage adoption and end-to-end product execution remain open.

## Verification and continuation

Run `python scripts/check_dir_context.py` and
`python examples/contextual_director_walkthrough.py`. The 53 new tests cover
context validation, teaching realization and registered-stage repair/consumers.
The preserved earlier 462 tests run alongside them. The three controlled cases
are science with a prerequisite bridge, economics with conflicting reported
mastery and a bridge, and a two-step supplied algebraic chain. They execute
generation, annotation failure/recovery, factual/reviewer phases, four original
consumers each and rejection after context invalidation. No live model, real PDF
pipeline, authenticated scoring, media render or playable runtime runs here.

Continue long-context segmentation and remaining rich codecs/teaching modes,
scene-local correction/catalog recovery/full stage adoption, independent real-source
and provider evaluation, then DIR re-audit and section-end canonical integration
in this chat. Preserve all original archives, task ledger and richer prior work.
No mandatory questionnaire, arbitrary lesson-duration cap, universal scene template
or raw Book-to-LLM-to-Remotion shortcut is introduced.
