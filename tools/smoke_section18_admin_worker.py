"""Separate real worker process + restart telemetry, safe synthetic source only."""
from pathlib import Path
import argparse,gc,json,os,secrets,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/productization/document_intelligence'))
from structural_pdf_fixtures import hierarchy_pdf_with_outline
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from apps.operator.service import Service

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--receipt',type=Path,required=True);a=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bie-app18-admin-smoke-') as tmp:
        token=secrets.token_hex(32);creds=Credentials();p=Principal('local-operator','local',PERMISSIONS,time.time()+3600);creds.grant(token,p)
        service=Service(Path(tmp),creds);cases=[]
        for label,data,expected in [('native_success',hierarchy_pdf_with_outline(),'ACKED'),
                ('native_empty_outline_title_negative',hierarchy_pdf_with_outline(((' ',0,None),)),'FAILED')]:
            source=service.import_pdf(p,data);assert source['validation']['status']=='VALID'
            run=service.create(p,source['source_id'],{},label)['run_id']
            r=subprocess.run([sys.executable,'-X','utf8','-B',str(ROOT/'scripts/run_bie_operator_worker.py'),
                '--data-root',tmp,'--run-id',run],cwd=ROOT,capture_output=True,text=True,timeout=45,
                env=dict(os.environ,BIE_OPERATOR_TOKEN=token,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1'))
            assert r.returncode==0;outcome=json.loads(r.stdout);assert outcome['outcome']==expected
            restarted=Service(Path(tmp),creds);status=restarted.status(p,run)
            workers=restarted.administration.workers(p)['items'];w=next(w for w in workers if w['run_id']==run)
            assert w['outcome']==expected and w['lifecycle']=='STOPPED' and w['active_tasks']==0
            assert status['queue_state']==('ACKED' if expected=='ACKED' else 'DEAD_LETTER')
            cases.append(dict(scenario=label,outcome=expected,status=status['status'],queue=status['queue_state'],
                worker_lifecycle=w['lifecycle'],persisted_after_process_restart=True,source_identity_verified=True))
        gc.collect()
    receipt=dict(passed=True,separate_process=True,processes_finished=True,cases=cases,new_distinct_test_methods=0,
        provider_calls_performed=False,synthetic_source=True,real_book_acceptance=False,product_accepted=False)
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
