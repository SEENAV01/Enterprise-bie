#!/usr/bin/env python3
"""Execute a synthetic two-scene H5 CLI benchmark with a disposable test signer.

The private key exists only in a private temporary directory and is destroyed.
The exported public trust policy is marked test-only; it is NOT production approval.
No external provider, original book, browser or GitHub is used.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,time,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise SystemExit('OUTPUT_EXISTS')
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat,PrivateFormat,NoEncryption
    from bie.audio.pipeline_contract import SCOPE
    from bie.audio.acoustic_contract import canonical
    from bie.audio.pipeline_bundle import NAMES
    result={'schema_version':'bie.audio.h5.cold-cli-benchmark/1','scope':'ACTUAL_LOCAL_SYNTHETIC_TWO_SCENE_PIPELINE',
            'test_authority':'DISPOSABLE_TEST_ONLY_NOT_PRODUCTION_TRUST','product_accepted':False,'steps':[]}
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT)+os.pathsep+str(ROOT/'dependency_snapshot')}
    with tempfile.TemporaryDirectory(prefix='bie-h5-benchmark-') as td:
        td=Path(td);key=Ed25519PrivateKey.generate();keypath=td/'ephemeral.key'
        keypath.write_bytes(key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption()));keypath.chmod(0o600)
        def run(label,args):
            started=time.monotonic()
            child=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_pipeline.py'),'--standalone-fixture',*map(str,args)],
                                 env=env,cwd=ROOT,capture_output=True,text=True,timeout=240)
            row={'label':label,'fresh_process':True,'exit_code':child.returncode,'seconds':round(time.monotonic()-started,3)}
            if child.returncode:
                row['stderr']=child.stderr[-4000:].replace(str(td),'<ephemeral>');result['steps'].append(row)
                a.output.mkdir(parents=True);(a.output/'NATIVE_BENCHMARK.json').write_bytes(canonical(result))
                raise RuntimeError(label+': '+row['stderr'])
            row['result']=json.loads(child.stdout);result['steps'].append(row);return row['result']
        run('probe-no-synthesis',['probe','--output',td/'profile.json'])
        profile=json.loads((td/'profile.json').read_text());now=int(time.time());keyid='H5_BENCHMARK_EPHEMERAL_DO_NOT_TRUST'
        trust={'schema_version':'bie.audio.pipeline-trust/1','revision':'H5_BENCHMARK_TEST_ONLY','scope':SCOPE,
               'max_age_seconds':3600,'max_future_skew_seconds':30,'issuers':[{'key_id':keyid,'role':'audio-pipeline-executor',
               'public_key_hex':key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex(),
               'profile_fingerprints':[profile['fingerprint']],'not_before':now-60,'not_after':now+86400,'revoked':False}]}
        (td/'trust.json').write_bytes(canonical(trust))
        run('prepare-exact-request',['request',ROOT/'examples/audio_h5/two_scenes.json','--profile',td/'profile.json',
             '--run-id','01952504-3824-4000-8000-000000000105','--job-id','synthetic-two-scenes',
             '--revision','h5-benchmark-v1','--key-id',keyid,'--output',td/'request.json'])
        common=['--request',td/'request.json','--profile',td/'profile.json','--trust',td/'trust.json']
        command=['run',*common,'--root',td/'state','--private-key-file',keypath,'--allow-technical-voice','--allow-review-output']
        first=run('first-native-run',[*command,'--output',td/'first'])
        second=run('cold-process-stored-reuse',[*command,'--output',td/'second'])
        verification=run('independent-export-verification',['verify-export',td/'second',*common])
        assert first['cache_hit'] is False and first['native_pipeline_runs']==1
        assert second['cache_hit'] is True and second['native_pipeline_runs']==0
        assert first['artifact_ref']==second['artifact_ref']
        assert all((td/'first'/n).read_bytes()==(td/'second'/n).read_bytes() for n in NAMES)
        request=json.loads((td/'request.json').read_text());summary=json.loads((td/'first/PIPELINE_SUMMARY.json').read_text())
        assert summary['segments']>=2 and summary['provider_calls']==summary['segments']
        assert verification['signature_reverified'] is True
        with wave.open(str(td/'first/master.wav'),'rb') as wav:
            result['audio']={'frames':wav.getnframes(),'sample_rate':wav.getframerate(),'channels':wav.getnchannels(),
                'seconds':wav.getnframes()/wav.getframerate(),'sample_width_bytes':wav.getsampwidth()}
        result.update({'passed':True,'exact_request_fingerprint':request['fingerprint'],'profile_fingerprint':profile['fingerprint'],
            'source_plan_segments':len(request['plan']['segments']),'same_artifact_ref':True,'identical_core_files':len(NAMES),
            'current_signature_reverified':True,'fresh_cli_processes':5,'first_native_pipeline_runs':1,'second_native_pipeline_runs':0,
            'second_process_note':'Namespace identity discovery still runs; no new speech/timing/mix execution on cache reuse.',
            'source_kind':'SYNTHETIC_NOT_REAL_BOOK','github_modified':False,'private_key_exported':False,
            'production_trust_verified':False,'neural_listening_verified':False,'actual_render_verified':False,'summary':summary})
        a.output.mkdir(parents=True)
        shutil.copytree(td/'first',a.output/'technical_export')
        for n in ('profile.json','request.json','trust.json'):shutil.copyfile(td/n,a.output/('TEST_ONLY_'+n))
        (a.output/'NATIVE_BENCHMARK.json').write_bytes(canonical(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ('steps','summary')},indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
