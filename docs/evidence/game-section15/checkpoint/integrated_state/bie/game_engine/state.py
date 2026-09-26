from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .expressions import ValueType, Expr, validate_expr
from .ids import require_id, require_unique_ids
from .errors import GameContractError

@dataclass(frozen=True)
class StateVariableSpec:
    variable_id:str; value_type:ValueType; initial_value:Any
    min_value:float|None=None; max_value:float|None=None
    enum_values:tuple[Any,...]=(); units:str|None=None; semantic_role:str|None=None
    def validate(self):
        require_id(self.variable_id,'GAME_STATE_ID')
        if type(self.value_type) is not ValueType:raise GameContractError('GAME_STATE_TYPE')
        if self.min_value is not None and self.max_value is not None and self.min_value>self.max_value:raise GameContractError('GAME_STATE_RANGE')
        if self.value_type==ValueType.ENUM and (not self.enum_values or self.initial_value not in self.enum_values):raise GameContractError('GAME_STATE_ENUM')
        if self.value_type in (ValueType.NUMBER,ValueType.INTEGER):
            if type(self.initial_value) not in (int,float) or isinstance(self.initial_value,bool):raise GameContractError('GAME_STATE_INITIAL')
            if self.value_type==ValueType.INTEGER and type(self.initial_value) is not int:raise GameContractError('GAME_STATE_INITIAL')
            if self.min_value is not None and self.initial_value<self.min_value:raise GameContractError('GAME_STATE_INITIAL_RANGE')
            if self.max_value is not None and self.initial_value>self.max_value:raise GameContractError('GAME_STATE_INITIAL_RANGE')
        if self.units is not None:require_id(self.units,'GAME_STATE_UNITS')
        if self.semantic_role is not None:require_id(self.semantic_role,'GAME_STATE_ROLE')
        return self

@dataclass(frozen=True)
class StateModel:
    variables:tuple[StateVariableSpec,...]
    reset_policy:str='level'
    def validate(self):
        if not self.variables:raise GameContractError('GAME_STATE_VARIABLES_REQUIRED')
        ids=[v.variable_id for v in self.variables];require_unique_ids(ids,'GAME_STATE_DUPLICATE')
        for v in self.variables:v.validate()
        if self.reset_policy not in {'challenge','level','experience','persistent'}:raise GameContractError('GAME_STATE_RESET_POLICY')
        return self
    def type_map(self):return {v.variable_id:v.value_type for v in self.variables}
