"""Bounded recovery harness over the actual BIE executor and preauthored providers."""
from dataclasses import replace
from directing_fixtures import context


def retry_context(fixture, previous, attempt=2, **changes):
    config = {**previous.configuration, 'director_repair': {'previous_idempotency_key': previous.idempotency_key}}
    return replace(context(fixture), attempt=attempt, idempotency_key='repair:' + str(attempt), configuration=config, **changes)


def intents(execution):
    # Consumer tests declare the original SYNC-002 -> SYNC-001 closure. Phase
    # recovery itself needs no synchronization fixture/import at module load.
    from bie.director.sync_contract import build_sync_context, SyncIndex, IntentBinding
    from bie.director.narration_visual_sync import VisualIntent
    from bie.director.narration_animation_sync import AnimationIntent
    e = execution
    sync = build_sync_context(e.speech, e.pauses, e.emphasis, e.timeline)
    index = SyncIndex(sync); u = e.snapshot.utterances[0]
    anchor = index.anchor(u.utterance_id, 0, 3)
    binding = IntentBinding('visual:1', 'target:1', anchor, u.evidence_ids, u.objective_ids,
                            e.game_handoff.concept_ids, 'Represent the actual narrated explanation')
    visual = VisualIntent(binding, 'text')
    animation = AnimationIntent(replace(binding, intent_id='animation:1'), 'visual:1', 'reveal')
    return (visual,), (animation,)
