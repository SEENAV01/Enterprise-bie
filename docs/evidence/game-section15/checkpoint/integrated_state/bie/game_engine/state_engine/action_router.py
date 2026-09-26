from __future__ import annotations
from dataclasses import dataclass
from ..document import GameLevelContract
from ..interaction import ActionKind
from ..errors import GameContractError
from ..canonical import fingerprint
from .contracts import ActionCommand,StateSnapshot,TransitionReceipt
from .manipulables import normalize_command
from .transition_engine import execute_rule
from .effects import apply_effects
from ..mechanics_engine.state_bridge import StateBinding,propose_patch

_ACTION_MECHANIC={
 ActionKind.TAP:'graph_exploration', ActionKind.DRAG:'drag_and_drop', ActionKind.DROP:'drag_and_drop',
 ActionKind.ADJUST:'manipulate_parameter', ActionKind.SELECT:'classify_sort', ActionKind.TYPE:'retrieval',
 ActionKind.CONNECT:'construct_model', ActionKind.ORDER:'sequence_ordering', ActionKind.PLACE:'spatial_arrangement',
 ActionKind.PREDICT:'prediction_then_observe', ActionKind.SUBMIT:'retrieval', ActionKind.RESET:'reset',
}

@dataclass(frozen=True)
class ActionRoute:
    action_id:str
    action_kind:str
    target_entity_id:str
    mechanic_id:str
    rule_id:str|None
    state_bindings:tuple[str,...]
    route_fingerprint:str
    product_accepted:bool=False
    def validate(self):
        if not all((self.action_id,self.action_kind,self.target_entity_id,self.mechanic_id)):raise GameContractError('GAME_ROUTE_IDENTITY')
        if self.mechanic_id!='reset' and not self.rule_id:raise GameContractError('GAME_ROUTE_RULE_REQUIRED',self.action_id)
        if not self.route_fingerprint.startswith('sha256:'):raise GameContractError('GAME_ROUTE_FINGERPRINT')
        if self.product_accepted:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

@dataclass(frozen=True)
class RoutedTransition:
    route:ActionRoute
    before_snapshot_id:str
    after_snapshot_id:str
    transition_receipt:TransitionReceipt|None
    command_fingerprint:str
    mechanic_patch_fingerprint:str|None
    deterministic:bool=True
    product_accepted:bool=False
    def validate(self):
        self.route.validate()
        if not self.before_snapshot_id or not self.after_snapshot_id or not self.command_fingerprint.startswith('sha256:'):raise GameContractError('GAME_ROUTED_TRANSITION_EVIDENCE')
        if self.route.mechanic_id!='reset' and self.transition_receipt is None:raise GameContractError('GAME_ROUTED_TRANSITION_RECEIPT')
        if self.route.mechanic_id!='reset' and (not self.mechanic_patch_fingerprint or not self.mechanic_patch_fingerprint.startswith('sha256:')):raise GameContractError('GAME_ROUTED_MECHANIC_PATCH')
        if self.deterministic is not True or self.product_accepted:raise GameContractError('GAME_ROUTED_TRANSITION_SCOPE')
        return self

def _entity_bindings(level:GameLevelContract):
    return {e.entity_id:tuple(sorted(set(e.state_bindings))) for e in level.visual.entities}

def compile_action_routes(level:GameLevelContract)->tuple[ActionRoute,...]:
    level.validate();bindings=_entity_bindings(level);rows=[]
    for action in sorted(level.interaction.actions,key=lambda a:a.action_id):
        state_bindings=bindings.get(action.target_entity_id,())
        mechanic=_ACTION_MECHANIC[action.kind];rule_id=None
        if action.kind is not ActionKind.RESET:
            candidates=[]
            for rule in level.interaction.rules:
                targets={e.target_variable_id for e in rule.effects}
                if targets.intersection(state_bindings):candidates.append(rule)
            if not candidates:raise GameContractError('GAME_ROUTE_NO_RULE',action.action_id)
            top=max(r.priority for r in candidates);winners=sorted((r for r in candidates if r.priority==top),key=lambda r:r.rule_id)
            if len(winners)!=1:raise GameContractError('GAME_ROUTE_AMBIGUOUS_RULE',action.action_id)
            rule_id=winners[0].rule_id
        material={'action_id':action.action_id,'kind':action.kind.value,'target':action.target_entity_id,'mechanic':mechanic,'rule_id':rule_id,'state_bindings':state_bindings}
        rows.append(ActionRoute(action.action_id,action.kind.value,action.target_entity_id,mechanic,rule_id,state_bindings,fingerprint(material),False).validate())
    return tuple(rows)

def route_for(level:GameLevelContract,action_id:str)->ActionRoute:
    rows={r.action_id:r for r in compile_action_routes(level)}
    if action_id not in rows:raise GameContractError('GAME_ROUTE_UNKNOWN_ACTION',action_id)
    return rows[action_id]

def dispatch_action(level:GameLevelContract,snapshot:StateSnapshot,command:ActionCommand):
    level.validate();snapshot.validate();norm=normalize_command(level,command);route=route_for(level,command.action_id)
    if route.mechanic_id=='reset':
        from .snapshots import initial_snapshot
        after=initial_snapshot(level.state)
        return after,RoutedTransition(route,snapshot.snapshot_id,after.snapshot_id,None,fingerprint(norm),None,True,False).validate()
    rule={r.rule_id:r for r in level.interaction.rules}[route.rule_id];current=snapshot.as_dict();proposed_values,deltas=apply_effects(level.state,current,rule.effects)
    bindings=tuple(StateBinding(d.variable_id,d.variable_id,True) for d in deltas);before_local={d.variable_id:current[d.variable_id] for d in deltas};after_local={d.variable_id:proposed_values[d.variable_id] for d in deltas}
    patch=propose_patch(level.state,snapshot,route.mechanic_id,before_local,after_local,bindings)
    after,receipt=execute_rule(level,snapshot,command,route.rule_id)
    if fingerprint(after.as_dict())!=patch.proposed_values_fingerprint:raise GameContractError('GAME_ROUTE_MECHANIC_STATE_DIVERGENCE',route.action_id)
    return after,RoutedTransition(route,snapshot.snapshot_id,after.snapshot_id,receipt,fingerprint(norm),fingerprint(patch),True,False).validate()
