from __future__ import annotations
from dataclasses import dataclass
from ..document import GameLevelContract
from ..errors import GameContractError
from ..canonical import fingerprint
from .contracts import CompiledRule
from .expression_runtime import evaluate_typed

@dataclass(frozen=True)
class RuleProgram:
    rules:tuple[CompiledRule,...]; execution_order:tuple[str,...]; program_fingerprint:str; product_accepted:bool=False

def compile_rules(level:GameLevelContract):
    level.validate();rows=[]
    for r in level.interaction.rules:
        row=CompiledRule(r.rule_id,r.priority,r.condition,len(r.effects),tuple(sorted(r.grounding_refs)));row.validate();rows.append(row)
    # A priority tie is allowed only when tied rules affect disjoint variables; otherwise ordering would be semantically ambiguous.
    byprio={}
    source={r.rule_id:r for r in level.interaction.rules}
    for r in rows:byprio.setdefault(r.priority,[]).append(r.rule_id)
    for ids in byprio.values():
        if len(ids)>1:
            touched=[]
            for rid in ids:touched.extend(e.target_variable_id for e in source[rid].effects)
            if len(touched)!=len(set(touched)):raise GameContractError('GAME_STATE_RULE_PRIORITY_CONFLICT')
    rows=tuple(sorted(rows,key=lambda x:(-x.priority,x.rule_id)));return RuleProgram(rows,tuple(r.rule_id for r in rows),fingerprint(rows),False)

def eligible_rules(level:GameLevelContract,snapshot):
    state=snapshot.as_dict();types=level.state.type_map();out=[]
    for r in sorted(level.interaction.rules,key=lambda x:(-x.priority,x.rule_id)):
        v=evaluate_typed(r.condition,state,types)
        if type(v) is not bool:raise GameContractError('GAME_STATE_RULE_CONDITION_NOT_BOOL',r.rule_id)
        if v:out.append(r.rule_id)
    return tuple(out)
