"""Authenticate every production assessment; content hashes alone are insufficient.

Configured services sign exact assessments; this proves service custody, not
scientific correctness or real-world evaluator independence. Keep trust keys and
policy out of candidate access. Reused secrets cannot masquerade as independent
raters. Fixture execution/fixture keys never qualify for production admission.
"""
import hashlib
from ..models import BenchmarkError, digest, exact_fields
from ..domains.structured import sequence
from .contracts import assessment, keyed_rows
from .auth import verify


def verify_admission(assessments, policy, tokens, trust, *, now):
    roster = keyed_rows(policy['aggregation']['raters'], {'id','kind','independence_group'}, lower=1, upper=16)
    expected = {}
    for row in assessments:
        assessment(row)
        key = row['assessment_sha256']
        if key in expected:
            raise BenchmarkError('DUPLICATE_ASSESSMENT')
        expected[key] = row
    actual = {}
    for token in sequence(tokens, lower=0, upper=10000):
        exact_fields(token, {'payload','signature'})
        p = token['payload']
        if type(p) is not dict or p.get('scope_sha256') not in expected:
            raise BenchmarkError('UNEXPECTED_ASSESSMENT_AUTHORIZATION')
        key = p['scope_sha256']
        if key in actual:
            raise BenchmarkError('DUPLICATE_ASSESSMENT_AUTHORIZATION')
        actual[key] = token
    if set(actual) != set(expected):
        raise BenchmarkError('MISSING_ASSESSMENT_AUTHORIZATION')
    used_secrets = {}
    records = []
    for key, row in sorted(expected.items()):
        assessor = row['assessor_id']
        if assessor not in roster or row['kind'] != roster[assessor]['kind']:
            raise BenchmarkError('UNEXPECTED_RATER')
        allowed = {'DETERMINISTIC':'LOCAL','MODEL':'ADAPTER','HUMAN':'HUMAN_ATTESTATION'}
        if row['execution'] != allowed[row['kind']]:
            raise BenchmarkError('ASSESSMENT_EXECUTION_NOT_PRODUCTION')
        p = verify(actual[key], trust, kind='EVALUATOR_ASSESSMENT', scope_sha256=key, now=now, production=True)
        if p['subject_id'] != assessor:
            raise BenchmarkError('ASSESSMENT_SIGNER_MISMATCH')
        claims = {'assessment_sha256':key, 'kind':row['kind'], 'assessor_version':row['assessor_version'],
                  'independence_group':roster[assessor]['independence_group']}
        if p['claims'] != claims:
            raise BenchmarkError('ASSESSMENT_AUTHORIZATION_CLAIMS_MISMATCH')
        fingerprint = hashlib.sha256(trust[p['key_id']]['secret']).digest()
        if fingerprint in used_secrets and used_secrets[fingerprint] != assessor:
            raise BenchmarkError('RATER_SIGNING_KEY_REUSED')
        used_secrets[fingerprint] = assessor
        records.append({'assessment_sha256':key, 'authorization_sha256':digest(actual[key]), 'subject_id':assessor})
    return {'status':'VERIFIED', 'records':records, 'scientific_accuracy_certified':False}
