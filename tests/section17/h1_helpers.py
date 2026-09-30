import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

import hashlib
from bie.evaluation.benchmarks.release.auth import sign
from bie.evaluation.benchmarks.release.contracts import make_assessment
from bie.evaluation.benchmarks.release import gate
from batch005_helpers import cohort,NOW

def bundle_fixture():
    m,p,rows=cohort()
    bundle={'schema_version':'1.0.0','candidates':{r['context']['case_id']:None for r in m['cases']}}
    m['artifact_sha256']=digest(bundle)
    return m,p,rows,bundle

def production_fixture():
    # Synthetic policy/service-identity controls, not real human/golden/native evidence.
    m,p,_=cohort(all_metrics=True,production=True)
    base=m['cases'];m['cases']=[];rows=[]
    for domain in ('math','physics'):
        for i,r in enumerate(base,1):
            r=deepcopy(r);c=r['context'];c['domain']=domain;c['case_id']=f'{domain}-{i}'
            c['reference_sha256']=digest(f'{domain}-reference-{i}')
            r['leakage_group']=c['case_id'];m['cases'].append(r)
            for assessor,kind,exe in [('det','DETERMINISTIC','LOCAL'),('human','HUMAN','HUMAN_ATTESTATION')]:
                rows.append(make_assessment(c,assessor,kind,'1',execution=exe))
    bundle={'schema_version':'1.0.0','candidates':{r['context']['case_id']:None for r in m['cases']}}
    m['artifact_sha256']=digest(bundle)
    coverage={'schema_version':'1.0.0','domains':[{'id':d,'metrics':[{'id':f'BIE-EVAL-METRIC-{i:03}','minimum_groups':1} for i in range(1,18)]} for d in ('math','physics')]}
    trust={}
    for name,roles in [('det',['EVALUATOR_ASSESSMENT']),('human',['EVALUATOR_ASSESSMENT']),('authority',sorted(gate.PRODUCTION_ATTESTATIONS))]:
        trust[name]={'secret':hashlib.sha256(('SYNTHETIC-H1-TEST-ONLY-'+name).encode()).digest(),'subject_id':name,'roles':roles,
            'not_before':0,'expires_at':10000,'revoked':False,'fixture_only':False}
    tokens=[]
    for a in rows:
        who=a['assessor_id'];group=next(r['independence_group'] for r in p['aggregation']['raters'] if r['id']==who)
        claims={'assessment_sha256':a['assessment_sha256'],'kind':a['kind'],'assessor_version':a['assessor_version'],'independence_group':group}
        tokens.append(sign_h1(trust,who,'EVALUATOR_ASSESSMENT',a['assessment_sha256'],claims))
    return m,p,rows,bundle,coverage,trust,tokens

def sign_h1(trust,key,kind,scope,claims):
    return sign({'schema_version':'1.0.0','kind':kind,'subject_id':trust[key]['subject_id'],'key_id':key,
                 'issued_at':900,'expires_at':2000,'nonce':'synthetic-h1','scope_sha256':scope,'claims':claims},trust[key]['secret'])

def gate_fixture_args(fixture=None):
    m,p,rows,b,c,tr,tokens=production_fixture() if fixture is None else fixture
    bindings=gate.production_input_bindings(b,c,tokens)
    scope=gate.evidence_scope(m,p,rows,production_inputs=bindings)
    blob={'SYNTHETIC_TEST_ONLY':True,'native_run':False,'real_reviewer':False}
    artifacts={digest(blob):blob}
    attestations=[sign_h1(tr,'authority',kind,scope,{'outcome':'PASS','evidence_sha256':digest(blob)}) for kind in p['required_attestations']]
    return {'manifest':m,'policy':p,'assessments':rows,'candidate_bundle':b,'coverage_contract':c,
            'expected_coverage_sha256':digest(c),'trust':tr,'assessment_tokens':tokens,'now':NOW,
            'expected_manifest_sha256':digest(m),'expected_policy_sha256':digest(p),
            'attestations':attestations,'artifacts':artifacts}
