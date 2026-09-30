"""Operator-only release evaluation CLI. Never accept raw candidate-owned scores.

Keys are read from explicitly named environment variables, never from packaged
fixtures by default. The default empty trust store cannot authorize production.
"""
from __future__ import annotations
import argparse,json,os,base64,time,sys
from pathlib import Path
from ..models import BenchmarkError,strict_loads,exact_fields
from .ledger import ReleaseLedger

def read_json(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>2000000:raise BenchmarkError('INVALID_INPUT_FILE')
    return strict_loads(p.read_bytes())

def load_trust(path):
    if path is None:return {}
    metadata=read_json(path)
    if type(metadata) is not dict:raise BenchmarkError('INVALID_TRUST_METADATA')
    result={}
    for key,row in metadata.items():
        exact_fields(row,{'secret_env','subject_id','roles','not_before','expires_at','revoked','fixture_only'})
        name=row['secret_env']
        if type(name) is not str or not name.startswith('BIE_ATTEST_') or not name.replace('_','').isalnum():
            raise BenchmarkError('INVALID_SECRET_ENV_NAME')
        if name not in os.environ:raise BenchmarkError('ATTESTATION_SECRET_UNAVAILABLE')
        try:secret=base64.b64decode(os.environ[name],validate=True)
        except (ValueError,TypeError) as exc:raise BenchmarkError('INVALID_SECRET_ENCODING') from exc
        if len(secret)<32:raise BenchmarkError('WEAK_ATTESTATION_KEY')
        result[key]={k:v for k,v in row.items() if k!='secret_env'};result[key]['secret']=secret
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['manifest','policy','assessments','manifest-sha256','policy-sha256','database','campaign-id','attempt-id','output-dir']:
        p.add_argument('--'+name,required=True)
    p.add_argument('--attestations');p.add_argument('--artifact-evidence');p.add_argument('--trust-metadata')
    a=p.parse_args(argv)
    try:
        out=Path(a.output_dir)
        if out.exists() or out.is_symlink():raise BenchmarkError('OUTPUT_ALREADY_EXISTS')
        m=read_json(a.manifest);policy=read_json(a.policy);rows=read_json(a.assessments)
        trust=load_trust(a.trust_metadata)
        with ReleaseLedger(a.database) as ledger:
            receipt=ledger.execute(campaign_id=a.campaign_id,attempt_id=a.attempt_id,manifest=m,policy=policy,assessments=rows,
                expected_manifest_sha256=a.manifest_sha256,expected_policy_sha256=a.policy_sha256,
                attestations=[] if a.attestations is None else read_json(a.attestations),trust=trust,
                artifacts={} if a.artifact_evidence is None else read_json(a.artifact_evidence),now=int(time.time()))
            if ledger.get(a.attempt_id)!=receipt:raise BenchmarkError('PERSISTENCE_ROUNDTRIP_FAILED')
        out.mkdir(parents=True,exist_ok=False)
        (out/'RELEASE_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps({'outcome':receipt['report']['outcome'],'product_accepted':False,'release_authorized':False}))
        return 0 if receipt['report']['outcome'] in {'PASS','DIAGNOSTIC_PASS'} else 2
    except (BenchmarkError,OSError) as exc:
        print(json.dumps({'outcome':'BLOCKED','error':exc.code if isinstance(exc,BenchmarkError) else 'IO_ERROR'}),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
