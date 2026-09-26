from __future__ import annotations
import json
from .provenance_adapter import all_refs
from .expression_codegen import compile_expr
from .identifiers import ts_identifier
from .contracts import *
def compile_adaptation(ctx:CompilerContext):
    ctx.validate();defs=[];rows=[]
    for exp in ctx.document.experiences:
      for level in exp.levels:
        tmap=level.state.type_map();rules=sorted(level.adaptation.rules,key=lambda r:(r.priority,r.adaptation_id))
        if len({r.priority for r in rules})!=len(rules):raise GameCompilerError('GAME_COMP_ADAPT_PRIORITY_TIE')
        for r in rules:
            fn=ts_identifier('adapt',json.dumps([exp.game_id,level.level_id,r.adaptation_id],separators=(',',':')));expr=compile_expr(r.condition,tmap);defs.append(f'export function {fn}(state: RuntimeState): boolean {{ return Boolean({expr}); }}')
            rows.append({'level_id':level.level_id,'adaptation_id':r.adaptation_id,'function_name':fn,'action':r.action.value,'priority':r.priority,'target_id':r.target_id})
    ts='export type RuntimeState = Record<string, string|number|boolean|null>;\n'+'\n'.join(defs)+'\nexport const adaptationMetadata = '+json.dumps({'schema_version':'bie.game.adaptation-program/2','rules':rows,'deterministic_priority':True,'product_accepted':False},sort_keys=True,separators=(',',':'))+' as const;\n'+'export const adaptationFunctions: Record<string,(state: RuntimeState)=>boolean> = {'+','.join(json.dumps(r['function_name'])+':'+r['function_name'] for r in rows)+'};\n'
    return artifact(ArtifactKind.ADAPTATION_PROGRAM,'runtime/adaptation.ts','text/typescript',ts,all_refs(ctx.document.provenance))
