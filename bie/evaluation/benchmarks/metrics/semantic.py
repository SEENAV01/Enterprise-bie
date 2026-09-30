"""METRIC-002: typed concept/facet/relationship coverage, not free-text NLP."""
from ..models import BenchmarkError, ident
from ..domains.structured import record
from .common import exact,indexed,no_extras,scalar,unit,weight
from fractions import Fraction

def facets(value):
    if type(value) is not dict or not 1<=len(value)<=64:raise BenchmarkError('INVALID_FACETS')
    for k,v in value.items():ident(k);scalar(v)
    return value

def measure(reference,candidate,artifacts):
    record(reference, {'concepts','relations'});record(candidate, {'concepts','relations'})
    refs=indexed(reference['concepts'],{'id','weight','facets'},lower=1)
    rels=indexed(reference['relations'],{'id','weight','from','predicate','to'})
    if set(refs)&set(rels):raise BenchmarkError('DUPLICATE_METRIC_ITEM')
    acts=indexed(candidate['concepts'],{'id','facets'});ars=indexed(candidate['relations'],{'id','from','predicate','to'})
    no_extras(acts,refs);no_extras(ars,rels);units=[]
    for key,row in sorted(refs.items()):
        w=weight(row);f=facets(row['facets']);a=acts.get(key);reasons=[];matched=0
        if a is None:reasons=['MISSING_CONCEPT']
        else:
            # Empty facet maps are a measurable omission, not successful concepts.
            af=a['facets']
            if type(af) is not dict or len(af)>64:raise BenchmarkError('INVALID_FACETS')
            for k,v in af.items():ident(k);scalar(v)
            if set(af)-set(f):reasons.append('UNEXPECTED_FACET')
            for k,v in sorted(f.items()):
                if k not in af:reasons.append('MISSING_FACET:'+k)
                elif not exact(v,af[k]):reasons.append('INCORRECT_FACET:'+k)
                else:matched+=1
        units.append(unit(key,w,Fraction(matched,len(f)),reasons))
    for key,row in sorted(rels.items()):
        w=weight(row)
        for k in ('from','predicate','to'):ident(row[k])
        if row['from'] not in refs or row['to'] not in refs:raise BenchmarkError('UNKNOWN_REFERENCE_CONCEPT')
        a=ars.get(key);reasons=[]
        if a is None:reasons=['MISSING_RELATION']
        else:
            for k in ('from','predicate','to'):ident(a[k])
            if any(row[k]!=a[k] for k in ('from','predicate','to')):reasons=['RELATION_MISMATCH']
            elif row['from'] not in acts or row['to'] not in acts:reasons=['RELATION_ENDPOINT_NOT_TAUGHT']
        units.append(unit(key,w,0 if reasons else 1,reasons))
    return units,[],{'assessment_scope':'TRUSTED_CONCEPT_IDS_TYPED_FACETS_AND_RELATIONS','natural_language_semantics':False}
