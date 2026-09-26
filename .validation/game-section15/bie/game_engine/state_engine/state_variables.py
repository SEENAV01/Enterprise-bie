from __future__ import annotations
from dataclasses import dataclass
from ..state import StateModel
from ..canonical import fingerprint
from .snapshots import initial_snapshot,schema_fingerprint

@dataclass(frozen=True)
class CompiledStateSchema:
    variable_ids:tuple[str,...]; type_map:tuple[tuple[str,str],...]; reset_policy:str; schema_fingerprint:str; initial_snapshot_id:str; product_accepted:bool=False

def compile_state_model(model:StateModel):
    model.validate();snap=initial_snapshot(model)
    return CompiledStateSchema(tuple(sorted(v.variable_id for v in model.variables)),tuple(sorted((v.variable_id,v.value_type.value) for v in model.variables)),model.reset_policy,schema_fingerprint(model),snap.snapshot_id,False)
