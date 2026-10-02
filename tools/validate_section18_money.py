"""Authorized real-book inspection lane; never logs book text or stores it in ZIPs."""
from pathlib import Path
import hashlib,json,secrets,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service
from apps.operator.main import create_app
from fastapi.testclient import TestClient

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True)
    p.add_argument('--data-root',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    expected='8fbe1357179b364824d97861152a31055c45b87177198b40f39c98f726e06857'
    raw=a.pdf.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected,'REAL_SOURCE_HASH_CHANGED'
    c=Credentials();token=secrets.token_hex(32);principal=Principal('validation','money-validation',PERMISSIONS,time.time()+3600);c.grant(token,principal)
    service=Service(a.data_root,c);headers={'Authorization':'Bearer '+token}
    with TestClient(create_app(service),base_url='http://localhost') as client:
        source=client.post('/operator/v1/sources',content=raw,headers={**headers,'Content-Type':'application/pdf'})
        assert source.status_code==200 and source.json()['validation']['status']=='VALID'
        submit=client.post('/operator/v1/runs',json=dict(source_id=source.json()['source_id'],config={},idempotency_key='real-money-section18'),headers=headers)
        assert submit.status_code==202;run=submit.json()['run_id']
        initial=client.get('/operator/v1/runs/'+run,headers=headers).json()
        restart=Service(a.data_root,c).status(principal,run)
        assert initial==restart
        outcome=service.work_once(principal,run)
        assert outcome['outcome'] in ('ACKED','TERMINAL')
        state=client.get('/operator/v1/runs/'+run,headers=headers).json();assert state['status']=='SUCCEEDED'
        first=client.get('/operator/v1/runs/'+run+'/result',headers=headers);second=client.get('/operator/v1/runs/'+run+'/result',headers=headers)
        assert first.status_code==second.status_code==200 and first.content==second.content
        r=first.json();assert r['source_hash']==expected and r['page_count']==20 and r['total_blocks']==755
        assert r['materialized_chapter_count']==1 and r['materialized_section_count']==r['materialized_subsection_count']==0
        assert r['native_outline_entry_count']==0 and r['outline_status']=='no_native_outline'
        keys=set()
        def visit(v):
            if type(v) is dict:
                keys.update(v)
                for x in v.values():visit(x)
            elif type(v) is list:
                for x in v:visit(x)
        visit(r);assert not keys.intersection({'text','title','body_text','heading_text','outline_title'})
        timeline=client.get('/operator/v1/runs/'+run+'/timeline',headers=headers).json()
    receipt=dict(schema='bie.section18.real-inspection/1',source_hash=expected,source_hash_matched=True,
       source_validation='VALID',submission_http=202,initial_status=initial['status'],restart_preserved=True,
       worker_outcome=outcome['outcome'],final_status=state['status'],result_http=200,page_count=r['page_count'],
       total_blocks=r['total_blocks'],chapters=1,sections=0,subsections=0,native_outline_count=0,
       outline_status=r['outline_status'],second_result_byte_identical=True,
       canonical_event_count=sum(e['event_origin']=='CANONICAL_PERSISTENCE' for e in timeline['items']),
       source_pdf_persistence='PRIVATE_LOCAL_VALIDATION_CAS_ONLY',raw_text_exposed=False,
       graph_execution='NOT_RUN_NO_REAL_KI_PRODUCER_BOUND',learning_video='NOT_RUN',learning_game='NOT_RUN',
       product_accepted=False,section_complete=False)
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
