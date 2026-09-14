# BIE-DIR-QA-003 — coherence

Owned source: bie/director/script_coherence_qa.py

Direct task dependencies: BIE-DIR-QA-001, BIE-DIR-LESSON-001, BIE-DIR-LESSON-005.

# BIE DIR original batch 005 — QA-001…005

Original roadmap scope, page 10: factual script QA, source grounding, coherence,
repetition detection, age/level appropriateness. This document specifies **new
implementation choices** under those original titles. The recovered master PDF
supplies IDs, titles and order; it does not supply these APIs or this dependency DAG.

The vision and section-end GitHub workflow are unchanged. These five tasks are
implemented and unit/contract tested, **NOT ACCEPTED**. After them, QA-006 pacing
QA and QA-007 director benchmark remain, followed by the mandatory DIR enterprise
completeness audit, concrete hardening, re-audit and canonical GitHub integration
in this chat. Do not integrate this incomplete section early.

## Run the delivered source

Use Python 3.10+ standard library; verification ran on Python 3.12.14.

```sh
python3 scripts/check_dir_qa.py --output verification/local_qa_tests.json
python3 examples/qa_walkthrough.py
```

The combined bundle includes all 35 original DIR atomic ZIPs, every prior DIR,
TIME and SYNC source/test file, required unchanged canonical dependencies and
verification evidence. Atomic ZIPs own only their task files; use their
DEPENDENCIES.json closure or extract the combined bundle to run immediately.

Use check_dir_qa.py for the current count. Prior check_dir_timing.py,
check_dir_sync.py and their contract documents remain historical; their category
labels predate QA and must not be used as current QA accounting. Canonical
scripts/test_enterprise.py still excludes tests/director until section integration;
the canonical 2,160-test gate is separate from the current DIR gate.

## Shared revision and report contract

`snapshot_script` consumes the original ScriptPlan, original VoiceoverDraft tuple,
explicit segment order and language. It calls the existing TIME-001 adapter and
retains the exact realized SpeechUtterance values. It never reads text_intent as
spoken narration, infers order from sorted IDs or needs a learner profile.

`TextSpan` binds utterance ID, exact character interval and utterance fingerprint.
Partial spoken words, invalid types, mutable input records, stale edits and unknown
references are rejected. `ScriptClaim` adds an ID, FACT/QUESTION/INSTRUCTION/OTHER
annotation and evidence IDs. Whole-word **union** coverage prevents overlapping
claims from inflating the coverage total. Non-factual labels still need review for
implicit assertions. Declaring the entire narration an instruction cannot pass
factual QA.

SourceCatalog retains SourcePage records with source ID, actual-byte digest,
one-based page number, extracted text and extractor version. SourcePassage has
exact page fingerprint, region identifier, character interval and quote. Page
and quote consistency is required; source and extraction revisions are distinct.

Each QAReport contains task ID, snapshot fingerprint, complete input fingerprint,
policy version, findings, numeric measurements, scope and limitations. Findings
carry severity, subject, relevant span/citations and repair stage. Status is
BLOCKED for any blocker, REVIEW_REQUIRED for unresolved review, otherwise
CHECKS_PASSED **within the stated scope**. `accepted` is always false. Upstream
script review and withheld-claim flags propagate. Each public validate_*_report
function recomputes the report from its inputs and rejects changes to findings,
policy, source, annotations or inspected script.

Invalid or stale contracts raise ValueError before emitting a report. Validly
formed but deficient content emits explicit findings. Callers must preserve both
failure channels. No automatic mapping turns these five reports into full
director_quality, semantic_correctness or enterprise release PASS.

## QA-001 — factual script QA

`factual_qa(snapshot, claims, catalog, receipts=(), policy=FactualPolicy())`
checks declared claim coverage, resolvable references and script lineage. Exact
case/whitespace-normalized equality records source fidelity, not contextual truth.
Otherwise identical numeric wording with changed values emits a blocker. General
keyword overlap cannot establish support; paraphrases and exact quotations both
need contextual assessment.

An optional provider-neutral SemanticReceipt binds exact claim and every cited
passage fingerprint, verdict, evaluator/version, confidence and rationale. Only
SUPPORTED receipts meeting an explicitly supplied evaluator@version allowlist
and confidence policy satisfy the reported semantic check. Empty default allowlist
trusts nobody. Any supplied contradiction blocks; uncertain, unlisted or weak
receipts require review. A support receipt never erases deterministic numeric
conflicts or missing coverage. Multiple citation contexts with conflicting numeric
versions require reconciliation.

Receipts are caller-supplied reports, not authenticated signatures, live model
calls, independent fact-checks or empirical guarantees. This batch implements no
new model provider and imposes no mandatory human review loop. Upstream KI/RE and
replaceable evaluation providers can supply governed receipts later. World truth,
mathematical correctness and source-context reliability remain separate evidence.

## QA-002 — source grounding

`source_grounding_qa(snapshot, claims, catalog, artifacts=())` takes SourceBytes
with actual immutable bytes and hashes them locally. Missing/wrong source bytes,
unresolved citations, citations outside draft lineage, unassigned draft references
and incomplete narration span coverage are explicit. Byte receipts (ID, MIME,
digest, length) enter the report fingerprint; raw bytes are not copied into it.

The `text/plain; charset=utf-8` adapter requires exact full-text equality to one
extracted page. Other media, including PDFs, retain EXTRACTION_ACCURACY_UNVERIFIED:
matching bytes does not certify extraction text, OCR, page numbering or region
meaning. Malformed/stale page/quote records fail validation. Supplying a correct
citation for an incorrect fact can pass this structural grounding scope and still
block QA-001; that boundary has an explicit cross-contract test.

## QA-003 — coherence

`coherence_qa(snapshot, architecture, beats, transitions=(), initial_concepts=())`
consumes the original LessonArchitecture and actual narrative order. It detects
missing/unplanned scenes, lesson or evidence/objective mismatch, uncovered declared
objectives, unknown/cyclic parents and children narrated before prerequisites.
The legacy LESSON-001 cycle defect is detected at the QA boundary; its original
implementation remains unchanged until section hardening.

Revision-bound DiscourseBeat annotations track concept introduction/requirements,
prior utterance references and open/answered questions. Missing annotations,
forward references and unresolved questions remain explicit. Optional initial
concepts are source/curriculum context, not a mandatory learner model. Original
Transition records bind to exact narrated cue spans entering the next scene;
unannotated, generic or unrealized transitions cannot silently pass their check.
This is structural coherence over supplied annotations, not automatic discourse
understanding or demonstrated learner comprehension.

## QA-004 — repetition detection

`repetition_qa(snapshot, purposes=(), policy=RepetitionPolicy())` examines exact
and near sentence pairs, including within an utterance, using deterministic token
sequences and SequenceMatcher. Minimum words and similarity threshold are
versioned engineering heuristics. Decimal values, negations, signs, common currency
symbols and operators are preserved. Detected changes require factual/context
review. Purposeful near copies retain a semantic-review flag for changed wording
or units; similarity does not prove equivalence.

RepeatPurpose binds two ordered complete sentence spans with shared objective and
evidence lineage and explicit rationale: RECAP, RETRIEVAL, MISCONCEPTION_RECHECK or
PRACTICE. Recap can retain identical exposition. Active retrieval questions may
repeat intentionally; merely relabelling repeated exposition as retrieval is
insufficient. Optional original PED RepetitionDecision is checked for mode conflict;
its interval_units are preserved but this module does not evaluate actual session
spacing or learner outcomes. No learner mastery/profile is required.

Non-English lexical similarity, abbreviations, sentence boundaries and semantic
duplicates need further evaluation. Detection is not exhaustive. No content is
deleted, rewritten or duration-capped by this module.

## QA-005 — age/level appropriateness

`age_level_qa(snapshot, target=None, terms=(), advisories=(), assessments=(),
policy=AudiencePolicy())` accepts an optional curriculum AudienceTarget, not a
mandatory personal learner profile. Missing target produces an explicit unresolved
audience review while source-driven generation can continue.

AudienceTarget declares an age interval, curriculum level rank, allowed cognitive
operations and curriculum basis. TermRequirement identifies an actual narrated
term, source evidence and optional exact definition span. Advanced terms need a
declared scaffold at/before first use. The supplied definition's semantic quality
remains a pedagogy check. A sentence-length threshold suggests review, never an
inferred school grade, scientifically calibrated age or content truncation.

ContentAdvisory binds a current narration span, category, policy minimum age and
rationale. Check against the youngest intended audience, not only the oldest.
These thresholds are supplied curriculum policy, not legal limits or automatic
moderation. Completeness of term/content annotation is caller-reported and false
by default. Unknown-language handling remains reviewable.

Original AssessmentPrompt objective/evidence lineage and cognitive operations are
checked against explicit target policy. Children are not automatically barred
from ANALYZE/EVALUATE/CREATE. No demographic inference or learner questionnaire is
introduced.

## Evidence and remaining section work

Tests include positive scoped results, negative content, revision/type validation,
coverage gaps, source-byte tampering, receipt conflicts, legacy parent cycles,
purposeful retrieval and a canonical release evaluator that remains blocked when
only partial QA evidence exists. The walkthrough uses controlled UTF-8 text and
actual DIR/TIME/SYNC contracts; it is not a real textbook run, generated audio,
rendered video, game/simulation runtime or empirical director benchmark.

Original rich code, prior ZIP evidence, canonical repository bytes, versioned
provenance, source-driven duration, structured directors/IR/compiler/runtime QA,
equally required playable games and cumulative PDF learning remain in scope.
QA-006/007 and section hardening must address concrete findings without inventing
replacement roadmap IDs. Three previously known legacy source defects and
canonical DIR discovery/provenance wiring remain open. IMPLEMENTED/UNIT_TESTED
does not mean INTEGRATED or ACCEPTED.
