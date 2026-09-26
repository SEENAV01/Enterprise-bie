from __future__ import annotations
from ..canonical import fingerprint
from ..state_engine.snapshots import initial_snapshot
from ..state_engine.contracts import ActionCommand
from ..state_engine.action_router import dispatch_action
from ..state_engine.replay import verify_receipt_chain
from ..state_engine.conditions import evaluate_conditions
from .action_script import derive_candidate_script
from .contracts import ReplayEvidence
from .errors import GameBuildError

def _run(ctx,script):
    ctx.validate();level=ctx.document.experiences[0].levels[0];initial=initial_snapshot(level.state);snapshot=initial;receipts=[]
    for seq,step in enumerate(script,1):
        cmd=ActionCommand(f'cmd:replay:{seq}',seq,step.action_id,'actor:runtime-replay',step.payload,snapshot.snapshot_id);snapshot,evidence=dispatch_action(level,snapshot,cmd)
        if evidence.transition_receipt:receipts.append(evidence.transition_receipt)
    if not receipts:raise GameBuildError('GAME_BUILD_REPLAY_NO_TRANSITIONS')
    chain=verify_receipt_chain(initial,tuple(receipts),snapshot);cond=evaluate_conditions(level,level.challenges[0],snapshot);body={'initial':initial,'final':snapshot,'receipts':receipts,'chain':chain,'condition':cond}
    return body,ReplayEvidence(fingerprint(body),initial.snapshot_id,snapshot.snapshot_id,tuple(r.receipt_id for r in receipts),cond.success,True,False)
def verify_deterministic_replay(ctx,script=None):
    steps=tuple(script or derive_candidate_script(ctx));a,ea=_run(ctx,steps);b,eb=_run(ctx,steps);same=fingerprint(a)==fingerprint(b)
    return ReplayEvidence(ea.run_fingerprint,ea.initial_snapshot_id,ea.final_snapshot_id,ea.transition_receipt_ids,ea.success,same,False).validate()
