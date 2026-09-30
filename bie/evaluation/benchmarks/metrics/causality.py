"""METRIC-006: declared linear structural causal models and do-interventions.

This checks fidelity to an explicitly supplied acyclic model, not empirical
identification, causal discovery or real-world causal validity.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError,ident
from ..domains.structured import amount,choice,record,sequence
from .common import indexed,no_extras,topological,unit,weight

def model(value):
    nodes=indexed(value,{'id','intercept','noise','parents'},lower=1);edges=[];terms={}
    for key,row in nodes.items():
        amount(row['intercept'],signed=True,maximum=10**6);amount(row['noise'],signed=True,maximum=10**6)
        parents={}
        for p in sequence(row['parents'],lower=0,upper=32):
            record(p, {'node','coefficient'});pid=ident(p['node'])
            if pid in parents:raise BenchmarkError('DUPLICATE_GRAPH_EDGE')
            coefficient=amount(p['coefficient'],signed=True,maximum=1000)
            if not coefficient:raise BenchmarkError('ZERO_COEFFICIENT_EDGE')
            parents[pid]=coefficient;edges.append((pid,key))
        terms[key]=parents
    order=topological(nodes,edges)
    return nodes,terms,order,set(edges)

def evaluate_model(nodes,terms,order,interventions):
    if type(interventions) is not dict or len(interventions)>128:raise BenchmarkError('INVALID_INTERVENTIONS')
    for key,val in interventions.items():
        ident(key)
        if key not in nodes:raise BenchmarkError('UNKNOWN_INTERVENTION_NODE')
        amount(val,signed=True,maximum=10**6)
    values={}
    for key in order:
        if key in interventions:val=amount(interventions[key],signed=True,maximum=10**6)
        else:
            r=nodes[key];val=amount(r['intercept'],signed=True)+amount(r['noise'],signed=True)
            val+=sum(c*values[p] for p,c in terms[key].items())
        if val.numerator.bit_length()>512 or val.denominator.bit_length()>512 or abs(val)>10**30:
            raise BenchmarkError('MODEL_MAGNITUDE_LIMIT')
        values[key]=val
    return values

def measure(reference,candidate,artifacts):
    record(reference, {'model','queries'});record(candidate, {'edges','queries'})
    nodes,terms,order,edges=model(reference['model']);reported=[]
    for row in sequence(candidate['edges'],lower=0,upper=256):
        record(row, {'from','to'});a,b=ident(row['from']),ident(row['to'])
        if a not in nodes or b not in nodes:raise BenchmarkError('UNKNOWN_CANDIDATE_NODE')
        reported.append((a,b))
    if len(set(reported))!=len(reported):raise BenchmarkError('DUPLICATE_GRAPH_EDGE')
    reported=set(reported);units=[];defects=[]
    for a,b in sorted(edges):
        ok=(a,b) in reported
        units.append(unit('edge:'+a+':'+b,1,1 if ok else 0,[] if ok else ['CAUSAL_EDGE_MISSING_OR_REVERSED']))
    for a,b in sorted(reported-edges):defects.append({'id':'edge:'+a+':'+b,'reason':'UNSUPPORTED_CAUSAL_EDGE'})
    refs=indexed(reference['queries'],{'id','weight','interventions','target','inference_kind'},lower=1)
    acts=indexed(candidate['queries'],{'id','value','inference_kind'});no_extras(acts,refs)
    for key,row in sorted(refs.items()):
        weight(row);target=ident(row['target']);kind=choice(row['inference_kind'],{'intervention','counterfactual_fixed_noise'})
        if target not in nodes:raise BenchmarkError('UNKNOWN_REFERENCE_NODE')
        expected=evaluate_model(nodes,terms,order,row['interventions'])[target];a=acts.get(key);reasons=[]
        if a is None:reasons=['MISSING_CAUSAL_QUERY']
        else:
            actual=amount(a['value'],signed=True,maximum=10**30)
            choice(a['inference_kind'],{'intervention','counterfactual_fixed_noise','association'})
            if actual!=expected:reasons.append('INTERVENTION_VALUE_MISMATCH')
            if a['inference_kind']!=kind:reasons.append('INFERENCE_KIND_MISMATCH')
        units.append(unit('query:'+key,weight(row),0 if reasons else 1,reasons))
    return units,defects,{'assessment_scope':'DECLARED_LINEAR_SCM_FIXED_NOISE_NOT_EMPIRICAL_IDENTIFICATION',
                         'independent_causal_validation':False}
