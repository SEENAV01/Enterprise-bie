from __future__ import annotations
import json
from .provenance_adapter import all_refs
from .expression_codegen import compile_expr
from .identifiers import ts_identifier
from .contracts import *
def compile_rules(ctx:CompilerContext):
    ctx.validate();defs=[];rows=[]
    for exp in ctx.document.experiences:
      for level in exp.levels:
        tmap=level.state.type_map()
        for rule in sorted(level.interaction.rules,key=lambda r:(-r.priority,r.rule_id)):
            fn=ts_identifier('rule',rule.rule_id);expr=compile_expr(rule.condition,tmap)
            effects=[{'target':e.target_variable_id,'kind':e.kind.value,'value':e.value} for e in rule.effects]
            defs.append(f'export function {fn}(state: RuntimeState): boolean {{ return Boolean({expr}); }}')
            rows.append({'level_id':level.level_id,'rule_id':rule.rule_id,'function_name':fn,'effects':effects,'priority':rule.priority,'grounding_refs':sorted(rule.grounding_refs),'explanation':rule.explanation})
    header='export type RuntimeState = Record<string, string|number|boolean|null>;\n'
    table='export const ruleMetadata = '+json.dumps({'schema_version':'bie.game.rule-program/2','rules':rows,'uses_eval':False,'product_accepted':False},sort_keys=True,separators=(',',':'))+' as const;\n'
    fnmap='export const ruleFunctions: Record<string,(state: RuntimeState)=>boolean> = {'+','.join(json.dumps(r['rule_id'])+':'+r['function_name'] for r in rows)+'};\n'
    ts=header+'\n'.join(defs)+'\n'+table+fnmap
    return artifact(ArtifactKind.RULE_PROGRAM,'runtime/rules.ts','text/typescript',ts,all_refs(ctx.document.provenance))
