from __future__ import annotations
from .provenance_adapter import all_refs
import json
from ..canonical import canonical_json
from .contracts import *
def compile_state_machine(ctx:CompilerContext):
    ctx.validate();games=[]
    for exp in ctx.document.experiences:
        levels=[]
        for level in exp.levels:
            vars=[{'id':v.variable_id,'type':v.value_type.value,'initial':v.initial_value,'min':v.min_value,'max':v.max_value,'units':v.units,'role':v.semantic_role} for v in level.state.variables]
            levels.append({'level_id':level.level_id,'reset_policy':level.state.reset_policy,'variables':vars,'state_ids':sorted(v['id'] for v in vars)})
        games.append({'game_id':exp.game_id,'levels':levels})
    data={'schema_version':'bie.game.state-machine/1','games':games,'deterministic':True,'product_accepted':False}
    ts='export const stateMachine = '+json.dumps(data,sort_keys=True,separators=(',',':'))+' as const;\nexport type RuntimeState = Record<string, string|number|boolean|null>;\nexport function cloneState(s: RuntimeState): RuntimeState { return {...s}; }\n'
    refs=all_refs(ctx.document.provenance);return artifact(ArtifactKind.STATE_MACHINE,'runtime/state-machine.ts','text/typescript',ts,refs)
