# BIE DIR original batch 004 — SYNC-001…005

These five original roadmap tasks are implemented and unit/contract tested.
The canonical GitHub base remains PED at
bc3147db408fc5a5d54017c8b907f580477ff2c3. DIR has 30 of 37 original tasks
implemented/tested; QA-001…007 remain. GitHub integration follows complete DIR
implementation, enterprise audit, required hardening and re-audit in this chat.
Nothing here establishes product acceptance.

## Original authority and implementation decisions

The original 18-section registry, page 10, specifies these exact IDs and titles.
It does not prescribe APIs or numeric policies. The contracts described here are
new implementation decisions under those original tasks, based on recovered
SCRIPT/LESSON contracts, verified TIME-001…005 and the existing canonical Scene
IR vocabulary. The shared sync_contract.py is owned by SYNC-001; it is not a
sixth task. Existing canonical and recovered DIR/TIME source is unchanged.

| Original task | Module | Main builder / validator |
| --- | --- | --- |
| BIE-DIR-SYNC-001 narration-to-visual intent | narration_visual_sync.py | sync_visual_intents / validate_visual_sync |
| BIE-DIR-SYNC-002 narration-to-animation intent | narration_animation_sync.py | sync_animation_intents / validate_animation_sync |
| BIE-DIR-SYNC-003 equation narration sync | equation_narration_sync.py | sync_equation_narration / validate_equation_sync |
| BIE-DIR-SYNC-004 graph narration sync | graph_narration_sync.py | sync_graph_narration / validate_graph_sync |
| BIE-DIR-SYNC-005 simulation narration sync | simulation_narration_sync.py | sync_simulation_narration / validate_simulation_sync |

## Run the delivered bundle

Use Python 3.10+ (tested with 3.12.14), standard library only. From the extracted
BIE_DIR_ORIGINAL_BATCH_004_SYNC_001_005.zip root:

```bash
python3 scripts/check_dir_sync.py
python3 examples/sync_walkthrough.py
```

The bundle contains a runnable DIR subset with all 30 original atomic ZIPs,
their working source/tests and the exact canonical Scene IR dependency. No
manual assembly of atomic ZIPs is needed. It is not a complete repository or a
GitHub integration. The older check_dir_timing.py and TIMING_CONTRACTS.md remain
preserved historical batch artifacts; use check_dir_sync.py for current counts.

Verification: 156 local DIR tests = 99 previous DIR/TIME + 49 new SYNC task unit
tests + 8 cross-contract tests, zero failures/errors/skips. A separate canonical
integrated_check.py gate passes 2,160 tests and archive-preservation checks.
Canonical test discovery does not yet include DIR: section integration must
connect both test discovery and archive/member provenance. The Scene IR bridge
test constructs and validates its existing SceneElement/AnimationTrack contracts;
it does not compile or render media.

## Shared timing, grounding and status

build_sync_context binds SpeechTimingPlan, PauseTimingPlan, EmphasisTimingPlan
and SceneDurationPlan. It recomposes and verifies the entire scene timeline from
its timing parents; matching stored hashes alone cannot validate edited events.
SyncIndex then resolves narration spans through indexed scene/utterance/word
events. It does not infer timing from a raw text-intent string.

NarrationAnchor is an exact half-open [start_word, end_word) span with scene ID,
utterance ID and the utterance fingerprint. IntentBinding adds stable intent and
target IDs, source evidence, learning objectives, explicit concepts and teaching
purpose. Blank/unknown IDs, bad ranges, mutable values, NaN/infinity/bool numeric
inputs, source mismatches and stale revisions are rejected. Source and objective
IDs must belong to the narration; child cues must also belong to their visual
parent. Equation/graph/simulation revisions are fingerprint-bound.

Concept-to-narration/target bindings are explicit structured inputs from the
upstream director. SYNC does not invent semantic correspondence from substring
matches. It validates and schedules those bindings, not their factual truth.
Future VIS/ANI planners choose actual diagrams, layouts, 2D/3D assets, motion
and renderer parameters. This preserves the intelligence/IR/compiler separation.

SyncWindow records scene-local integer milliseconds, core narration start/end,
character anchors and segment ID. A word span includes its internal planned
pauses, measured/report-supplied gaps and emphasis time. New WPM, pause or source
revisions invalidate old sync results; explicit rebuilding computes new windows.
Different scenes can reuse element IDs because identity is scene-scoped.

SyncPlan records task/policy versions, exact context and visual-parent
fingerprints, immutable original inputs, definitions, cues, structured issues
with repair destinations and inherited review reasons. Status is BLOCKED if
any issue remains; otherwise READY_FOR_DOWNSTREAM_REVIEW. requires_review stays
true and accepted stays false. Structural corruption raises ValueError. Empty
scoped requests produce NO_INTENTS rather than an apparently successful plan.

Timing basis remains ESTIMATED_WPM or REPORTED_AUDIO_ALIGNMENT as supplied by
TIME. Reported alignment is not certified audio: no audio bytes are opened or
retimed. An unresolved audio pause shortfall propagates AUDIO_REPLAN_REQUIRED
through visual and specialized plans. Consumers must honor BLOCKED and review
state; a mathematically valid timestamp is not release/acceptance permission.

## Visual and animation behavior

VisualIntent selects an existing Scene IR element kind and explicit lead/hold
milliseconds around a narration span. Negative lead time and holds beyond scene
end produce actionable blockers with the original requested interval preserved.
There is no silent clipping, scene cap or narration truncation. Same-target
overlapping visibility requests require explicit upstream consolidation;
separate nonoverlapping windows are supported. A target cannot change element
kind within one scene.

AnimationIntent references a specific visual intent, a supported animation kind,
minimum duration and optional predecessor IDs. Intervals must fit the visual
lifetime and minimum duration. Unknown/cross-scene/self dependencies and cycles
are rejected; timing-order violations are blocked. Iterative cycle validation
avoids Python call-stack limits. Concurrent property ownership is checked,
including transform/path-follow conflicts with position changes. Independent
properties can overlap. The property map is an intent-level ownership contract;
actual renderer effects still require ANI/compiler QA.

## Equation behavior

EquationState retains the original SCRIPT-007 DerivationNarrationStep, expression,
step index and source IDs. EquationToken binds an ID to exact expression character
offsets (nested source spans are allowed, duplicate token IDs are not). The timed
utterance must match the source step's narration exactly. For spoken equation
realization changes, rebuild the upstream structured step and its fingerprints.
Existing timing review flags for raw numbers/symbols remain visible.

SHOW_STEP establishes a display state; HIGHLIGHT_TOKEN requires named tokens in
the active state throughout its interval. Declared states need display cues.
Displays are ordered by actual narration time; backward/repeated steps require
an explicit allow_revisit flag. State overlap and inactive-token highlights block.
SHOW_STEP carries active_until_ms, ending at the next state change or its visual
lifetime. The original expression and source-step hash survive in cue data.
No symbolic-equivalence, derivation-correctness or math acceptance is inferred.

## Graph behavior

GraphDefinition declares scene/element/revision, labeled numeric x/y axes with
explicit units, source-bound series and point IDs. Linear and positive log axes
are supported; values, ranges, finite arithmetic and source coverage are checked.
Categorical charts, inferred trends, arbitrary plotting functions and layouts
are separate downstream responsibilities. Series order is explicitly supplied;
parametric curves need not be sorted by x. Reversed request order is rejected
rather than silently rearranged; an intentionally reversed series needs its own
revised definition.

SHOW_AXES must finish before TRACE_SERIES, HIGHLIGHT_POINT or HIGHLIGHT_RANGE in
the same visibility window. Point/range IDs bind exact data and units. Range
endpoints select a contiguous interval in declared series order. Trace waypoints
retain raw x/y, normalized coordinates and monotonic scene timestamps. Timing
uses source-index linear scheduling, an explicit intent heuristic, not physical
time interpolation or proof of a trend. Insufficient milliseconds block and
produce no invented simultaneous trace samples. Data meaning/render QA remains.

## Simulation behavior

SimulationDefinition declares a model fingerprint, seed, revision, bounded
parameters/units, complete named states and allowed transitions. Each transition
names exact source/destination states, the changed-parameter set and minimum
duration. These must agree structurally. Definitions contain immutable numeric
data; no user code, expression evaluator or model execution is invoked.

SimulationIntent consumes original SCRIPT-006 DemoNarrationStep objects and
exact timed narration. SETUP initializes the declared initial state; ACTION
requires a valid transition from the current state; OBSERVE follows that action;
INTERPRET follows observation of the same state. Overlaps, invalid causal order,
unfinished cycles and insufficient action time block. Explicit later SETUP can
reset after a completed cycle; it cannot hide an unfinished action.

Cues carry declared_values, seed, model/state fingerprints and
execution_status=DECLARED_NOT_EXECUTED. These values are planned inputs/states,
not measured simulation outcomes. Physics/model validity, actual deterministic
runtime traces, frame/audio synchronization and interactive-game execution are
separate acceptance requirements.

## Next work and preserved limitations

Next original tasks are BIE-DIR-QA-001…007: factual script QA, source grounding,
coherence, repetition detection, age/level appropriateness, pacing QA and the
director benchmark. A normal next batch can cover QA-001…005, followed by
QA-006…007 before the required section completeness audit.

The three recovered legacy findings remain open under existing IDs:
LESSON-001 parent cycles; SCRIPT-001 blank grounding IDs; SCRIPT-010 blank game
handoff IDs. New sync/timing validation does not rewrite those original modules.
Synthetic tests/examples are not Money.pdf ingestion or a multi-domain benchmark.
Real BI/KI/PR/MATH/RE/PED/DIR lineage, downstream VIS/ANI and compiler behavior,
actual audio/video builds/renders, playable-game validation and governed
cumulative learning remain explicit product requirements. Original vision and
the section-end integration workflow are unchanged.
