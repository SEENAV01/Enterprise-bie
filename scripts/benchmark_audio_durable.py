#!/usr/bin/env python3
"""Synthetic-source native benchmark; ephemeral TEST-ONLY signing authority.

No private key is retained. This exercises real persisted/reloaded sound and
native legacy acoustic analysis, not production voices or phonetic acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile,time,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.absolute();out.mkdir(parents=True,exist_ok=False)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat,PrivateFormat,NoEncryption
    from tests.audio.qa_test_support import native
    from bie.audio.mix_io import publish_mix
    from bie.audio.acoustic_contract import SCOPE,canonical
    from bie.audio.acoustic_runtime import probe_local_runtime
    from bie.audio.acoustic_io import verify_publication
    from bie.audio.durable_store import AudioArtifactStore
    runtime=probe_local_runtime();now=int(time.time());key=Ed25519PrivateKey.generate();key_id='H3-BENCHMARK-EPHEMERAL-TEST-ONLY'
    trust={'schema_version':'bie.audio.evaluator-trust/1','revision':'TEST_ONLY_NEVER_USE_FOR_RELEASE',
        'scope':SCOPE,'max_age_seconds':3600,'max_future_skew_seconds':30,'issuers':[{
        'key_id':key_id,'public_key_hex':key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex(),
        'role':'acoustic-evaluator','runtime_fingerprints':[runtime['fingerprint']],
        'not_before':now-60,'not_after':now+3600,'revoked':False}]}
    (out/'RUNTIME.json').write_bytes(canonical(runtime));(out/'TRUST_TEST_ONLY.json').write_bytes(canonical(trust))
    summary={'scope':'Real local acoustic persistence/restart diagnostics on synthetic source',
        'native_worker_scope':'H2 bounded subprocess; canonical kernel adoption remains open',
        'github_write_performed':False,'production_authority':False,'product_accepted':False,
        'private_key_bundled':False,'cases':[]}
    with tempfile.TemporaryDirectory(prefix='bie-h3-key-') as td:
        private=Path(td)/'signer';private.write_bytes(key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption()));private.chmod(0o600)
        for language,runs,expected in [('english',2,3),('hindi',1,2)]:
            case=out/language;case.mkdir();sync,mixed,_=native(language=language)
            publish_mix(mixed,case/'input',sync=sync,allow_review=True)
            before=hashlib.sha256(mixed.wav_bytes).hexdigest();rows=[]
            for i in range(runs):
                command=[sys.executable,'-B',str(ROOT/'scripts/audio_durable.py'),'evaluate',
                    '--store',str(case/'store'),'--input',str(case/'input'),'--output',str(case/f'evidence-{i+1}'),
                    '--runtime',str(out/'RUNTIME.json'),'--trust-file',str(out/'TRUST_TEST_ONLY.json'),
                    '--private-key-file',str(private),'--key-id',key_id,
                    '--run-id','01952504-3824-4000-8000-000000000003','--job-id',language,'--revision','1',
                    '--allow-local-diagnostic','--with-dir-snapshot']
                r=subprocess.run(command,capture_output=True,text=True,timeout=120)
                (case/f'run-{i+1}.stdout.txt').write_text(r.stdout);(case/f'run-{i+1}.stderr.txt').write_text(r.stderr)
                if r.returncode!=expected:raise RuntimeError(f'{language}: {r.returncode}: {r.stderr}')
                row=json.loads(r.stdout)
                assert row['cache_hit']==(i>0) and row['native_evaluations']==(0 if i else 1)
                row['returncode']=r.returncode;rows.append(row)
                assert verify_publication(case/f'evidence-{i+1}',mixed,sync,trust)['passed']
            measurement=json.loads((case/'evidence-1/MEASUREMENT.json').read_text())
            file_identity=lambda p:{x.relative_to(p).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file() and x.name!='OUTPUT_SHA256.json' and not x.name.endswith('.lock')}
            identical= file_identity(case/'evidence-1')==file_identity(case/'evidence-2') if runs==2 else None
            if runs==2:assert identical and rows[0]['artifact_ref']==rows[1]['artifact_ref']
            after=hashlib.sha256((case/'input/master.wav').read_bytes()).hexdigest();assert before==after
            summary['cases'].append({'case':language,'runs':rows,'source_media_unchanged':True,
                'delivered_wav_sha256':before,'cold_restart_payload_bytes_identical':identical,
                'publication_comparison_scope':'All evidence/caption payload files; random publish-lock names and manifests differ and are verified independently by inherited verifier',
                'native_segment_statuses':[s['status'] for s in measurement['segments']],
                'native_search_passes':sum(len(s['native_passes']) for s in measurement['segments']),
                'word_windows':sum(len(s['words']) for s in measurement['segments']),
                'store':AudioArtifactStore(case/'store/artifacts').inspect()})
        with tempfile.TemporaryDirectory(prefix='bie-h3-corrupt-') as td:
            dest=Path(td)/'store';shutil.copytree(out/'english/store',dest)
            info=summary['cases'][0];h=info['delivered_wav_sha256']
            blob=dest/'artifacts/cas/blobs/sha256'/h[:2]/h;blob.write_bytes(b'tampered')
            r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_durable.py'),'inspect','--store',str(dest),'--with-dir-snapshot'],capture_output=True,text=True,timeout=15)
            assert r.returncode==2
            summary['tampered_stored_media_rejected']={'returncode':r.returncode,'stderr':r.stderr}
    # Database evidence is data, not an active deployment snapshot. Checkpoint
    # and close WAL through the existing catalog before packaging.
    for language in ('english','hindi'):
        with AudioArtifactStore(out/language/'store/artifacts').session() as io:
            io.catalog.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    summary['tested_source']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ('bie','scripts','dependency_snapshot') for p in (ROOT/folder).rglob('*.py')}
    summary['passed']=True
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='tested_source'},indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
