"""Real inspection recheck; never substitute fixture previews for missing media."""
from pathlib import Path
import argparse, json, secrets, sys, time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import validate_section18_batch002_money as prior
from apps.operator.contracts import Credentials, Principal, PERMISSIONS
from apps.operator.service import Service
from apps.operator.main import create_app
from fastapi.testclient import TestClient

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', type=Path, required=True)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    prior.main()
    credentials = Credentials()
    token = secrets.token_hex(32)
    principal = Principal('validation', 'money-validation', PERMISSIONS, time.time()+3600)
    credentials.grant(token, principal)
    service = Service(args.data_root, credentials)
    headers = {'Authorization': 'Bearer '+token}
    runs = service.list_runs(principal, 0, 25)['items']
    assert len(runs) == 1, 'REAL_VALIDATION_RUN_INVENTORY_CHANGED'
    run_id = runs[0]['run_id']
    with TestClient(create_app(service), base_url='http://localhost') as client:
        preview_states = {}
        for kind in ('render', 'game'):
            response = client.get('/operator/v1/runs/'+run_id+'/previews/'+kind, headers=headers)
            assert response.status_code == 200 and response.json()['status'] == 'NOT_RUN'
            preview_states[kind] = response.json()['status']
        assert client.get('/operator/v1/runs/'+run_id+'/render/media', headers=headers).status_code == 404
        assert client.post('/operator/v1/runs/'+run_id+'/game/preview-grant', json={}, headers=headers).status_code == 404
    receipt = json.loads(args.receipt.read_text())
    receipt.update(real_preview_states=preview_states, synthetic_previews_substituted=False,
                   native_video_producer_executed=False, native_game_build_worker_executed=False,
                   missing_media_fail_closed=True, section_complete=False, task028='PAUSED')
    args.receipt.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, sort_keys=True))

if __name__ == '__main__':
    main()
