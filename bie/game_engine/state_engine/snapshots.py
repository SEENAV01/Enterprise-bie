from __future__ import annotations
from typing import Any,Mapping
import math
from ..canonical import fingerprint
from ..errors import GameContractError
from ..state import StateModel,StateVariableSpec
from ..expressions import ValueType
from .contracts import StateSnapshot

def schema_fingerprint(model:StateModel)->str:
    model.validate();return fingerprint(model)

def _validate_value(spec:StateVariableSpec,value:Any):
    if type(value) is float and not math.isfinite(value):raise GameContractError('GAME_STATE_VALUE_NONFINITE',spec.variable_id)
    if spec.value_type==ValueType.NUMBER:
        if type(value) not in (int,float) or isinstance(value,bool):raise GameContractError('GAME_STATE_VALUE_TYPE',spec.variable_id)
    elif spec.value_type==ValueType.INTEGER:
        if type(value) is not int:raise GameContractError('GAME_STATE_VALUE_TYPE',spec.variable_id)
    elif spec.value_type==ValueType.BOOLEAN:
        if type(value) is not bool:raise GameContractError('GAME_STATE_VALUE_TYPE',spec.variable_id)
    elif spec.value_type==ValueType.STRING:
        if type(value) is not str:raise GameContractError('GAME_STATE_VALUE_TYPE',spec.variable_id)
    elif spec.value_type==ValueType.ENUM:
        if value not in spec.enum_values:raise GameContractError('GAME_STATE_VALUE_ENUM',spec.variable_id)
    if type(value) in (int,float) and not isinstance(value,bool):
        if spec.min_value is not None and value<spec.min_value:raise GameContractError('GAME_STATE_VALUE_RANGE',spec.variable_id)
        if spec.max_value is not None and value>spec.max_value:raise GameContractError('GAME_STATE_VALUE_RANGE',spec.variable_id)
    return value

def validate_values(model:StateModel,values:Mapping[str,Any]):
    model.validate();specs={v.variable_id:v for v in model.variables}
    if set(values)!=set(specs):raise GameContractError('GAME_STATE_VALUE_COVERAGE')
    return {k:_validate_value(specs[k],values[k]) for k in sorted(values)}

def make_snapshot(model:StateModel,values:Mapping[str,Any],tick:int=0,parent_snapshot_id=None,transition_receipt_id=None):
    checked=validate_values(model,values);sf=schema_fingerprint(model)
    body={'tick':tick,'values':checked,'schema_fingerprint':sf,'parent_snapshot_id':parent_snapshot_id,'transition_receipt_id':transition_receipt_id}
    snap=StateSnapshot('snapshot:'+fingerprint(body)[7:31],tick,tuple(sorted(checked.items())),sf,parent_snapshot_id,transition_receipt_id,False)
    return snap.validate()

def initial_snapshot(model:StateModel):
    return make_snapshot(model,{v.variable_id:v.initial_value for v in model.variables},0)
