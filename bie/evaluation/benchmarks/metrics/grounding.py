"""METRIC-001: exact claim/span binding against trusted captured text.

This evaluates a curated proposition-to-span annotation, NOT automatic textual
entailment. Source hashes and Unicode offsets prove binding, not truth.
"""
from __future__ import annotations
import hashlib
from ..models import BenchmarkError, digest_string, ident, text
from ..domains.structured import record, sequence
from .common import exact,indexed,no_extras,scalar,unit,weight

def text_sha(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()

def proposition(value):
    record(value, {'subject','predicate','object'})
    ident(value['subject']);ident(value['predicate']);scalar(value['object'])
    return value

def span(value,sources,artifacts,*,reference):
    record(value, {'source_id','start','end','span_sha256'} if reference else {'source_id','start','end'})
    sid=ident(value['source_id']);start,end=value['start'],value['end']
    if sid not in sources:raise BenchmarkError('UNKNOWN_SOURCE')
    if type(start) is not int or type(end) is not int or not 0<=start<end<=len(artifacts[sid]):
        raise BenchmarkError('INVALID_SOURCE_SPAN')
    if reference and digest_string(value['span_sha256'])!=text_sha(artifacts[sid][start:end]):
        raise BenchmarkError('REFERENCE_SPAN_HASH_MISMATCH')
    return sid,start,end

def measure(reference,candidate,artifacts):
    record(reference, {'sources','claims'});record(candidate, {'claims'})
    sources=indexed(reference['sources'],{'id','text_sha256','locator'},lower=1)
    if set(artifacts)!=set(sources):raise BenchmarkError('SOURCE_ARTIFACT_ROSTER_MISMATCH')
    for sid,row in sources.items():
        text(row['locator']);text(artifacts[sid],maximum=1000000)
        if digest_string(row['text_sha256'])!=text_sha(artifacts[sid]):raise BenchmarkError('SOURCE_ARTIFACT_HASH_MISMATCH')
    refs=indexed(reference['claims'],{'id','weight','proposition','supports'},lower=1)
    acts=indexed(candidate['claims'],{'id','proposition','citations'});no_extras(acts,refs)
    units=[]
    for key,row in sorted(refs.items()):
        w=weight(row);proposition(row['proposition'])
        allowed=[span(s,sources,artifacts,reference=True) for s in sequence(row['supports'])]
        if len(set(allowed))!=len(allowed):raise BenchmarkError('DUPLICATE_REFERENCE_SPAN')
        reasons=[];a=acts.get(key)
        if a is None:reasons=['MISSING_CLAIM']
        else:
            proposition(a['proposition'])
            if not exact(a['proposition'],row['proposition']):reasons.append('PROPOSITION_MISMATCH')
            cited=[span(s,sources,artifacts,reference=False) for s in sequence(a['citations'],lower=0)]
            if not cited:reasons.append('UNCITED_CLAIM')
            if len(set(cited))!=len(cited):raise BenchmarkError('DUPLICATE_CITATION')
            if any(s not in allowed for s in cited):reasons.append('CITATION_NOT_ANNOTATED_SUPPORT')
        units.append(unit(key,w,0 if reasons else 1,reasons))
    return units,[],{'assessment_scope':'CURATED_PROPOSITION_AND_EXACT_SPAN_BINDING','automatic_entailment':False,
                     'captured_source_hashes':{k:v['text_sha256'] for k,v in sorted(sources.items())}}
