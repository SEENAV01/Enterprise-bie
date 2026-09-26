from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
from ..canonical import fingerprint
from ..ids import require_id
from ..state import StateModel
from ..state_engine.contracts import StateSnapshot,StateDelta
from ..state_engine.snapshots import validate_values
from ..errors import GameContractError

@dataclass(frozen=True)
class StateBinding:
    local_key:str;state_variable_id:str;writable:bool=True
    def validate(self,state_ids:set[str]):
        require_id(self.local_key,'GAME_MECH_BINDING_LOCAL');require_id(self.state_variable_id,'GAME_MECH_BINDING_STATE')
        if self.state_variable_id not in state_ids:raise GameContractError('GAME_MECH_BINDING_UNKNOWN_STATE',self.state_variable_id)
        if type(self.writable) is not bool:raise GameContractError('GAME_MECH_BINDING_WRITABLE')
        return self
@dataclass(frozen=True)
class ProposedStatePatch:
    snapshot_id:str;mechanic_id:str;bindings:tuple[StateBinding,...];deltas:tuple[StateDelta,...];before_fingerprint:str;proposed_values_fingerprint:str;authoritative_applied:bool=False;product_accepted:bool=False
    def validate(self):
        require_id(self.snapshot_id,'GAME_MECH_PATCH_SNAPSHOT');require_id(self.mechanic_id,'GAME_MECH_PATCH_MECHANIC')
        if not self.bindings or not self.deltas:raise GameContractError('GAME_MECH_PATCH_EMPTY')
        for d in self.deltas:d.validate()
        if not self.before_fingerprint.startswith('sha256:') or not self.proposed_values_fingerprint.startswith('sha256:'):raise GameContractError('GAME_MECH_PATCH_HASH')
        if self.authoritative_applied or self.product_accepted:raise GameContractError('GAME_MECH_PATCH_SCOPE')
        return self

def propose_patch(model:StateModel,snapshot:StateSnapshot,mechanic_id:str,before_local:Mapping[str,Any],after_local:Mapping[str,Any],bindings:tuple[StateBinding,...]):
    model.validate();snapshot.validate();require_id(mechanic_id,'GAME_MECH_PATCH_MECHANIC')
    state_ids=set(model.type_map());[b.validate(state_ids) for b in bindings]
    if len({b.local_key for b in bindings})!=len(bindings) or len({b.state_variable_id for b in bindings})!=len(bindings):raise GameContractError('GAME_MECH_BINDING_DUPLICATE')
    current=snapshot.as_dict();proposed=dict(current);deltas=[]
    for b in bindings:
        if b.local_key not in before_local or b.local_key not in after_local:raise GameContractError('GAME_MECH_BINDING_LOCAL_MISSING',b.local_key)
        if before_local[b.local_key]!=current[b.state_variable_id]:raise GameContractError('GAME_MECH_BINDING_STALE',b.state_variable_id)
        if before_local[b.local_key]!=after_local[b.local_key]:
            if not b.writable:raise GameContractError('GAME_MECH_BINDING_READONLY',b.state_variable_id)
            proposed[b.state_variable_id]=after_local[b.local_key];deltas.append(StateDelta(b.state_variable_id,current[b.state_variable_id],after_local[b.local_key],'mechanic_proposal').validate())
    if not deltas:raise GameContractError('GAME_MECH_PATCH_NOOP')
    checked=validate_values(model,proposed)
    p=ProposedStatePatch(snapshot.snapshot_id,mechanic_id,bindings,tuple(deltas),fingerprint(snapshot),fingerprint(checked),False,False)
    return p.validate()
