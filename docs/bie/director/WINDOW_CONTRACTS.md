# BIE DIR window execution — batch 012

This extends the existing BIE director for the documented bounded-context scope.
The original 37 DIR tasks, original product vision and prior hardening remain the
baseline. DIR enterprise implementation is still incomplete; BIE is NOT ACCEPTED.
Video teaching and playable revision games remain equally mandatory outcomes.

## Supported execution

`BIE-DIR-HARD-WINDOWS-001` constructs deterministic execution windows over actual
selected PED decisions. `BIE-DIR-HARD-LONG-DIRECTING-001` executes those windows on
the original registered director, assembles one complete lesson and preserves its
source, RE/PED, assessment, QA, repair and consumer contracts. These are two new
audit-derived implementation tasks, not recovered original roadmap entries.

Configure the same executor explicitly:

```python
from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.director_executor import DirectorStageExecutor

director = DirectorStageExecutor(
    io, idempotency_store, generator, generator_identity, critic, critic_identity,
    policy=WindowedDirectingPolicy(),
    annotations=annotation_runtime,
)
```

The existing `execute_grounded_director` also accepts this policy. Its public input
must still be the verified `DirectorInputs` loaded from actual source/RE/PED
artifacts. The stage still receives exactly RE and PED references. Its existing
graph, namespace, artifact types, SQLite revision/currentness and downstream APIs
remain in place. `DirectingPolicy()` keeps the earlier single-context path and
schemas. Window generation is explicit, not a silent fallback on a rejected call.

## Source and teaching invariants

Windows follow the actual PED and supplied rich-context prerequisite DAG, with
original binding order as the stable tie-breaker. A decision belongs to exactly
one window; its complete source pages and supplied math chain stay indivisible.
Every selected source evidence ID and cited page fingerprint must be covered.
The scheduler includes transitive prerequisite support and the actual RE closure;
the model context also carries original prerequisite bindings, objectives and
decisions under an explicitly separate support field. Supporting decisions are
context, not additional owned teaching or duplicated assessments.

Exact source definitions/conditions, supplied math steps and original RE/PED
identities remain. Existing KI/PR/MATH/PED compilation and source-envelope checks
still run. A window is a distinct immutable input view, not a new upstream
artifact. No source text, source artifact, original PED plan, earlier narration
or requirement is overwritten by a projection.

Every planning response echoes full-input, view and window bindings and uses its
assigned scene namespace. The number and structure of scenes are chosen within
the original resource/teaching contracts; one decision can produce several scenes.
Host assembly then re-runs the original **full-scope** plan validator: complete
PED/objective/evidence/assessment coverage, unique IDs, prerequisites, bridge
obligations and ordered math steps. Passing individual windows cannot waive a
global requirement. Every narration is also validated against the full input and
assembled plan before the original compiler and factual QA execute.

## Continuity and resource boundaries

| Item | Contract |
| --- | --- |
| Original generation request budget | 96,000 characters by default, including instructions and response schema |
| Planning reserve | 12,000 characters by default for completed-plan context and retry feedback |
| Window count | At most 128 by default; exceeding this fails explicitly |
| Planning continuity | Complete global objective/prerequisite outline and completed scene contracts |
| Narration continuity | Complete global outline, full-plan fingerprint, completed scene identity/coverage ledger and the last complete scene by default |
| Earlier speech | All scenes remain unchanged in the host result; `prior_scene_count` controls complete recent scenes sent to the generator |
| Aggregate output | Existing total scene, beat, utterance and response budgets still apply |
| Annotation/reviewer | Existing full-context 180,000/260,000-character budgets remain; no segmentation is added here |
| Factual evaluation | Existing complete-cited-page 48,000-character budget remains |

These are configured character/resource limits, not demonstrated model token
limits or lesson-duration targets. Production transports still need real provider
token budgeting, deadlines/cancellation and calibration.

The completed ledger is evidence of generated coverage, not learner mastery and
not a summary of unseen wording. Requests explicitly identify omitted earlier
scene wording and prohibit inventing previous quotations, examples, learner
answers or dangling references from hashes. The exact recent scenes are not cut.
The host retains all speech, but semantic continuity across arbitrarily distant
scenes has not been established. Full-discourse retrieval/reconciliation remains
implementation work.

One indivisible page, RE record, prerequisite closure or math chain may exceed the
budget. The full outline, accumulated ledger, actual local plan or recent speech
may also overflow later requests. Such cases fail explicitly. This batch does not
silently trim evidence, split a derivation, summarize conditions, drop a remaining
decision or publish a partially generated lesson. Planning does not guarantee that
every later request will fit; the actual request gate is authoritative. A late
generation failure retains its attempt trace but has no scene-local checkpoint.

## Persistence, repair and consumers

`WindowedDirectorResult` retains `WindowExecution`: policy, generator identity,
ordered source-bound windows and exact window-to-scene assignments. The restricted
recovery codec recognizes these frozen types. Revalidation rebuilds the schedule
and reconstructs every actual plan/narration request fingerprint, including retry
feedback and the preceding generated speech. Missing, extra, reordered or edited
request evidence and removed window metadata fail. Response fingerprints are
retained transport evidence; they are not independently signed provider receipts.

The existing whole-base annotation repair reuses exact planning/narration only
when inputs, policies and code match; it re-executes factual QA. Changing the
window policy regenerates. Source/context ancestor invalidation reaches outputs
and timing, visual, animation and game-handoff candidates. Every candidate remains
review-required and `accepted=False`, `release_ready=False`. These consumers run
the original planning functions; they do not render media or run a game.

## Reproduce

Use the combined runnable ZIP for the complete supported path. Atomic ZIPs declare
their earlier task and canonical-file dependencies. Apply original archives first,
then hardening overlays in dependency order. Do not overwrite later source with an
earlier archive. The context-window atomic package alone establishes its contract
layer; the long-directing package adds execution and complete support propagation.

```sh
python scripts/check_dir_windows.py
python examples/windowed_director_walkthrough.py --output verification/windowed_director.json
```

The new controlled walkthrough uses two authored archive collections and one
supplied algebraic chain. It exercises actual registered execution, failed
annotation recovery without generation, complete source coverage, bounded actual
requests, all four original consumers and stale rejection. These are authored
UTF-8 source/provider fixtures, not real PDF extraction or empirical teaching
quality. The original 515 DIR tests remain alongside the new contract/adverse and
integration tests. A separate unchanged canonical gate does not discover staged
DIR; neither gate establishes product acceptance.

## Remaining implementation

Continue bounded annotation/reviewer context with global discourse reconciliation
and coverage, richer upstream codecs and grounded demonstration/inquiry/
misconception teaching, scene-local correction/checkpoints, catalog/crash/lease
recovery and production stage adoption. Independent real-source/provider
evaluation, authenticated grading integration, media/runtime and playable-game
validation remain required. Re-audit DIR implementation, then integrate losslessly
into canonical GitHub in this chat. No GitHub write occurs in batch 012.
