# BIE DIR batch 010: phase recovery and current consumer candidates

Original checkpoint: **BIE-DIR-QA-007 (37/37)**. Additive checkpoint:
**BIE-DIR-HARD-CONSUMERS-001**. DIR implementation scope remains incomplete;
the BIE product is **NOT ACCEPTED**. Continue the original recovered vision.

## Implemented work

| Additive task | Supported execution |
| --- | --- |
| BIE-DIR-HARD-REPAIR-001 | Strict frozen-record decoding, bounded phase recovery from actual completed stage evidence, durable current lesson revisions and dependency invalidation in the existing SQLite/CAS/executor path |
| BIE-DIR-HARD-CONSUMERS-001 | Verified persisted DIR consumption by the original timing, visual/animation synchronization and game-handoff functions; typed planning candidates with mandatory freshness/review checks |

The original generation and annotation implementations are retained. One existing
file, `bie/director/director_executor.py`, is extended; before bytes and its patch
are provided. No second orchestrator, artifact ID scheme, repository source root,
new learner questionnaire or lesson-duration target is introduced.

## Bounded phase recovery

Configure the existing `DirectorStageExecutor` normally. For the next existing
`EnterpriseOrchestrator` retry, add:

```python
orchestrator.configuration['director_repair'] = {
    'previous_idempotency_key': previous_completed_director_key,
}
orchestrator.retry_failed('DIRECTOR')
orchestrator.resume()
```

The previous key must identify the previous completed attempt of this lesson and
run. Keys of in-flight work need infrastructure recovery; no lease is stolen.
The existing policy permits at most three stage attempts, with at most three
transport attempts per operation. Currentness also requires consecutive revision
attempts. A successful component may be replaced through a new `ExecutionContext`
with the next attempt and a fresh key; it must not reuse its old key.

Recovery opens the original idempotency receipt and verifies every referenced CAS
blob, envelope hash and parent graph. A complete saved plan/narration is reused
only when the full input fingerprint, generator identity, generation policy and
entire working-code fingerprint are unchanged. Original plan/narration validators
and compilation reconstruct its text, timing and assessment obligations. Changed
dependencies regenerate the lesson. A code upgrade conservatively regenerates;
batch 009 checkpoints do not receive an invented compatibility waiver.

Whole-utterance factual evaluation and original QA execute again after reuse.
Configured annotations, separate review, fine factual checks and timing/QA
composition then execute again. A new contradiction blocks output. The repair
receipt distinguishes reused phases from required phases; actual attempt records
show which operations ran. Semantic model judgments are not a quality certificate.

A failure before complete narration has no reusable narration checkpoint and
regenerates. No sentence patch, scene-local regeneration, annotation-only cache,
partial narration checkpoint, distributed lease recovery or catalog-index restore
is claimed. These remain concrete implementation work.

## Currentness and invalidation

`DirectorRevisionStore` uses a table in the already injected
`SQLiteIdempotencyStore`. It records run, lesson, bounded attempt, execution
fingerprint, owner, verified input IDs, state and current artifact ID. Beginning
a new valid revision withdraws the old current output before provider work.
Failure does not restore it. Owner checks prevent an older worker from publishing
or failing a newer revision. Source invalidation during generation also prevents
late publication. Historical immutable evidence remains readable for audit.

An upstream owner must notify this boundary when replacing source/RE/PED inputs:

```python
receipts = executor.revisions.invalidate_inputs(
    io, run_id, exact_superseded_input_refs, 'Reason for the upstream replacement'
)
```

Supply the old exact refs, not arbitrary filenames or a mutable path. The API
checks the verified input ancestor graph and invalidates only affected ready or
running lessons. Retries may not reuse an explicitly invalidated ancestor. Merely
changing a title or key cannot clear that condition. Old consumer descendants
are rejected transitively; unrelated artifacts do not invalidate this lesson.
All operations are local and use short SQLite transactions, with no model call
inside a publication lock. Replacing files outside this API is not an upstream
change notification system; production BI/RE/PED assembly must call it.

## Actual typed consumer entry points

```python
from bie.director.director_consumers import DirectorConsumers
consumers = DirectorConsumers(io, executor.revisions)
timing_ref = consumers.timing(current_director_ref)
visual_ref = consumers.visual(current_director_ref, typed_visual_intents)
animation_ref = consumers.animation(current_director_ref, visual_ref, typed_animation_intents)
game_ref = consumers.game_handoff(current_director_ref)
candidate = consumers.read_current(animation_ref)
```

These run the existing builders and validators. Inputs are actual persisted
director execution, verified source bytes, exact narration/voice/word anchors,
and supplied typed visual/animation intents. No visual or game quality score is
accepted from the caller. Visual conflicts are retained as BLOCKED candidates
and cannot feed animation. Changed voice/text anchors and mixed revision inputs
are rejected. The game handoff retains shared objective, concept, evidence and
mastery-check bindings.

| Artifact type | Meaning |
| --- | --- |
| director.timing_candidate | Verified original estimated timing/SyncContext |
| director.visual_sync_candidate | Original grounded visual-intent schedule |
| director.animation_sync_candidate | Original visual-dependent animation schedule |
| director.game_handoff_candidate | Original shared-learning-model game handoff |

Every candidate retains `requires_review=true`, `release_ready=false` and
`accepted=false`. Only `PLANNING_PREVIEW` reads are allowed. Render, production,
release and acceptance purposes fail. A final currentness check guards each
write, and each consumer read checks currentness again. Direct CAS reads are
historical/audit access, not authority for consumption. Database/CAS storage and
configured producer identities are trusted local infrastructure, not signatures
or protection against arbitrary Python code modifying its own database.

These are functioning DIR-side review gates. The full VIS/ANI/Game stage
implementations, generated intent producers, SceneIR/GameIR compilers, audio/video
and playable runtime paths must adopt and extend them in their owning work.
Neither a SyncPlan nor a game handoff is a completed executable product.

## Verification and continuation

Run `python scripts/check_dir_repair.py` and
`python examples/repaired_director_walkthrough.py`. The walkthrough deliberately
fails annotation, resumes the saved narration through the original orchestrator,
executes four consumers per domain and rejects all twelve candidates after an
upstream revision. It uses science, economics and fictional-history authored
protocol fixtures. No live model or real PDF/media/game production run is claimed.

Keep the rich upstream KI/math/prerequisite/mastery bridges, long-context
segmentation, broader grounded teaching modes, scene-local repair and durable
catalog/crash recovery on the implementation roadmap. Independently evaluate
real sources and live providers, then re-audit DIR before canonical GitHub
integration in this chat. Video **and** playable revision games, structured IR,
provenance, replaceable models/tools, uncertainty and governed cumulative learning
remain mandatory. ZIP/test counts are not product completion.
