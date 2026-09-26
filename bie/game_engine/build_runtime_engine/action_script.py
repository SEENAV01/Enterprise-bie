from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from ..interaction import ActionKind
from ..ids import require_id
from .errors import GameBuildError
@dataclass(frozen=True)
class ActionStep:
    action_id:str
    payload:tuple[tuple[str,Any],...]=()
    def validate(self):require_id(self.action_id,'GAME_BUILD_SCRIPT_ACTION');return self

def default_payload(kind:ActionKind):
    if kind in {ActionKind.DRAG,ActionKind.DROP,ActionKind.PLACE}:return (('x',2.0),('y',0.0))
    if kind is ActionKind.ADJUST:return (('delta',1.0),)
    if kind is ActionKind.PREDICT:return (('prediction','candidate'),)
    if kind is ActionKind.TYPE:return (('text','candidate'),)
    if kind is ActionKind.CONNECT:return (('target_id','candidate'),)
    if kind is ActionKind.ORDER:return (('order',('candidate',)),)
    if kind is ActionKind.SELECT:return (('selection','candidate'),)
    return ()

def derive_candidate_script(ctx):
    ctx.validate();level=ctx.document.experiences[0].levels[0]
    from ..state_engine.action_router import compile_action_routes
    routes={r.action_id:r for r in compile_action_routes(level)}
    for a in sorted(level.interaction.actions,key=lambda x:x.action_id):
        route=routes[a.action_id]
        if route.rule_id:return (ActionStep(a.action_id,tuple(sorted(default_payload(a.kind)))).validate(),)
    raise GameBuildError('GAME_BUILD_NO_ROUTABLE_ACTION')
