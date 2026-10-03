"""Coherent Section18 supported operator flow; never full learning-product acceptance.

Uses actual application/controlled worker and explicitly retains NOT_RUN.
No provider calls, fixtures published as downstream output, or new test counts.
"""
from pathlib import Path
import argparse, hashlib, json, os, secrets, socket, subprocess, sys, tempfile, time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT
OUT = ROOT / 'validation/section18-supported-flow'
DATA_ROOT = None
sys.path.insert(0, str(SOURCE))
sys.path.insert(1, str(SOURCE / 'tests/productization/document_intelligence'))


def serve(data_root, port):
    from apps.operator.contracts import Credentials, Principal, PERMISSIONS
    from apps.operator.main import create_app
    from apps.operator.service import Service
    import uvicorn
    creds = Credentials()
    creds.grant(os.environ['BIE_OPERATOR_TOKEN'], Principal('local-operator', 'local', PERMISSIONS, time.time()+600))
    creds.grant(os.environ['BIE_TEST_FOREIGN_TOKEN'], Principal('foreign-probe', 'foreign', PERMISSIONS, time.time()+600))
    uvicorn.run(create_app(Service(data_root, creds)), host='127.0.0.1', port=port,
                access_log=False, log_level='critical')


def main():
    from structural_pdf_fixtures import hierarchy_pdf_with_outline
    from bie.document_intelligence.real_pdf_toc_runtime import inspect_real_pdf_toc
    from apps.operator.process_supervision import child_environment
    assert not OUT.exists(), 'immutable diagnostic output already exists'
    OUT.mkdir(parents=True)
    private_state = tempfile.TemporaryDirectory(prefix='bie-s18-supported-flow-')
    storage = Path(private_state.name) / 'state'
    storage.mkdir()
    assert storage.resolve().is_relative_to(Path(private_state.name).resolve())
    token, foreign = secrets.token_hex(32), secrets.token_hex(32)
    env = child_environment()
    # The parser's intentionally minimal environment is not an HTTP-server
    # environment. Windows os.environ iteration uppercases SYSTEMROOT, whereas
    # the parser allowlist uses SystemRoot. Explicitly restore this OS loader
    # setting for this test server only; do not broaden production child env.
    if os.name == 'nt': env['SystemRoot'] = os.environ['SystemRoot']
    env.update(BIE_OPERATOR_TOKEN=token, BIE_TEST_FOREIGN_TOKEN=foreign,
               PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    rows, workers, server = [], [], None
    responses = []
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'

    def stop():
        nonlocal server
        if server is not None:
            if server.poll() is None: server.terminate()
            try: server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=10)
            server = None

    def start():
        nonlocal server
        server = subprocess.Popen([sys.executable, '-X', 'utf8', '-B', str(Path(__file__).resolve()),
            '--serve', '--data-root', str(storage), '--port', str(port), '--output', str(OUT)], cwd=SOURCE,
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            if server.poll() is not None:
                _, stderr = server.communicate(timeout=5)
                receipt['startup_stderr_sha256'] = hashlib.sha256(stderr).hexdigest()
                receipt['startup_stderr_bytes'] = len(stderr)
                # Local harness-only classification; never echo credentials,
                # source bytes, traceback, or filesystem paths into receipts.
                receipt['startup_failure_code'] = ('SOCKET_PERMISSION' if b'10013' in stderr or b'PermissionError' in stderr
                    else 'HARNESS_CHILD_STARTUP')
                last_line = stderr.decode('utf-8', errors='replace').strip().splitlines()[-1]
                for secret in (token, foreign): last_line = last_line.replace(secret, '[credential-redacted]')
                last_line = last_line.replace(str(ROOT), '[workspace]').replace(str(SOURCE), '[source]')
                receipt['safe_startup_last_line'] = last_line[:400]
                print(json.dumps(dict(startup_failure_code=receipt['startup_failure_code'])), flush=True)
                print(json.dumps(dict(safe_startup_last_line=receipt['safe_startup_last_line'])), flush=True)
                raise AssertionError('owned HTTP process failed')
            try:
                with urlopen(base+'/healthz', timeout=1) as response:
                    assert response.status == 200
                    assert json.loads(response.read(4097)) == dict(status='ok', service='bie-local-operator', product_accepted=False)
                    return
            except OSError: time.sleep(.1)
        raise AssertionError('bounded HTTP startup failed')

    def request(label, path, value=None, raw=None, expected=200, credential=None):
        headers = {'Authorization': 'Bearer '+(token if credential is None else credential)}
        data = None
        if value is not None:
            data = json.dumps(value, sort_keys=True).encode(); headers['Content-Type'] = 'application/json'
        if raw is not None: data = raw; headers['Content-Type'] = 'application/pdf'
        req = Request(base+'/operator/v1/'+path, data=data, headers=headers)
        try: response = urlopen(req, timeout=45)
        except HTTPError as error: response = error
        with response:
            body = response.read(512*1024+1); status = response.status
        if status != expected:
            safe_error = json.loads(body).get('error', {}).get('code', 'unclassified')
            receipt['first_http_failure'] = dict(step=label, http=status, safe_code=safe_error)
        assert len(body) <= 512*1024 and status == expected, 'HTTP contract failed: '+label
        result = json.loads(body)
        responses.append(body)
        rows.append(dict(step=label, http=status, response_sha256=hashlib.sha256(body).hexdigest()))
        print(json.dumps(dict(step=label, http=status)), flush=True)
        return result

    def work(run, expected):
        # The canonical controlled entry point applies its own stricter worker
        # budget. The probe deadline only bounds ownership of the CLI wrapper.
        outcome = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(SOURCE/'scripts/run_bie_operator_worker.py'),
            '--data-root', str(storage), '--run-id', run], cwd=SOURCE, env=env,
            capture_output=True, timeout=60)
        assert outcome.returncode == 0 and len(outcome.stdout) <= 4096, 'controlled worker failed'
        value = json.loads(outcome.stdout)
        assert value['outcome'] == expected
        workers.append(dict(run_id=run, outcome=expected, separate_process=True, finished=True))
        print(json.dumps(dict(worker=expected)), flush=True)

    receipt = dict(schema='bie.section18.supported-flow-diagnostic/1', source_kind='SYNTHETIC_TEST',
        full_learning_flow='NOT_RUN', full_flow_gate_passed=False, new_distinct_test_methods=0,
        provider_calls=False, product_accepted=False, deployed=False, task028='PAUSED')
    try:
        pdf = hierarchy_pdf_with_outline(); source_sha = hashlib.sha256(pdf).hexdigest()
        expected_safe = inspect_real_pdf_toc(pdf).to_safe_dict()
        start()
        request('authorized_workspace', 'workspace')
        invalid = request('invalid_source', 'sources', raw=b'SYNTHETIC_TEST invalid PDF')
        assert invalid['validation']['status'] == 'INVALID' and not invalid['stored']
        request('invalid_source_cannot_create', 'runs', dict(source_id=invalid['source_id'], config={}, idempotency_key='invalid'), expected=409)
        src = request('source_admission', 'sources', raw=pdf)
        assert src['sha256'] == source_sha and src['validation']['status'] == 'VALID'
        dup = request('source_duplicate', 'sources', raw=pdf)
        assert dup['duplicate'] and dup['source_id'] == src['source_id']
        run = request('run_creation', 'runs', dict(source_id=src['source_id'], config={}, idempotency_key='coherent'), expected=202)['run_id']
        initial = request('ready', 'runs/'+run)
        assert initial['status'] == initial['queue_state'] == 'READY' and initial['source_hash'] == source_sha
        paused = request('pause', 'runs/'+run+'/control', dict(action='pause', expected_revision=initial['revision']))
        assert paused['status'] == 'PAUSED'
        work(run, 'PAUSED')
        stop(); start()
        reopened = request('restart_paused', 'runs/'+run)
        assert reopened['run_id'] == run and reopened['status'] == 'PAUSED' and reopened['source_hash'] == source_sha
        resumed = request('resume', 'runs/'+run+'/control', dict(action='resume', expected_revision=reopened['revision']))
        assert resumed['status'] == 'READY'
        work(run, 'ACKED')
        final = request('succeeded', 'runs/'+run)
        assert final['status'] == 'SUCCEEDED' and final['queue_state'] == 'ACKED' and final['result_available']
        result = request('safe_result', 'runs/'+run+'/result')
        assert result == expected_safe and final['source_hash'] == source_sha
        timeline = request('durable_timeline', 'runs/'+run+'/timeline')
        assert timeline['run_id'] == run and len(timeline['items']) >= 3
        inventory = request('actual_artifacts', 'runs/'+run+'/artifacts')
        assert inventory['total'] >= 3
        for item in inventory['items']:
            assert item['run_id'] == run and item['native_run_id'] == final['native_job_id']
        for kind in ('concept', 'prerequisite'):
            assert request('missing_graph_'+kind, 'runs/'+run+'/graphs/'+kind)['status'] == 'NOT_RUN'
        from apps.operator.view_contracts import KINDS
        assert set(KINDS) == {'reasoning', 'curriculum', 'lesson', 'director', 'scene_ir', 'game_plan'}
        for kind in KINDS:
            assert request('missing_view_'+kind, 'runs/'+run+'/views/'+kind)['status'] == 'NOT_RUN'
        for kind in ('render', 'game'):
            assert request('missing_preview_'+kind, 'runs/'+run+'/previews/'+kind)['status'] == 'NOT_RUN'
        for kind in ('gates', 'repairs'):
            assert request('missing_assurance_'+kind, 'runs/'+run+'/assurance/'+kind)['status'] == 'NOT_RUN'
        for kind in ('benchmark', 'release'):
            assert request('missing_quality_'+kind, 'runs/'+run+'/quality/'+kind)['status'] == 'NOT_RUN'
        assert all(v['status'] == 'NOT_RUN' for v in final['learning_outputs'].values())
        request('foreign_tenant', 'runs/'+run, expected=404, credential=foreign)
        request('forbidden_artifact', 'runs/'+run+'/artifacts/missing/code', expected=404)
        bad_source = request('valid_inventory_invalid_outline', 'sources', raw=hierarchy_pdf_with_outline(((' ', 0, None),)))
        assert bad_source['validation']['status'] == 'VALID'
        failed_run = request('failed_run_create', 'runs', dict(source_id=bad_source['source_id'], config={}, idempotency_key='fail'), expected=202)['run_id']
        work(failed_run, 'FAILED')
        failure = request('real_failed_state', 'runs/'+failed_run)
        assert failure['status'] == 'FAILED' and failure['queue_state'] == 'DEAD_LETTER' and not failure['result_available']
        assert request('safe_failure_view', 'runs/'+failed_run+'/failure')['traceback_exposed'] is False
        request('failure_has_no_result', 'runs/'+failed_run+'/result', expected=409)
        child = request('governed_retry_child', 'runs/'+failed_run+'/retry', dict(idempotency_key='retry-one'), expected=202)['run_id']
        assert child != failed_run
        retry_replay = request('retry_replay', 'runs/'+failed_run+'/retry', dict(idempotency_key='retry-one'), expected=202)
        assert retry_replay['run_id'] == child
        assert request('retry_lineage', 'runs/'+child)['parent_run_id'] == failed_run
        work(child, 'FAILED')
        cancelled_run = request('cancel_run_create', 'runs', dict(source_id=src['source_id'], config={}, idempotency_key='cancel'), expected=202)['run_id']
        revision = request('before_cancel', 'runs/'+cancelled_run)['revision']
        cancelled = request('real_cancel', 'runs/'+cancelled_run+'/control', dict(action='cancel', expected_revision=revision))
        assert cancelled['status'] == 'CANCELLED'
        cancelled_state = request('persisted_cancel_receipt', 'runs/'+cancelled_run)
        assert cancelled_state['status'] == 'CANCELLED' and cancelled_state['queue_state'] == 'DEAD_LETTER'
        work(cancelled_run, 'CANCELLED')
        stop(); old_token = token; token = secrets.token_hex(32); env['BIE_OPERATOR_TOKEN'] = token; start()
        request('old_credential_revoked_after_restart', 'runs/'+run, expected=401, credential=old_token)
        after = request('reopened_final_state', 'runs/'+run)
        assert after['run_id'] == run and after['source_hash'] == source_sha and after['status'] == 'SUCCEEDED'
        assert request('result_survives_restart', 'runs/'+run+'/result') == result
        replay = request('creation_replay_after_restart', 'runs', dict(source_id=src['source_id'], config={}, idempotency_key='coherent'), expected=202)
        assert replay['run_id'] == run
        transcript = b'\n'.join(responses)
        assert token.encode() not in transcript and old_token.encode() not in transcript and foreign.encode() not in transcript
        assert b'CHAPTER 1 Foundation' not in transcript and b'Ordinary hierarchy' not in transcript
        receipt.update(supported_pdf_flow='PASS', section18_supported_operator_flow_passed=True, source_hash=source_sha, run_id=run,
            native_job_id=after['native_job_id'], result_sha256=hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
            source_run_cas_bindings_verified=True, restart_identity_verified=True,
            downstream_not_run_preserved=True, raw_source_and_credential_leak_detected=False)
    except Exception as error:
        receipt.update(supported_pdf_flow='FAIL', safe_failure_type=type(error).__name__, completed_steps=len(rows))
        raise
    finally:
        stop()
        private_state.cleanup()
        receipt.update(steps=rows, workers=workers, owned_http_process_reaped=server is None,
            temporary_synthetic_state_removed=True, local_synthetic_cas_retained=False, stage_outputs_fabricated=False)
        (OUT/'DIAGNOSTIC_RESULT.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps({k:v for k,v in receipt.items() if k not in ('steps','workers')}, sort_keys=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--data-root', type=Path)
    parser.add_argument('--port', type=int)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output.absolute()
    assert not OUT.is_symlink()
    if args.serve:
        assert args.data_root.name == 'state'
        assert args.data_root.parent.name.startswith('bie-s18-supported-flow-')
        assert args.data_root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
        assert 1024 <= args.port <= 65535
        serve(args.data_root, args.port)
    else:
        assert args.data_root is None, 'private state is owned and created by this harness'
        main()
