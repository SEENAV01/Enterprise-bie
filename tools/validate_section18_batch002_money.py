"""Recheck real persisted inspection; missing learning outputs remain NOT_RUN."""
from pathlib import Path
import sys,json,secrets,time,hashlib,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service
from apps.operator.main import create_app
from fastapi.testclient import TestClient
from apps.operator.view_contracts import KINDS
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pdf',type=Path,required=True)
    parser.add_argument('--data-root',type=Path,required=True);parser.add_argument('--receipt',type=Path,required=True);a=parser.parse_args()
    expected='8fbe1357179b364824d97861152a31055c45b87177198b40f39c98f726e06857'
    data=a.pdf.read_bytes();assert hashlib.sha256(data).hexdigest()==expected,'REAL_SOURCE_HASH_CHANGED'
    creds=Credentials();token=secrets.token_hex(32);p=Principal('validation','money-validation',PERMISSIONS,time.time()+3600);creds.grant(token,p)
    service=Service(a.data_root,creds);headers={'Authorization':'Bearer '+token}
    with TestClient(create_app(service),base_url='http://localhost') as client:
        source=client.post('/operator/v1/sources',content=data,headers={**headers,'Content-Type':'application/pdf'})
        assert source.status_code==200 and source.json()['validation']['status']=='VALID'
        submission=client.post('/operator/v1/runs',headers=headers,json=dict(source_id=source.json()['source_id'],config={},idempotency_key='real-money-section18'))
        assert submission.status_code==202;run=submission.json()['run_id'];prefix='/operator/v1/runs/'+run
        outcome=service.work_once(p,run);assert outcome['outcome'] in ('ACKED','TERMINAL')
        first=client.get(prefix+'/result',headers=headers);second=client.get(prefix+'/result',headers=headers)
        assert first.status_code==second.status_code==200 and first.content==second.content
        value=first.json();assert value['source_hash']==expected and value['page_count']==20 and value['total_blocks']==755
        assert value['materialized_chapter_count']==1 and value['native_outline_entry_count']==0
        missing={}
        for kind in KINDS:
            r=client.get(prefix+'/views/'+kind,headers=headers);assert r.status_code==200 and r.json()['status']=='NOT_RUN';missing[kind]='NOT_RUN'
        artifacts=client.get(prefix+'/artifacts',headers=headers);assert artifacts.status_code==200
        types=[x['artifact_type'] for x in artifacts.json()['items']]
        assert 'document.inspection.safe_json' in types and not any(x.startswith('operator.view.') for x in types)
        for row in artifacts.json()['items']:
            lineage=client.get(prefix+'/artifacts/'+row['artifact_id']+'/lineage',headers=headers);assert lineage.status_code==200
            assert lineage.json()['complete'] and all(n['integrity']=='VERIFIED' for n in lineage.json()['nodes'])
        assert client.get(prefix+'/artifacts/'+artifacts.json()['items'][0]['artifact_id']+'/content',headers=headers).status_code==404
    receipt=dict(source_hash=expected,source_hash_match=True,result_http=200,page_count=20,total_blocks=755,chapters=1,
        sections=value['materialized_section_count'],subsections=value['materialized_subsection_count'],native_outline_count=0,
        outline_status=value['outline_status'],second_safe_result_identical=True,artifact_types=sorted(types),
        actual_artifact_lineage_verified=True,missing_real_learning_artifacts=missing,
        synthetic_artifacts_substituted=False,raw_source_route_present=False,real_learning_production_executed=False,
        raw_text_persisted=False,source_pdf_persistence='PRIVATE_LOCAL_VALIDATION_CAS_ONLY',product_accepted=False)
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
