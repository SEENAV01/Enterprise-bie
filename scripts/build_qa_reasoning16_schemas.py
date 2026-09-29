#!/usr/bin/env python3
"""Export closed structural schemas. Runtime codec enforces stricter semantics."""
from pathlib import Path
import dataclasses, json, sys, types, typing
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bie.qa.reasoning_v2.models import ReasoningRequest,ReasoningPolicy
from bie.qa.reasoning_v2.attestation import Review

def schema_for(cls):
    definitions={}
    def shape(t):
        origin=typing.get_origin(t);args=typing.get_args(t)
        if dataclasses.is_dataclass(t):
            key=t.__module__.replace('.','_')+'_'+t.__name__
            if key not in definitions:
                definitions[key]={}
                hints=typing.get_type_hints(t)
                props={f.name:shape(hints[f.name]) for f in dataclasses.fields(t)}
                definitions[key]={'type':'object','properties':props,'required':list(props),'additionalProperties':False}
                if t.__name__=='Expr':
                    props['op']={'enum':['atom','not','and','or','implies','iff']}
                    definitions[key]['allOf']=[
                      {'if':{'properties':{'op':{'const':'atom'}}},'then':{'properties':{'atom':{'minLength':1},'args':{'maxItems':0}}},
                       'else':{'properties':{'atom':{'const':''}}}},
                      {'if':{'properties':{'op':{'const':'not'}}},'then':{'properties':{'args':{'minItems':1,'maxItems':1}}}},
                      {'if':{'properties':{'op':{'enum':['and','or','implies','iff']}}},'then':{'properties':{'args':{'minItems':2,'maxItems':2}}}}]
            return {'$ref':'#/$defs/'+key}
        if origin in (typing.Union,types.UnionType):return {'anyOf':[shape(a) for a in args]}
        if origin is typing.Literal:return {'enum':list(args)}
        if origin in (tuple,list):
            return {'type':'array','items':shape(args[0]),'maxItems':8192}
        if t in (str,int,bool,float,type(None)):return {'type':{str:'string',int:'integer',bool:'boolean',float:'number',type(None):'null'}[t]}
        raise TypeError(f'Unsupported schema type: {t}')
    root=shape(cls)
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':cls.__name__+' — structural wire schema',
        'description':'Closed structural validation only. Use the strict runtime codec and evaluators for ranges, duplicate identities, graph scope, provenance, authority and resource limits.',**root,'$defs':definitions}

def main():
    dest=ROOT/'docs/qa_section16/batch004';dest.mkdir(parents=True,exist_ok=True)
    for cls,name in ((ReasoningRequest,'request.schema.json'),(ReasoningPolicy,'policy.schema.json'),(Review,'review.schema.json')):
        (dest/name).write_text(json.dumps(schema_for(cls),indent=2,ensure_ascii=False)+'\n')
    print('Generated three closed structural schemas. They do not replace runtime validation.')
if __name__=='__main__':main()
