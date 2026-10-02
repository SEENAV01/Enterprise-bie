"""Read existing real inspection via new administrative windows, no source copy."""
from pathlib import Path
import argparse,hashlib,json,secrets,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from apps.operator.service import Service
from apps.operator.main import create_app
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from fastapi.testclient import TestClient

def main():
    p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    expected='8fbe1357179b364824d97861152a31055c45b87177198b40f39c98f726e06857'
    assert hashlib.sha256(a.pdf.read_bytes()).hexdigest()==expected,'REAL_SOURCE_HASH_CHANGED'
    creds=Credentials();token=secrets.token_hex(32);p=Principal('validation','money-validation',PERMISSIONS,time.time()+3600);creds.grant(token,p)
    service=Service(a.data_root,creds);headers={'Authorization':'Bearer '+token}
    run=service.list_runs(p)['items'][0]['run_id'];assert service.status(p,run)['status']=='SUCCEEDED'
    with TestClient(create_app(service),base_url='http://localhost') as client:
        first=client.get('/operator/v1/runs/'+run+'/result',headers=headers);second=client.get('/operator/v1/runs/'+run+'/result',headers=headers)
        assert first.status_code==second.status_code==200 and first.content==second.content
        result=first.json();assert result['source_hash']==expected and result['page_count']==20 and result['total_blocks']==755
        assert result['materialized_chapter_count']==1 and result['materialized_section_count']==result['materialized_subsection_count']==0
        assert result['native_outline_entry_count']==0 and result['outline_status']=='no_native_outline'
        response=client.get('/operator/v1/admin/queue?state=ACKED',headers=headers);assert response.status_code==200
        queue=response.json();q=next(q for q in queue['items'] if q['run_id']==run);assert q['source_hash']==expected
        providers=client.get('/operator/v1/admin/providers',headers=headers).json();assert providers['status']=='NOT_CONFIGURED'
        dlq=client.get('/operator/v1/admin/queue?state=DEAD_LETTER',headers=headers).json();assert dlq['items']==[]
        # Record one controlled terminal no-op, not a fabricated new inspection.
        assert service.work_once(p,run)['outcome']=='TERMINAL'
        workers=client.get('/operator/v1/admin/workers',headers=headers).json();assert workers['items'] and all(w['lifecycle']=='STOPPED' for w in workers['items'])
        for kind in ('gates','repairs'):
            r=client.get('/operator/v1/runs/'+run+'/assurance/'+kind,headers=headers);assert r.json()['status']=='NOT_RUN'
    receipt=dict(passed=True,real_book_executed_at_prior_verified_checkpoint=True,new_learning_execution=False,
        source_hash_match=True,result_http=200,page_count=20,total_blocks=755,chapters=1,sections=0,subsections=0,native_outline_count=0,
        outline_status='no_native_outline',second_safe_result_identical=True,actual_queue_state='ACKED',actual_source_link_verified=True,
        provider_status='NOT_CONFIGURED',live_provider_calls=False,worker_telemetry_outcome='TERMINAL_NOOP',worker_lifecycle='STOPPED',
        dead_letters=0,real_assurance_states={'gates':'NOT_RUN','repairs':'NOT_RUN'},fixture_substituted=False,
        raw_text_persisted=False,real_pdf_new_copy_created=False,background_storage_sync_exclusion='NOT_ATTESTED',product_accepted=False)
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
