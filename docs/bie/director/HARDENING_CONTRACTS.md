# BIE DIR hardening batch 007

Original checkpoint: BIE-DIR-QA-007, 37/37 original entries implemented and tested.
Additive checkpoint: BIE-DIR-HARD-SEMANTIC-001. DIR section implementation-scope
completion is **not established**; BIE is **NOT ACCEPTED**. This is the current
runnable DIR subset over canonical commit
`bc3147db408fc5a5d54017c8b907f580477ff2c3`, which remains through PED.

Read `CAPABILITY_AUDIT.md` for the 37-task source audit and exact remaining work.
The recovered product vision, original roadmap and section-end GitHub integration
workflow are retained. No GitHub write or live model call occurred in this batch.

## Run the delivered source

Extract the combined ZIP into a new directory, then run with Python 3.10+ standard
library (verified on Python 3.12.14):

```bash
python3 scripts/check_dir_hardening.py --output verification/local_tests.json
python3 examples/director_benchmark.py --output verification/local_benchmark.json
python3 examples/semantic_qa_walkthrough.py --output verification/local_semantic.json
```

The current gate has 338 tests: 286 original regression tests, 49 new hardening
unit tests and 3 hardening integration tests. Every test runs; there are no skips.
Older check scripts remain as history; use `check_dir_hardening.py` for current
test accounting. The separate canonical gate passes 2,160 tests and currently
does not discover DIR; section-end canonical wiring remains required.

The benchmark runs six controlled source cases in mathematics, science and
economics twice. Lexical expectations pass; QA remains REVIEW_REQUIRED. The
semantic walkthrough makes two actual fixture-provider calls (invalid JSON,
then a valid receipt) and also ends REVIEW_REQUIRED. These examples exercise
real code with explicit fixtures; they do not measure a live model's factual
accuracy, actual textbook E2E, rendered video/audio or a playable game.

## BIE-DIR-HARD-CONTRACTS-001

This additive task corrects the original LESSON-001..010 and SCRIPT-001..010
working source under preserved original provenance. It does not replace the
original ZIPs or change original task IDs. `contract_validation.py` centralizes
strict ID/collection/numeric checks and iterative scene-DAG validation.

Lesson architecture validates objective coverage, source IDs, review flags and
scene-parent references/cycles, and detaches mutable nested ID lists. Script
plans validate all fields and ordered unique IDs. Game handoffs validate required
and optional IDs and retain the prohibition on ungrounded mechanics. Explicit
`validate_lesson_architecture`, `validate_script_plan` and `validate_game_handoff`
functions reject invalid raw/deserialized records. Raw dataclasses are still
constructible for diagnostics; code must call a producer or validator at a
runtime boundary.

The other original helpers now reject malformed records, whitespace evidence,
string-as-collection input, inappropriate booleans, nonfinite/out-of-range scores
and missing grounding. Unknown scene teaching modes fail explicitly. Pacing
requires a nonempty unique scene schedule and finite positive targets; extremely
large or rounding-to-zero targets fail. Optional misconceptions and absence of
curiosity gaps remain allowed. Uncited voiceover claims remain withheld with
review; they are not silently promoted to grounded text. Unknown nonblank
transition relations retain their old generic cue and require later review.

Thirteen before/after probes capture concrete old defects and current rejection.
Forty-six representative valid cases across all 20 modules retain exact prior
outputs/fingerprints. The controlled benchmark's outputs and QA reports also
remain unchanged. This is bounded compatibility evidence, not proof for every
possible input. Generic helper content and the old fixed HOOK/RECAP wrapper remain
as components; they are not the final adaptive teaching director.

One existing TIME boundary test had relied on constructing an invalid ScriptPlan
through the permissive old builder. It now asserts rejection by the hardened
builder and separately constructs a raw invalid dataclass to retain the original
downstream rejection check. No test was removed or skipped. The original file,
exact change and source hashes are preserved alongside the 20 original modules.

## BIE-DIR-HARD-SEMANTIC-001

`bie.director.semantic_execution.evaluate_script_semantics` consumes the existing
ScriptSnapshot, ScriptClaim, SourceCatalog and SourceBytes contracts. Its provider
implements the canonical ModelProvider `invoke(ModelRequest)` interface. The
canonical gateway interface, schema validator and GPTAdapter are copied without
changes and recorded against the pinned commit. Provider identity is explicit;
the implementation is replaceable and does not instantiate a vendor SDK.

Execution order:

1. Validate immutable current inputs, actual source bytes/extracted passages and
   deterministic factual checks. Source/claim blockers prevent model invocation.
2. For each FACT claim, include exact claim and passage fingerprints, full cited
   page context, the current utterance's narration, language and policy versions.
   Source text is data, including any embedded instructions. The critic must
   consider scope, caveats, negation, quantities, units, causality and conflict.
3. Call the provider with canonical text/structured-output capabilities and
   temperature zero. Request budgets cover the system instruction, payload and
   schema, including retry instructions. Context is never silently truncated.
4. Validate provider/model identity, completion reason, JSON structure, exact
   binding fields, supported verdict, finite confidence and nonblank rationale.
   Reject duplicate JSON keys, NaN, extra/missing fields and stale bindings.
5. Construct a SemanticReceipt from the actual response, then recompute factual
   QA. Model-authored PASS reports are not accepted as input.

The default policy allows two attempts, never more than three. It bounds request
characters (48,000) and response characters (16,000). Invalid JSON/bindings and
transport failures may retry within this limit; refused responses, identity
mismatches or oversized responses terminate the affected claim. Truncated
responses cannot produce receipts. Failure outcomes are explicit, and provider
exception text is not exposed. Retries reuse source content and only add a
validation error code; there is no unbounded repair loop or automatic narration
rewrite. The injected transport owns network deadlines/cancellation; this module
does not claim a wall-clock timeout or external provider authentication.

Each attempt records request/response fingerprints, identity, attempt number and
outcome. Response hashes cover the relevant gateway envelope fields, not opaque
transport/usage objects. Request hashes bind the complete policy, messages,
schema and identity. Malformed JSON-shaped responses retain a hash when possible;
unsupported non-JSON objects may have no response fingerprint.

The trusted evaluator allowlist is empty by default. Merely configuring a
provider does not trust it. `evaluator_key(identity, policy)` produces the explicit
key used by `FactualPolicy.trusted_evaluators`; tests use scoped fixture policies
to exercise supported/contradicted/uncertain/low-confidence paths. A production
policy needs separate provider calibration and provenance. Gateway fields are
reported identity, not an authenticated signature or proof of factual truth.

`SemanticEvaluation.status` is BLOCKED when grounding/factual QA blocks,
REVIEW_REQUIRED for unresolved execution/evaluation or upstream review, and
CHECKS_PASSED only for its scoped checks. `accepted` is always false. Non-FACT
claims receive no factual semantic receipt; existing QA retains review. Automatic
claim extraction/classification, implicit assertions, broader book context
selection, coherence/audience annotation producers and semantic calibration
remain implementation/evaluation obligations.

## Preservation, packaging and dependency rules

The combined bundle is the recommended runnable deliverable. It contains all 37
original atomic archives byte-for-byte in `original_archives/` and two additive
archives in `hardening_archives/`. Apply corrected working source after originals;
never extract old originals over the final working tree. Atomic packages declare
their owned files, canonical dependencies and task dependencies. Fresh closure
tests use only those declared inputs. Cross-task examples/integration tests and
the adjusted TIME test are part of the combined bundle with explicit provenance.

`verification/preservation.json` lists every intentional prior source/test change,
unchanged prior files, new files, original archive hashes and unchanged canonical
dependencies. `verification/before_hardening/` preserves the exact 20 original
source files and the original TIME test. Earlier batch ZIPs and historical source
remain retained in the continuation pack. `MANIFEST.json` hashes every other ZIP
member; ZIP CRC, atomic dependency extraction and fresh combined execution are
checked. Packaging scripts are reproducibility tools, not product entrypoints.

Older QA/TIME/SYNC documents describe their original component contracts. This
document and the capability audit supersede historical statements that the
documented original boundary defects or factual-provider invocation remain
unfixed. Their other production/acceptance limits remain applicable.

## Next checkpoint

Implement actual canonical artifact-to-DIR execution and substantive grounded
directing/narration, followed by narration-bound annotations and integrated
semantic/coherence/audience QA, bounded repair and typed consumer handoffs.
Exercise real-source independent benchmarks and re-audit DIR scope. GitHub
canonical integration stays in this chat after required section hardening and
re-audit. No original task needs restarting. The original 867-entry baseline is
unchanged; these two hardening IDs are additive and not a completion percentage.
