"""Shared strict, bounded metric contracts; no candidate-owned pass flags."""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError, canonical_json, ident, text
from ..domains.structured import amount, record, sequence

def indexed(value,fields,*,lower=0,upper=128):
    rows=sequence(value,lower=lower,upper=upper);out={}
    for row in rows:
        record(row,fields);key=ident(row['id'])
        if key in out:raise BenchmarkError('DUPLICATE_METRIC_ITEM')
        out[key]=row
    return out

def ids(value,*,lower=0):
    vals=[ident(x) for x in sequence(value,lower=lower,upper=128)]
    if len(set(vals))!=len(vals):raise BenchmarkError('DUPLICATE_METRIC_ITEM')
    return vals

def weight(row):return amount(row['weight'],positive=True,maximum=1000000)

def scalar(value):
    if type(value) not in (str,int,float,bool) or (type(value) is str and not value.strip()):
        raise BenchmarkError('INVALID_PROPOSITION_VALUE')
    canonical_json(value)
    return value

def exact(a,b):return canonical_json(a)==canonical_json(b)

def unit(key,w,earned,reasons):
    ident(key);w=amount(w,positive=True,maximum=1000000)
    earned=amount(earned)
    if earned>1:raise BenchmarkError('INVALID_METRIC_CREDIT')
    return {'id':key,'weight':str(w),'credit':str(earned),'reasons':sorted(set(reasons))}

def no_extras(actual,expected):
    if set(actual)-set(expected):raise BenchmarkError('UNEXPECTED_METRIC_ITEM')

def topological(nodes,edges):
    nodes=set(nodes);adj={n:[] for n in nodes};degree={n:0 for n in nodes};seen=set()
    for a,b in edges:
        if a not in nodes or b not in nodes or a==b:raise BenchmarkError('INVALID_GRAPH_EDGE')
        if (a,b) in seen:raise BenchmarkError('DUPLICATE_GRAPH_EDGE')
        seen.add((a,b));adj[a].append(b);degree[b]+=1
    ready=sorted(n for n in nodes if not degree[n]);order=[]
    while ready:
        n=ready.pop(0);order.append(n)
        for v in sorted(adj[n]):
            degree[v]-=1
            if degree[v]==0:ready.append(v);ready.sort()
    if len(order)!=len(nodes):raise BenchmarkError('CYCLIC_REFERENCE_GRAPH')
    return order
