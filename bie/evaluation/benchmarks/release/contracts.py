"""Strict candidate/reference bindings shared by raters and release gates.

Assessment digests provide content integrity, not authentication. Only an operator-
controlled evaluator service may admit them to its ledger. Production authorization
uses separate keyed attestations and must not trust candidate-authored JSON.
"""
from __future__ import annotations
from copy import deepcopy
from fractions import Fraction
from ..models import BenchmarkError, canonical_json, digest, digest_string, exact_fields, ident, text
from ..domains.structured import amount, choice, sequence, unique_ids

CONTEXT_FIELDS = {'run_id','case_id','domain','metric_id','candidate_sha256',
                  'reference_sha256','rubric_sha256','dataset_sha256','environment_sha256','split'}
KINDS = {'DETERMINISTIC','MODEL','HUMAN'}

def bounded_int(value, lower=0, upper=2**53-1):
    if type(value) is not int or not lower <= value <= upper:
        raise BenchmarkError('INVALID_INTEGER')
    return value

def score(value):
    q = amount(value)
    if q > 1: raise BenchmarkError('SCORE_OUT_OF_RANGE')
    return q

def context(value):
    canonical_json(value); exact_fields(value, CONTEXT_FIELDS)
    for k in CONTEXT_FIELDS:
        if k.endswith('_sha256'): digest_string(value[k])
        elif k == 'split': choice(value[k], {'DEVELOPMENT','CALIBRATION','HOLDOUT'})
        else: ident(value[k])
    if value['metric_id'] not in {f'BIE-EVAL-METRIC-{i:03}' for i in range(1,18)}:
        raise BenchmarkError('UNKNOWN_METRIC')
    return deepcopy(value)

def pinned(value, expected):
    if digest(value) != digest_string(expected): raise BenchmarkError('SNAPSHOT_MISMATCH')
    return value

def make_assessment(ctx, assessor_id, kind, value, *, status='MEASURED', reasons=(),
                    evidence=None, execution='LOCAL', assessor_version='1.0.0'):
    ctx=context(ctx); ident(assessor_id); choice(kind,KINDS)
    choice(status,{'MEASURED','BLOCKED'}); choice(execution,{'LOCAL','ADAPTER','HUMAN_ATTESTATION','FIXTURE'})
    ident(assessor_version); value=score(value)
    reasons=sorted(set(ident(r) for r in reasons))
    if status=='BLOCKED' and (value!=0 or not reasons): raise BenchmarkError('INVALID_BLOCKED_ASSESSMENT')
    evidence={} if evidence is None else evidence; canonical_json(evidence)
    row={'schema_version':'1.0.0','context':ctx,'assessor_id':assessor_id,'kind':kind,
         'assessor_version':assessor_version,'status':status,'score_exact':str(value),
         'reasons':reasons,'evidence':deepcopy(evidence),'execution':execution,
         'release_authorized':False,'product_accepted':False}
    row['assessment_sha256']=digest(row)
    return row

def assessment(row, expected_context=None):
    exact_fields(row,{'schema_version','context','assessor_id','kind','assessor_version','status',
                      'score_exact','reasons','evidence','execution','release_authorized',
                      'product_accepted','assessment_sha256'})
    choice(row['schema_version'],{'1.0.0'}); context(row['context']); ident(row['assessor_id'])
    choice(row['kind'],KINDS); ident(row['assessor_version']); choice(row['status'],{'MEASURED','BLOCKED'})
    choice(row['execution'],{'LOCAL','ADAPTER','HUMAN_ATTESTATION','FIXTURE'}); score(row['score_exact'])
    unique_ids(row['reasons'],lower=0,upper=128); canonical_json(row['evidence'])
    if row['release_authorized'] is not False or row['product_accepted'] is not False:
        raise BenchmarkError('UNAUTHORIZED_PROMOTION')
    if row['status']=='BLOCKED' and (score(row['score_exact'])!=0 or not row['reasons']):
        raise BenchmarkError('INVALID_BLOCKED_ASSESSMENT')
    if digest({k:v for k,v in row.items() if k!='assessment_sha256'}) != digest_string(row['assessment_sha256']):
        raise BenchmarkError('ASSESSMENT_INTEGRITY')
    if expected_context is not None and context(expected_context)!=row['context']:
        raise BenchmarkError('ASSESSMENT_CONTEXT_MISMATCH')
    return row

def keyed_rows(rows, fields, key='id', lower=0, upper=1000):
    out={}
    for row in sequence(rows,lower=lower,upper=upper):
        exact_fields(row,fields); k=ident(row[key])
        if k in out: raise BenchmarkError('DUPLICATE_ROW')
        out[k]=row
    return out

def gate_result(gate, reasons, **details):
    reasons=sorted(set(reasons))
    return {'gate':gate,'outcome':'FAIL' if reasons else 'PASS','reasons':reasons,
            **details,'release_authorized':False,'product_accepted':False}
