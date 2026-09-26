from __future__ import annotations
from ..canonical import fingerprint
from ..state_engine.snapshots import initial_snapshot
from ..state_engine.contracts import ActionCommand
from ..state_engine.action_router import dispatch_action
from .action_script import derive_candidate_script
from .contracts import InteractionSimulationReceipt
from .errors import GameBuildError

def simulate(ctx,bundle,script=None):
    ctx.validate();level=ctx.document.experiences[0].levels[0];snapshot=initial_snapshot(level.state);steps=tuple(script or derive_candidate_script(ctx))
    if not steps:raise GameBuildError('GAME_BUILD_ACTION_SCRIPT_REQUIRED')
    interactions=next(a for a in bundle.artifacts if a.path=='runtime/interactions.ts').content;last=None
    for seq,step in enumerate(steps,1):
        step.validate();cmd=ActionCommand(f'cmd:runtime:{seq}',seq,step.action_id,'actor:runtime-test',step.payload,snapshot.snapshot_id);after,evidence=dispatch_action(level,snapshot,cmd);route=evidence.route
        if route.action_id not in interactions or (route.rule_id and route.rule_id not in interactions):raise GameBuildError('GAME_BUILD_COMPILED_ROUTE_MISSING')
        last=(route,evidence);snapshot=after
    route,evidence=last;motion_ids=tuple(m.cue_id for m in level.visual.motion if m.entity_id==route.target_entity_id) or tuple(m.cue_id for m in level.visual.motion)
    if not motion_ids:raise GameBuildError('GAME_BUILD_SEMANTIC_MOTION_MISSING')
    return InteractionSimulationReceipt(route.mechanic_id,evidence.transition_receipt.receipt_id if evidence.transition_receipt else 'receipt:reset','event:'+route.action_id,fingerprint(evidence),True,motion_ids,True,False).validate()
