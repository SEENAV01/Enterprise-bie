# DIR original batch 006 — QA-006 and QA-007

These are the last two original DIR roadmap entries (page 10 of the original
18-section registry). Their APIs are implementation decisions under the recovered
scope, not signatures claimed to have existed in the old chats.

The original vision remains the authority: source intelligence and reasoning →
pedagogy → autonomous directors → structured video AND game outputs → actual
execution/QA/repair. This batch completes the original 37-entry implementation
sequence. **DIR section implementation-scope completion is still blocked by its
capability audit and required hardening. No GitHub integration or acceptance is
claimed.** Read SECTION_EXIT_REVIEW.md for concrete open implementation work.

## Run

Python 3.10+ standard library; verified on Python 3.12.14.

```sh
python3 scripts/check_dir_qa.py --output verification/local_dir_tests.json
python3 examples/director_benchmark.py --output verification/local_benchmark.json
```

The combined bundle is directly runnable and preserves all 37 original atomic
ZIPs, prior source/tests, canonical dependencies and evidence. Atomic archives own
only their listed files; DEPENDENCIES.json gives the exact closure to run them.
The canonical gate remains separate until DIR integration adds test discovery.

## QA-006: actual timing consumers

`pacing_qa(snapshot, speech, pauses, emphasis, timeline, beats=(), policy=...)`
uses original SCRIPT, TIME and QA contracts. `validate_timing` reconstructs the
existing TIME-004 output and checks the exact realized script, voice, source,
order, word intervals, pause plan, emphasis and soft targets. A hash label alone
is insufficient. Invalid/stale data raises ValueError; validly formed content
with problems produces scoped findings.

PacingBeat binds an exact QA TextSpan to a teaching mode, concepts, evidence and
objectives. Its optional minimum_reflection_ms is an explicit timing requirement.
The check measures contiguous silence immediately after the beat; silence at the
start or elsewhere cannot satisfy it. Shared clip edges count once. Scene cuts
and utterance boundaries are not implicit reflection breaks. An unmet declared
minimum blocks and routes to TIME or, for reported recordings, AUDIO.

Policy-derived retrieval/reasoning reflection targets are review heuristics.
Active WPM excludes silence and includes realized emphasis; a rolling word window
finds fast bursts hidden by slower words. Checks also cover abrupt rate changes,
reasoning pace, declared concept density, continuous narration across scenes,
unexplained silence, unmet recorded pause requests and soft scene targets.

Policies are configurable, versioned engineering thresholds, not measured age,
cognitive load or comprehension limits. There is no maximum lesson duration,
forced truncation, mandatory learner profile or automatic rewrite. Long content
can require a processing-break review while retaining every source-bound word.

Pacing reports retain upstream review and estimated/reported-audio uncertainty.
No supplied alignment becomes verified audio. `validate_pacing_report` recomputes
the report; repaired timing invalidates the prior report and SYNC context while
preserving the script. Missing mode annotations remain an explicit review.

## QA-007: executable benchmark contract

`run_director_benchmark(suite, candidate, artifacts, identity, repetitions=2)`
executes a candidate against pinned source bytes and original canonical PED
objects. DirectorRequest contains SourceCatalog, UnifiedPedagogyPlan and
LearningObjective records. The runner reconstructs PED lineage, validates source
and objective references, hashes actual source bytes and rejects missing domains,
duplicate cases, conflicting revisions and missing independently held expectations.

The candidate receives only the request, and returns DirectorExecution containing
actual lesson/script, realized narration, game handoff, timing and annotations.
It receives no oracle/expected results. The runner executes all six actual QA
modules itself and inspects narration text independently of candidate claim labels.
A candidate cannot submit a score or precomputed PASS instead of these outputs.

NarrativeExpectation performs exact case/whitespace-normalized, word-boundary
PRESENT/ABSENT/ORDER checks grounded to source references. It preserves punctuation,
operators and negation. This finite lexical oracle is deliberately limited:
valid paraphrases can fail and unlisted semantic errors can escape. The supplied
fixtures have engineering-authored expectations; they are not independent
educator-validated golden textbooks or a semantic judge. The in-process API is
an accidental-leakage boundary, not isolation from malicious candidate code.

The runner checks PED objective/lesson/source bindings, upstream review
propagation and the same learning-model/evidence coverage in the game handoff.
Unexpected blockers fail a case. Explicit expected negative findings can pass a
regression expectation while qa_status remains BLOCKED. Missing checks, execution
exceptions and invalid contracts stay in the denominator. Any case failure fails
the benchmark checks regardless of an aggregate average. Per-domain counts are
reported. Repeated output changes also fail exact deterministic replay.

The report retains each actual output, its fingerprint, exact request, dataset,
policies, source-byte receipts, candidate/config identity, six QA reports and
failed checks. The example computes a digest from its executing source files;
the generic identity contract is declared provenance, not remote attestation.
Reproducibility for stochastic model output needs a separately governed policy.

## What actually executed

`benchmarks/director_controlled_v1.json` contains six short authored source cases,
two each in mathematics, science and economics. Expected facts/order are written
in that dataset separately from the candidate implementation. Each is executed
twice. The reference adapter consumes actual canonical PED decisions/objectives,
respects their dependency order, invokes original lesson/script/voiceover/game
builders and current timing/QA modules. Its narration copies selected source
passages. It is a controlled integration reference, not the missing full
source-to-teaching intelligence implementation. It reads no oracle or fixture.

The checks pass, with QA still REVIEW_REQUIRED. Factual contextual interpretation,
semantic annotation production and audience calibration remain unresolved; no
trusted semantic receipt is fabricated to turn these cases green. No PDF pipeline,
actual audio, rendered video, playable game or external model was executed.

Tests also deliberately corrupt source facts while retaining citation labels,
reverse teaching order, lose game concepts, omit required pauses, submit forged
scores, alter timings, drop PED review, change replay outputs and raise exceptions.
The benchmark must expose those failures. Tests distinguish planned pauses from
immutable recorded audio and verify exact timing/SYNC invalidation after repairs.

## Dependencies and ownership

| Task | Direct task dependencies | Canonical dependencies |
| --- | --- | --- |
| QA-006 | QA-001, TIME-004 | Through declared TIME closure |
| QA-007 | QA-001…006, LESSON-001, SCRIPT-010 | PED objective generator, unified plan, provenance and initializer |

QA-006 owns pacing_qa.py, its unit tests and pacing fixtures. QA-007 owns
director_benchmark.py, its unit tests, controlled example and pinned dataset.
The combined-only boundary tests additionally use unchanged SYNC-001. Existing
source, atomic ZIPs and contracts remain preserved; this document supersedes
only the previous documents' current-checkpoint descriptions.

Read the recovered design review before hardening. Next is the DIR capability
audit and source-preserving corrections, then re-audit and section-end canonical
GitHub integration in this chat. Do not declare the section complete from 37/37
or from the test count. IMPLEMENTED/UNIT_TESTED is not ACCEPTED.
