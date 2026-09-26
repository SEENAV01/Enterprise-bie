from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
from ..document import GameLevelContract
from ..interaction import ActionKind
from ..errors import GameContractError
from ..canonical import fingerprint
from .contracts import ActionCommand,CompiledAction

_PAYLOAD_RULES={ActionKind.TAP:(),ActionKind.SELECT:('selection',),ActionKind.SUBMIT:(),ActionKind.RESET:(),ActionKind.DRAG:('x','y'),ActionKind.DROP:('x','y'),ActionKind.PLACE:('x','y'),ActionKind.ADJUST:('delta',),ActionKind.TYPE:('text',),ActionKind.CONNECT:('target_id',),ActionKind.ORDER:('order',),ActionKind.PREDICT:('prediction',)}

def compile_actions(level:GameLevelContract):
    level.validate();entities={e.entity_id for e in level.visual.entities};rows=[]
    for a in level.interaction.actions:
        if a.target_entity_id not in entities:raise GameContractError('GAME_STATE_ACTION_VISUAL_TARGET_MISSING',a.action_id)
        row=CompiledAction(a.action_id,a.kind.value,a.target_entity_id,a.accessible_label,a.keyboard_equivalent);row.validate();rows.append(row)
    return tuple(sorted(rows,key=lambda x:x.action_id))

def normalize_command(level:GameLevelContract,command:ActionCommand):
    command.validate();catalog={a.action_id:a for a in level.interaction.actions}
    if command.action_id not in catalog:raise GameContractError('GAME_STATE_UNKNOWN_ACTION',command.action_id)
    spec=catalog[command.action_id];payload=dict(command.payload);required=_PAYLOAD_RULES[spec.kind]
    if any(k not in payload for k in required):raise GameContractError('GAME_STATE_ACTION_PAYLOAD_REQUIRED',command.action_id)
    if spec.kind in {ActionKind.DRAG,ActionKind.DROP,ActionKind.PLACE} and any(type(payload[k]) not in (int,float) for k in ('x','y')):raise GameContractError('GAME_STATE_ACTION_COORDINATE_TYPE')
    if spec.kind==ActionKind.ADJUST and type(payload['delta']) not in (int,float):raise GameContractError('GAME_STATE_ACTION_DELTA_TYPE')
    return {'command':command,'action_kind':spec.kind.value,'target_entity_id':spec.target_entity_id,'payload':tuple(sorted(payload.items())),'command_fingerprint':fingerprint(command),'product_accepted':False}
