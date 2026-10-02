"""Actual Money HTTP recheck with truthful absence of evaluation/release proof."""
from pathlib import Path
import argparse,json,secrets,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import validate_section18_batch003_money as prior
from apps.operator.service import Service
from apps.operator.main import create_app
from apps.operator.contracts import Credentials,Principal,PERMISSIONS
from fastapi.testclient import TestClient
def main():
    p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    prior.main()
    credentials=Credentials();token=secrets.token_hex(32);principal=Principal('validation','money-validation',PERMISSIONS,time.time()+3600);credentials.grant(token,principal)
    service=Service(a.data_root,credentials);run=service.list_runs(principal,0,25)['items'][0]['run_id']
    states={}
    with TestClient(create_app(service),base_url='http://localhost') as client:
        for kind in ('benchmark','release'):
            r=client.get('/operator/v1/runs/'+run+'/quality/'+kind,headers={'Authorization':'Bearer '+token})
            assert r.status_code==200 and r.json()['status']=='NOT_RUN' and not r.json()['items'];states[kind]='NOT_RUN'
    receipt=json.loads(a.receipt.read_text());receipt.update(real_quality_states=states,real_benchmark_or_release_substituted=False,
        live_independent_assessment='NOT_RUN',native_learning_production='NOT_RUN',product_accepted=False)
    a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
