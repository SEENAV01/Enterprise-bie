"""Closed TypeScript emitters: constants and a finite pure reducer only.

These do NOT compile arbitrary Scene IR, repair handwritten programs or replace a
native game UI. Their executable grammar is fixed; all supplied strings are data.
"""
import json,re
from ..release_v2.contracts import ContractError
from ..source_v2.codec import loads
RESERVED=set(('break case catch class const continue debugger default delete do else enum export extends false finally for function if import in instanceof new null return super switch this throw true try typeof var void while with as implements interface let package private protected public static yield any boolean constructor prototype __proto__ eval arguments await async undefined NaN Infinity').split())
def identifier(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}',value) or value in RESERVED:raise ContractError('MEDIA_REPAIR_EXPORT_IDENTIFIER')
    return value

def read_value(raw):
    if type(raw) is not str or len(raw)>1048576:raise ContractError('MEDIA_REPAIR_JSON_VALUE')
    v=loads(raw.encode('utf-8'))
    def check(x,depth=0):
        if depth>24:raise ContractError('MEDIA_REPAIR_VALUE_DEPTH')
        if x is None or type(x) is bool:return
        if type(x) is int:
            if abs(x)>9007199254740991:raise ContractError('MEDIA_REPAIR_JS_INTEGER_RANGE')
            return
        if type(x) is str:
            if len(x)>100000 or '\x00' in x:raise ContractError('MEDIA_REPAIR_VALUE_TEXT')
            return
        if type(x) is list:
            if len(x)>4096:raise ContractError('MEDIA_REPAIR_VALUE_ITEMS')
            for a in x:check(a,depth+1)
            return
        if type(x) is dict:
            if len(x)>4096 or any(k in ('__proto__','constructor','prototype') for k in x):raise ContractError('MEDIA_REPAIR_VALUE_KEY')
            for a in x.values():check(a,depth+1)
            return
        raise ContractError('MEDIA_REPAIR_VALUE_TYPE')
    check(v);return v

def literal(x):return json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)
def code_header(module_id):return '// BIE-QA-GENERATED-CONSTANTS/1 '+module_id+'\n'
def game_header(game_id):return '// BIE-QA-GENERATED-REDUCER/1 '+game_id+'\n'

def emit_constants(policy):
    lines=[code_header(policy.module_id),'// Data grammar only. No imports or executable candidate expressions.\n']
    for e in sorted(policy.exports,key=lambda x:x.name):
        v=read_value(e.json_value)
        lines.append('export const '+identifier(e.name)+' = '+literal(v)+(' as const' if v is not None else '')+';\n')
    return ''.join(lines).encode('utf-8')

def validate_oracle(p):
    states={s.state_id for s in p.states};edges={(t.before,t.action_id):t.after for t in p.transitions}
    reached={p.initial_state}
    while True:
        nxt=reached|{v for (s,_),v in edges.items() if s in reached}
        if nxt==reached:break
        reached=nxt
    if reached!=states:raise ContractError('MEDIA_REPAIR_UNREACHABLE_ORACLE_STATE')
    for scenario in p.scenarios:
        state=p.initial_state
        for action in scenario.action_ids:
            if (state,action) not in edges:raise ContractError('MEDIA_REPAIR_ORACLE_SCENARIO_GAP')
            state=edges[state,action]
    return edges

def emit_reducer(p):
    validate_oracle(p)
    states=[[s.state_id,[[v.key,v.text] for v in sorted(s.values,key=lambda v:v.key)]] for s in sorted(p.states,key=lambda s:s.state_id)]
    transitions=[[t.before,t.action_id,t.after] for t in sorted(p.transitions,key=lambda t:(t.before,t.action_id))]
    # Map avoids prototype-key collisions. Returned objects are fresh copies. No
    # caller can mutate the internal oracle through exported references.
    return (game_header(p.game_id)+
      'const rows: [string, [string,string][]][] = '+literal(states)+';\n'+
      'const edges: [string,string,string][] = '+literal(transitions)+';\n'+
      'const stateValues = new Map(rows);\n'+
      'const transitionMap = new Map<string, Map<string,string>>();\n'+
      'for (const [before,action,after] of edges) {\n'+
      '  if (!transitionMap.has(before)) transitionMap.set(before,new Map());\n'+
      '  transitionMap.get(before)!.set(action,after);\n}\n'+
      'export const initialState: string = '+literal(p.initial_state)+';\n'+
      'export function observe(state: string): Record<string,string> {\n'+
      '  const values=stateValues.get(state);\n'+
      '  if (!values) throw new Error("UNKNOWN_STATE");\n'+
      '  return Object.fromEntries(values);\n}\n'+
      'export function step(state: string, action: string): string {\n'+
      '  if (!stateValues.has(state)) throw new Error("UNKNOWN_STATE");\n'+
      '  const next=transitionMap.get(state)?.get(action);\n'+
      '  if (next===undefined) throw new Error("UNDEFINED_TRANSITION");\n'+
      '  return next;\n}\n').encode('utf-8')
