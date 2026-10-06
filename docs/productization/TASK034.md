# BIE-PROD-034 — Governed current Director → Visual producer

This is the explicitly assigned productization continuation after canonical
Task033. The exact base is `66047150b5037e5ff19c6411ec84125e4cc44b86`, tree
`f580d3b42c1522b7458b118b6f42f940147b5d2c`. Task033 canonical closure includes
Post-DIR run `37480660660` and Section18 run `37480660802`, whose unchanged
candidate passed attempt 2. The first browser/CDP failure remains evidence;
its precise cause was not proved by the successful reexecution.

## Current and historical handoff contracts

The current Task033 output is the persisted native `director.plan` envelope
version `1.0.0`, with payload `bie.dir.annotated_plan/1.0.0`.
`DirectorConsumers._director` validates its actual retained production
execution, exact Reasoning/Pedagogy inputs, source bytes, revisions and review
boundary. Current consumer candidates are read through `read_current`.

The older Visual `canonical_dir_codec.py` expects a different DIR handoff
packet containing `visual_intents`, `timing_cues`, `narration_revision`, source
identity and evidence/reasoning refs. It pins commit
`73840d86a78e5f31438e2a1bad34f3b2a8433eb9` and tree
`adf64727adaf2ec9dd92c8f1ea03e2df2b8d738c`. Current Task033 bytes are never
relabelled as that packet and the pinned identities are unchanged.

Current `DirectorConsumers.visual` can validate current Director output and
produce `director.visual_sync_candidate`, but callers must supply canonical
typed `VisualIntent` inputs. The historical test helper `intents(execution)`
does not establish production intent discovery. Task034 derives those inputs
from current verified source semantics and exact narration/teaching evidence.

`rep_original_codec.py` also requires exact original REP archive provenance.
Its `EXPECTED_REP_ARCHIVE_SHA256` constants and archive verification gate remain
unchanged. Current execution through native REP modules records current
implementation/policy/code identities separately from historical archive
implementation provenance. It does not claim to have reconstructed a current
decision by executing a historical ZIP. `actual_visual_e2e` and
`vis_section_gate` retain their original historical meaning.

## Profile and stage boundary

The new immutable profile is
`source_grounded_di_knowledge_pr_math_reasoning_pedagogy_director_visual_v1`:

SOURCE → DOCUMENT_INTELLIGENCE → KNOWLEDGE → PREREQUISITE → MATH → REASONING
→ PEDAGOGY → DIRECTOR → VISUAL.

It contains exactly nine global stages. Historical Task029/030/031/032/033
profiles retain exactly 3/5/6/7/8 stages. Task030 preserves
`math_evidence_required`; Task033 preserves
`director_math_teaching_contract_required` when explicit native derivation
teaching obligations are unavailable. Task028 and Android remain unchanged.

The existing global graph already defines VISUAL after DIRECTOR and REASONING,
consuming `director.plan` and `reasoning.decision_set` and emitting
`visual.plan`. Task034 composes this boundary without editing that graph.

## Bounded authoritative intent production

This initial current producer supports strict bounded source declarations for
data/chart relations, explicit chronology/timelines and cellular structure.
The declarations must occur in real extracted document blocks and match the
actual current Director narration spans. The declaration parser supplies
bounded typed semantic values; it cannot turn a keyword, page order or an
uncited narration sentence into a visual obligation.

Every supported intent binds the exact current Director revision, scene,
utterance/span, objective and concept IDs, evidence IDs, reasoning IDs,
purpose and visual target. Native `NarrationAnchor`, `IntentBinding`,
`VisualIntent` and `sync_visual_intents` validate those bindings before the
current `DirectorConsumers.visual` call publishes a real preview candidate.
The candidate retains `PLANNING_PREVIEW_ONLY`, `requires_review=true`,
`accepted=false` and `release_ready=false`.

Unmatched instructional material produces an explicit abstention/review finding.
Arbitrary prose understanding, automatic book-wide visual discovery and
general semantic extraction are not established by this bounded parser. Pure
equation representation has native REP support, but the current canonical
family registry has no standalone equation grammar. Such material abstains or
blocks at the current bridge instead of inventing a grammar or substituting a
generic diagram. Unsupported Math remains blocked before Director/Visual.

The supported source declaration families are technical composition evidence.
Their presence in a generated/native PDF is not expert academic validation.
Hosted Director protocol providers remain explicitly `SYNTHETIC_TEST`.
Production keeps the configured provider-neutral Director contract and an
explicit externally supplied Visual TargetProfile.

## Native Visual composition and QA

The native internal sequence is DIR_ADOPT → REP → GRAM → LAYOUT → ASSET → TEXT
→ ACCESS → QA. A complete successful prefix through QA is required for global
VISUAL success. The current bridge uses provenance-neutral native
`DirectorHandoff`/`DirectorContext` adoption; it does not invoke the old pinned
DIR decoder on current output.

Native representation candidate/fitness/specialist engines determine the
representation. Native grammar arbitration, registry and family wiring select
and execute the actual domain grammar. The native layout solver, safe areas,
subtitle/collision controls, asset-need/rights decisions, on-screen text,
contrast/readability/color-independent encoding and alt-description policies
remain canonical components.

The bounded technical complexity estimate is the number of independently
retained source items divided by the declared maximum element bound. That
actual estimate is passed to native REP008 dimension/composition and must also
fit the explicit target's `max_complexity` before planning proceeds. This is a
technical budget policy, not empirically optimal cognitive load or an invented
device capability. Native REP code is unchanged.

Relevant native semantic constraints and semantic/layout/clutter/asset QA must
execute against the grounded source obligation before publication. A provider
or a self-consistent visual payload cannot certify its own correctness.
Unsupported CRS, graph axis semantics, simulation model evidence, equation
morph mapping, target capabilities, grammar ambiguity, layout, text,
accessibility, rights or semantic findings remain explicit blockers/review.
No internet asset is fetched. Procedural primitives are planned; unresolved
external requirements remain governed asset requests.

The global output is the native `VisualPlan` contract as `visual.plan`, with
schema/policy semver, exact source/current Director/target identity, internal
stage refs and computed plan fingerprint. Its review boundary remains
`review_required=true` and `accepted=false`. A successful planning component
does not establish rendered imagery, animation, visual quality acceptance or
product acceptance.

## Durability, currentness and safe projection

The existing canonical CAS, pipeline SQLitePersistence, durable queue,
idempotency, EnterpriseOrchestrator and fencing/recovery remain authoritative.
The native Director index/revision/recovery machinery remains stage-internal
in the same governed run namespace and uses the same CAS. Exact current
consumer envelope IDs and bytes are bridged into the outer artifact index.
Visual intermediates are private same-run artifacts, not a second run store.

Intent binds exact Director/Reasoning artifacts, upstream lineage, derivation
policy, TargetProfile, native Visual policy/code identity and revision. Replay
must preserve the committed visual identity. Different target or Director
intent conflicts or requires a governed revision. Status/recovery revalidates
Director currentness, sync candidate, immutable ancestry, internal refs and
plan fingerprint before success or ACK. Superseded Director output cannot feed
active downstream work. Interrupted attempts are retained; no distributed
cross-store atomicity or uncontrolled redrive is claimed.

Final Visual publication holds the existing native
`DirectorRevisionStore.guard` for the verified current Director envelope.
The guard covers only the short same-run CAS/index publication boundary; model
providers and native Visual algorithms do not execute inside it. This retains
native Director revision authority while the outer persistence remains the
pipeline authority. Safe Visual receipts require an exact field set, exact
run/stage/schema identity and actual intent/abstention/internal-stage counts.
The receipt's positive fencing epoch must not exceed the persisted lease epoch,
and the saved lease must bind the same governed intent fingerprint. An ACK
recovery lease may legitimately advance beyond the committed receipt epoch;
a future or foreign-intent receipt remains rejected. Review/acceptance, technical evidence and
historical-runtime non-claims are independently revalidated. Recomputed valid
CAS bytes cannot turn an extra private-text field or a forged acceptance flag
into safe output.

Task034-only control-plane operations scope redundant pure source-code hashing
with a `ContextVar`. Repeated code identity requests inside that single
operation reuse an immutable-by-copy dictionary; a fresh operation and direct
service calls outside that scope rehash independently. Scope tokens reset in `finally`, including
errors. Before terminal ACK validation (also when recovery invokes that hook),
the complete code identity is freshly rehashed, then the inherited full status
validation executes. CAS, configuration, source bytes, run state, Director
currentness, lineage and QA results are never cached by this optimization.
It changes neither production resource limits nor historical profile behavior.

Section18 remains the authenticated governed control plane through its existing
delegation pattern. Safe projections expose bounded counts, stage/review state,
target and artifact identities/hashes. Source text, equations, narration,
prompts, raw model responses, credentials, paths and tracebacks remain private.

## Animation and Audio boundary

Animation compatibility uses the actual native
`vis_ani_adoption.adopt_visual_handoff` on the current native
`DownstreamVisualHandoff`, with the exact VisualPlan fingerprint and revision.
Current Director/narration revision, timing bounds and source/reasoning refs
are verified independently before admission. The native validator does not
itself accept a `director.plan` envelope, so no nonexistent artifact-pair loader
is claimed. Compatibility validation does not construct Animation tracks or
execute the global ANIMATION stage.

ANIMATION, SCENE_IR, VIDEO_CODE, compile/render and GAME stages remain NOT_RUN.
AUDIO graph reconciliation remains OPEN. Textual narration/timing is not final
recorded/TTS audio, and `AUDIO_REPLAN_REQUIRED` is not silently cleared.

## Validation and acceptance

`tools/run_task034_tests.py` inherits every unique selected Task033 authored and
affected module, adds native Visual/Visual QA and Animation adoption/currentness
contracts, and selects the new Task034 modules once. Safe receipts contain
counts and failed method names, not raw private errors. Baseline comparison and
repeated diagnostic executions are excluded from authored/targeted totals.

`BIE Visual Producer` is credential-free on Ubuntu 24.04 and retains existing
approved dependency profiles. It requires legacy smokes, the new actual
nine-stage multiple-domain child-process journey, second-process identity
reopening, fail-closed controls, safe leakage and canonical source preservation.
Only safe JSON receipts from the dedicated runner temporary directory are
uploaded. Full governed Linux PR preservation remains required before merge.

The final new Task034 Windows lane passed 111 unique controls: 94 producer and
17 recovery tests, with zero failures/errors/skips. An earlier 111-test run
found one real new-adapter defect: recomputed CAS receipt bytes could claim a
future fencing epoch. The adapter now checks persisted lease intent/epoch as
described above; the entire post-fix 111-test lane passed. Diagnostic repeats
are excluded from that count. Hosted Linux status remains PENDING until the
exact committed feature SHA is observed; no unexecuted gate is reported as
passing.
The selected inherited Windows lane executed 4,163 unique tests across 424
files, with 105 failures, 69 errors and zero skips. Combined with the 111 new
tests, the current targeted total is 4,274 distinct test executions, not a
full-green result. All 659 selected earlier productization tests, all 694
native Visual tests (83 files), and all 17 Animation handoff/replay tests
passed. Section16 QA/trust/adapter/repair failures remain separate recorded
evidence. In particular, the seven Visual QA integration files reported 24
failures and 12 errors within the above inherited totals. Native algorithms
or tests were not changed to erase those failures; a universal cause or fresh
base reproduction for every failure is not claimed.

An earlier diagnostic new lane passed the 50 producer controls loaded at that
time and all 17 recovery controls with zero failures/errors/skips. That 67-test
diagnostic is not the final authored test total and is not added to a later
validation count. Initial standalone Task034 child smokes retained
`child_supervision_incomplete`, including a state with eight ACKED predecessors
and VISUAL READY. An earlier code-scope diagnostic, before the final receipt
epoch fix, passed quantitative, chronology, cellular and unsupported-Math
journeys, with restart/replay/queue identities verified. That diagnostic is not
misrepresented as the final code's complete process gate.

The final-code Windows quantitative smoke hit the unchanged 45-second
supervision limit twice: 45.060 seconds with all nine stages SUCCEEDED and
eight ACKED messages, then 45.025 seconds with all nine SUCCEEDED and nine
ACKED messages. Both lacked the child's final output and complete second-process
proof. The remaining journeys, which the fail-fast smoke had not reached,
were executed separately through the exact unchanged smoke function. Chronology
passed in 40.697 seconds with all nine stages, explicit NOT_REQUIRED Math,
exact artifacts, queue ACKs, safe projection, replay and second-process restart.
The unsupported-Math journey passed in 10.936 seconds with Math BLOCKED and
Reasoning/Pedagogy/Director/Visual PENDING, no downstream artifacts, and verified
restart. Cellular hit the supervision limit at 45.037 seconds after all nine
stages SUCCEEDED with eight ACKED messages; its final process/restart proof
remains incomplete. These are not full-smoke passes. No safe stage diagnostic
was persisted for those supervision failures and their cause remains unproved.

No timeout/resource limit, native validation or pre/post-ACK revalidation was
weakened. No validation shortcut or alternate larger-budget execution was
introduced. The focused-test-green implementation is submitted to the requested
exact-head Ubuntu workflow without claiming Windows process closure. Its
complete multi-domain process/restart gate and complete-review readiness remain
unverified until exact-head Linux evidence is externally confirmed.
Windows full canonical green is not claimed. Recorded inherited Windows
failures and qualified historical base comparisons remain retained without
universal cause attribution or waiver. The canonical source audit still
reports its four historical Windows long-path mismatches. Independent reads
of those four exact files through extended paths matched both the preservation
ledger SHA256 and the unchanged base Git blobs. This does not make the original
audit green or rewrite its evidence.

This slice does not establish live-model quality, academic correctness,
teaching effectiveness, learner mastery, rendered visuals, Animation/Audio,
cinematic video, playable games, deployment/security or product acceptance.
