"""HIST-002: annotated causal argument constraints, not an automated historian.

The input dossier is authored/curated evidence metadata, never proof of source
truth. A sequence does not establish causation; annotations cannot prove sole,
necessary or sufficient causes. All outcomes preserve human/source-review gates.
"""
from __future__ import annotations
from ..models import BenchmarkError, ident
from .structured import choice, record, sequence, unique_ids
from .temporal import date_interval, relation


def assess(data: dict) -> dict:
    record(data, {'cause','effect','relation_claim','evidence','alternatives_considered'})
    nodes=[]
    for role in ('cause','effect'):
        node=record(data[role],{'id','date'})
        nodes.append((ident(node['id']),date_interval(node['date'])))
    (cause,cdate),(effect,edate)=nodes
    if cause==effect:raise BenchmarkError('SELF_CAUSATION')
    claim=choice(data['relation_claim'],{'contributes_to','necessary','sufficient','sole_cause'})
    alternatives=unique_ids(data['alternatives_considered'],lower=0,upper=16)
    if cause in alternatives or effect in alternatives:raise BenchmarkError('ALTERNATIVE_REPEATS_ENDPOINT')
    evidence=sequence(data['evidence'],lower=0,upper=32);seen=set();kinds=set()
    for item in evidence:
        record(item, {'id','cause_id','effect_id','kind','source_ref'})
        key=ident(item['id']);ident(item['source_ref'])
        if key in seen:raise BenchmarkError('DUPLICATE_EVIDENCE')
        seen.add(key)
        if item['cause_id']!=cause or item['effect_id']!=effect:
            raise BenchmarkError('EVIDENCE_ENDPOINT_MISMATCH')
        kinds.add(choice(item['kind'],{'temporal_record','mechanism_account','source_interpretation','counter_evidence'}))
    order=relation(cdate,edate);issues=[]
    if order=='AFTER':issues.append('TEMPORAL_REVERSAL')
    elif order!='BEFORE':issues.append('TIME_ORDER_UNRESOLVED')
    if not evidence:issues.append('NO_EVIDENCE')
    if not kinds.intersection({'mechanism_account','source_interpretation'}):
        issues.append('SEQUENCE_ALONE_DOES_NOT_ESTABLISH_CAUSATION')
    if claim!='contributes_to':issues.append('OVERSTRONG_CAUSAL_CLAIM')
    if not alternatives:issues.append('ALTERNATIVES_NOT_CONSIDERED')
    if 'counter_evidence' in kinds:issues.append('COUNTEREVIDENCE_REQUIRES_REVIEW')
    return {'status':'REVIEW_REQUIRED' if issues else 'ANNOTATED_INTERPRETATION_STRUCTURALLY_SUPPORTED',
            'time_relation':order,'issues':issues,'evidence_ids':sorted(seen),
            'causality_proven':False,'annotations_independently_verified':False,
            'profile':'ANNOTATED_ARGUMENT_AUDIT_NOT_SOURCE_VERIFICATION'}


def solve(data: dict) -> dict:
    if type(data) is not dict:raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='assess_link':
        record(data, {'op','cause','effect','relation_claim','evidence','alternatives_considered'})
        return assess({k:v for k,v in data.items() if k!='op'})
    if op=='audit_graph':
        record(data, {'op','links'})
        links=sequence(data['links'],upper=32)
        nodes={};pairs=set();adj={};results=[]
        for link in links:
            result=assess(link)
            a,b=link['cause']['id'],link['effect']['id']
            if (a,b) in pairs:raise BenchmarkError('DUPLICATE_CAUSAL_EDGE')
            pairs.add((a,b));adj.setdefault(a,set()).add(b);adj.setdefault(b,set())
            for name in ('cause','effect'):
                key=link[name]['id'];interval=date_interval(link[name]['date'])
                if key in nodes and nodes[key]!=interval:raise BenchmarkError('CONFLICTING_EVENT_DATES')
                nodes[key]=interval
            results.append({'cause_id':a,'effect_id':b,'assessment':result})
        active=set();done=set()
        def visit(node):
            if node in active:return True
            if node in done:return False
            active.add(node)
            cyclic=any(visit(v) for v in sorted(adj[node]))
            active.remove(node);done.add(node)
            return cyclic
        cyclic=any(visit(k) for k in sorted(nodes))
        return {'cycle_detected':cyclic,'links':sorted(results,key=lambda r:(r['cause_id'],r['effect_id'])),
                'review_required':cyclic or any(r['assessment']['issues'] for r in results),
                'causality_proven':False,'profile':'ANNOTATED_CAUSAL_GRAPH_ONLY'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
