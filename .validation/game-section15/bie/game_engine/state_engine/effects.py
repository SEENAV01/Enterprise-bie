from __future__ import annotations
from ..interaction import EffectKind,EffectSpec
from ..errors import GameContractError
from ..expressions import ValueType
from .contracts import StateDelta
from .snapshots import validate_values

def _checked_numeric(v,code):
    if type(v) not in (int,float) or isinstance(v,bool):raise GameContractError(code)
    return v

def apply_effect(model,state,effect:EffectSpec):
    effect.validate(model);spec={v.variable_id:v for v in model.variables}[effect.target_variable_id];before=state[effect.target_variable_id]
    k=effect.kind;value=effect.value
    if k==EffectKind.SET:after=value
    elif k==EffectKind.ADD:after=_checked_numeric(before,'GAME_STATE_EFFECT_NUMERIC')+_checked_numeric(value,'GAME_STATE_EFFECT_NUMERIC')
    elif k==EffectKind.SUB:after=_checked_numeric(before,'GAME_STATE_EFFECT_NUMERIC')-_checked_numeric(value,'GAME_STATE_EFFECT_NUMERIC')
    elif k==EffectKind.MUL:after=_checked_numeric(before,'GAME_STATE_EFFECT_NUMERIC')*_checked_numeric(value,'GAME_STATE_EFFECT_NUMERIC')
    elif k==EffectKind.DIV:
        d=_checked_numeric(value,'GAME_STATE_EFFECT_NUMERIC')
        if d==0:raise GameContractError('GAME_EFFECT_DIV_ZERO')
        after=_checked_numeric(before,'GAME_STATE_EFFECT_NUMERIC')/d
    elif k==EffectKind.TOGGLE:
        if type(before) is not bool:raise GameContractError('GAME_STATE_EFFECT_TOGGLE_BOOL')
        after=not before
    else:raise GameContractError('GAME_STATE_EFFECT_KIND')
    if spec.value_type==ValueType.INTEGER and type(after) is not int:raise GameContractError('GAME_STATE_EFFECT_INTEGER_PRESERVATION')
    updated=dict(state);updated[effect.target_variable_id]=after;validate_values(model,updated)
    d=StateDelta(effect.target_variable_id,before,after,k.value);d.validate();return updated,d

def apply_effects(model,state,effects):
    current=dict(state);deltas=[]
    for e in effects:
        current,d=apply_effect(model,current,e);deltas.append(d)
    return current,tuple(deltas)
