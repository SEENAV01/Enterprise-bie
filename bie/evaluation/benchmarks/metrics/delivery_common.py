"""Bounded delivery metrics. All thresholds belong to the trusted reference.

Metadata profiles do not certify what a viewer or learner actually experienced.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError, ident, text, digest, digest_string
from ..domains.structured import amount, record, sequence, probability
from .common import ids, indexed, unit, weight

def integer(value, low=0, high=1000000):
    if type(value) is not int or not low <= value <= high:
        raise BenchmarkError('INTEGER_OUT_OF_PROFILE')
    return value

def boolean(value):
    if type(value) is not bool: raise BenchmarkError('BOOLEAN_REQUIRED')
    return value

def interval(row, duration, start='start', end='end'):
    a=integer(row[start],0,duration); b=integer(row[end],0,duration)
    if a>=b: raise BenchmarkError('EMPTY_OR_REVERSED_INTERVAL')
    return a,b

def unknown(actual, expected):
    if set(actual)-set(expected): raise BenchmarkError('UNKNOWN_CANDIDATE_ITEM')

def result_unit(key,reasons,w=1):
    return unit(key,w,0 if reasons else 1,reasons)

def defect(key,reason): return {'id':ident(key),'reason':reason}

def overlaps(a,b): return max(a[0],b[0]) < min(a[1],b[1])

def covered(start,end,ranges,max_gap=0):
    cursor=start
    for a,b in sorted(ranges):
        if b<=cursor or a>=end: continue
        if a>cursor+max_gap: return False
        cursor=max(cursor,b)
    return cursor+max_gap>=end

def observation(artifacts, key, kind, subject=None):
    """Validate evaluator-owned evidence, NOT a signature or identity system.

    Only an isolated trusted collector may populate the artifacts argument.
    Never bind an end-user request body directly to it in production.
    """
    ident(key)
    if key not in artifacts: raise BenchmarkError('TRUSTED_OBSERVATION_MISSING')
    o=artifacts[key]
    record(o,{'schema_version','kind','collector_id','run_id','subject_sha256','facts','receipt_sha256'})
    if o['schema_version']!='1.0.0' or o['kind']!=kind or o['collector_id']!='bie-local-collector-v1':
        raise BenchmarkError('OBSERVATION_PROFILE_MISMATCH')
    ident(o['run_id']);digest_string(o['subject_sha256']);digest_string(o['receipt_sha256'])
    if digest({k:v for k,v in o.items() if k!='receipt_sha256'})!=o['receipt_sha256']:
        raise BenchmarkError('OBSERVATION_HASH_MISMATCH')
    if subject is not None and digest_string(subject)!=o['subject_sha256']:
        raise BenchmarkError('OBSERVATION_SUBJECT_MISMATCH')
    return o

def used_artifacts(artifacts,used):
    if set(artifacts)!=set(used): raise BenchmarkError('UNUSED_OR_MISSING_OBSERVATIONS')

def seal(kind,run_id,subject,facts):
    ident(run_id);digest_string(subject)
    o={'schema_version':'1.0.0','kind':kind,'collector_id':'bie-local-collector-v1',
       'run_id':run_id,'subject_sha256':subject,'facts':facts}
    o['receipt_sha256']=digest(o)
    return o
