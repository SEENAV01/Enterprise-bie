#!/usr/bin/env python3
"""Real local technical-speech benchmark for H2, not neural/listening acceptance.

Four controlled cases plus a repeated independent process, actual CLI publication,
public-key verification, stale/tampered evidence checks and source-preserving remix.
Private signing keys exist only in a temporary directory and are never exported.
"""
from pathlib import Path
from dataclasses import asdict,replace
import argparse,hashlib,json,os,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
sys.path.append(str(ROOT/'dependency_snapshot'))


def corrupt_delivery_to_silence(mixed):
    """Explicit negative fixture: corrupt ONLY delivered PCM, retain original source."""
    import numpy as np
    from bie.audio.mix_contract import MixBuffer
    from bie.audio.mix_meter import FFmpegMeter
    from bie.audio.tts_contract import AudioFormat
    from bie.audio.common import fingerprint
    c=mixed.clock();r=mixed.receipt();fmt=AudioFormat(c['sample_rate'],c['channels'])
    pcm=MixBuffer.from_wav(mixed.wav_bytes,fmt)
    wav=MixBuffer.from_array(np.zeros_like(pcm.array()),pcm.sample_rate).to_wav()
    parsed=MixBuffer.from_wav(wav,fmt);sha=hashlib.sha256(wav).hexdigest()
    c['output_audio_sha256']=sha;r['output_audio_sha256']=sha;r['delivery_pcm']=parsed.info();r['peak_control']['output']=parsed.info()
    r['peak_control']['after']=asdict(FFmpegMeter().measure(parsed,dual_mono=r['policy']['loudness']['dual_mono']))
    r['final_loudness_target_reached']=False;r['requires_review']=True
    r['review_reasons']=['FINAL_LOUDNESS_TARGET_UNMET']
    if r['narration_normalization']['requires_review']:r['review_reasons'].append('NARRATION_LOUDNESS_CONSTRAINED')
    r['clock_fingerprint']=fingerprint(c);r.pop('fingerprint');r['fingerprint']=fingerprint(r)
    return replace(mixed,wav_bytes=wav,clock_json=json.dumps(c),receipt_json=json.dumps(r)).validate()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--allow-local-diagnostic',action='store_true');a=ap.parse_args()
    if not a.allow_local_diagnostic:raise SystemExit('LOCAL_DIAGNOSTIC_OPT_IN_REQUIRED')
    if a.output.exists() or any(p.is_symlink() for p in (a.output,*a.output.parents)):raise SystemExit('OUTPUT_EXISTS_OR_SYMLINK')
    from audio_synthesize import prepare_input
    from bie.audio.timed_espeak_provider import TimedEspeakProvider
    from bie.audio.tts_cache import TTSCache
    from bie.audio.voice_selection import SelectionPolicy
    from bie.audio.caption_alignment import CaptionPolicy
    from bie.audio.sync_pipeline import prepare_sync
    from bie.audio.mix_pipeline import mix_synchronized
    from bie.audio.mix_io import publish_mix
    from bie.audio.acoustic_contract import SCOPE,canonical,build_job
    from bie.audio.acoustic_runtime import probe_local_runtime
    from bie.audio.acoustic_evidence import verify_receipt
    from bie.audio.acoustic_repair import recheck_repair
    from bie.audio.acoustic_io import verify_publication
    from bie.audio.common import AudioError,fingerprint
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
    a.output.mkdir(parents=True);a.output.chmod(0o700);runtime=probe_local_runtime()
    (a.output/'NATIVE_RUNTIME_SNAPSHOT.json').write_bytes(canonical(runtime)+b'\n')
    key=Ed25519PrivateKey.generate();now=int(time.time())
    trust={'schema_version':'bie.audio.evaluator-trust/1','revision':'BENCHMARK_TEST_ONLY_NOT_PRODUCTION_AUTHORITY',
           'scope':SCOPE,'max_age_seconds':3600,'max_future_skew_seconds':30,
           'issuers':[{'key_id':'benchmark-test-only','role':'acoustic-evaluator',
                'public_key_hex':key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex(),
                'runtime_fingerprints':[runtime['fingerprint']], 'not_before':now-30,
                'not_after':now+86400,'revoked':False}]}
    (a.output/'TEST_ONLY_PUBLIC_TRUST.json').write_bytes(canonical(trust)+b'\n')
    cases=[];saved={}
    with tempfile.TemporaryDirectory(prefix='bie-h2-benchmark-private-') as td:
        private=Path(td)/'signer.key';private.write_bytes(key.private_bytes_raw());private.chmod(0o600)
        def prepare(example,label):
            raw=(ROOT/'examples'/example).read_bytes()
            plan=prepare_input(json.loads(raw),'batch001-144')
            sync=prepare_sync(plan,TimedEspeakProvider(),TTSCache(Path(td)/label,namespace='h2-native-benchmark'),
                SelectionPolicy(('espeak-timed-local',),('technical_formant',),require_same_voice_code_switching=False),
                caption_policy=CaptionPolicy(channel='display'))
            return sync,mix_synchronized(sync),raw
        s,m,raw=prepare('audio_batch003/scene_animation_pause.json','english-cache')
        hs,hm,hraw=prepare('audio_batch002/hindi.json','hindi-cache')
        bad=corrupt_delivery_to_silence(m)
        # Actual correction: rerun the existing MIX implementation against intact source.
        repaired=mix_synchronized(s)
        for name,sync,mixed,narration,expected in (
            ('english',s,m,raw,3),('controlled-silent-delivery',s,bad,raw,2),
            ('actual-remix',s,repaired,raw,3),('hindi-unsupported',hs,hm,hraw,2)):
            folder=a.output/name;folder.mkdir()
            publish_mix(mixed,folder/'mix',sync=sync,inputs={'narration.json':narration},allow_review=True)
            cmd=[sys.executable,'-B',str(ROOT/'scripts/audio_acoustic.py'),'evaluate',str(folder/'mix'),
                '--with-dir-snapshot','--allow-local-diagnostic','--runtime',str(a.output/'NATIVE_RUNTIME_SNAPSHOT.json'),
                '--private-key-file',str(private),'--key-id','benchmark-test-only',
                '--trust-file',str(a.output/'TEST_ONLY_PUBLIC_TRUST.json'),'--output',str(folder/'evaluation')]
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
            (folder/'CLI_STDOUT.txt').write_text(p.stdout);(folder/'CLI_STDERR.txt').write_text(p.stderr)
            if p.returncode!=expected:raise RuntimeError('UNEXPECTED_CLI_EXIT:'+name+':'+p.stderr)
            verification=verify_publication(folder/'evaluation',mixed,sync,trust)
            measurement=json.loads((folder/'evaluation/MEASUREMENT.json').read_text())
            receipt=json.loads((folder/'evaluation/EVALUATOR_RECEIPT.json').read_text())
            saved[name]=(build_job(mixed,sync),receipt,folder)
            cases.append({'case':name,'cli_exit':p.returncode,'expected_exit':expected,
                'status':json.loads((folder/'evaluation/ASSESSMENT.json').read_text())['status'],
                'segment_statuses':[r['status'] for r in measurement['segments']],
                'native_search_passes':sum(len(r['native_passes']) for r in measurement['segments']),
                'actual_word_windows':sum(len(r['words']) for r in measurement['segments']),
                'publication_verified':verification['passed'],'delivered_audio_sha256':hashlib.sha256(mixed.wav_bytes).hexdigest()})
        # Same input, new independent CLI process: measurement data must reproduce.
        folder=a.output/'english'
        cmd=[sys.executable,'-B',str(ROOT/'scripts/audio_acoustic.py'),'evaluate',str(folder/'mix'),
            '--with-dir-snapshot','--allow-local-diagnostic','--runtime',str(a.output/'NATIVE_RUNTIME_SNAPSHOT.json'),
            '--private-key-file',str(private),'--key-id','benchmark-test-only',
            '--trust-file',str(a.output/'TEST_ONLY_PUBLIC_TRUST.json'),'--output',str(folder/'evaluation-repeat')]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
        (folder/'REPEAT_CLI_STDOUT.txt').write_text(p.stdout);(folder/'REPEAT_CLI_STDERR.txt').write_text(p.stderr)
        if p.returncode!=3:raise RuntimeError('REPEAT_CLI_FAILED')
        repeat=json.loads((folder/'evaluation-repeat/MEASUREMENT.json').read_text())
        first=json.loads((folder/'evaluation/MEASUREMENT.json').read_text())
        if repeat!=first:raise RuntimeError('NATIVE_MEASUREMENT_NOT_REPRODUCIBLE')
        # Exercise the read-only public CLI, not just the Python verifier.
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_acoustic.py'),'verify',str(folder/'mix'),
            '--with-dir-snapshot','--trust-file',str(a.output/'TEST_ONLY_PUBLIC_TRUST.json'),
            '--evidence',str(folder/'evaluation-repeat')],capture_output=True,text=True,timeout=60)
        (folder/'VERIFY_CLI_STDOUT.txt').write_text(p.stdout);(folder/'VERIFY_CLI_STDERR.txt').write_text(p.stderr)
        if p.returncode:raise RuntimeError('VERIFY_CLI_FAILED')
        old_job,old_receipt,old_folder=saved['controlled-silent-delivery']
        new_job,new_receipt,_=saved['actual-remix']
        plan=json.loads((old_folder/'evaluation/REPAIR_PLAN.json').read_text())
        recheck=recheck_repair(plan,old_job,old_receipt,new_job,new_receipt,trust)
        if len(recheck['resolved_diagnostic_items'])!=len(plan['items']):raise RuntimeError('SILENCE_REPAIR_NOT_RECHECKED')
        (a.output/'ACTUAL_REMIX_RECHECK.json').write_bytes(canonical(recheck)+b'\n')
        negative=[]
        for label,rec,job,t in (
            ('old-audio-receipt-on-remix',old_receipt,new_job,trust),
            ('unknown-issuer',new_receipt,new_job,{**trust,'issuers':[{**trust['issuers'][0],'key_id':'not-the-signer'}]}),
            ('revoked-issuer',new_receipt,new_job,{**trust,'issuers':[{**trust['issuers'][0],'revoked':True}]})):
            try:verify_receipt(rec,job,t)
            except AudioError as exc:negative.append({'case':label,'rejected':True,'error_code':exc.code})
            else:raise RuntimeError('NEGATIVE_CHECK_UNEXPECTEDLY_ACCEPTED:'+label)
        bad_receipt=json.loads(json.dumps(new_receipt));bad_receipt['payload']['measurement']['segments'][0]['crop_sha256']='0'*64
        measure=bad_receipt['payload']['measurement'];measure.pop('fingerprint');measure['fingerprint']=fingerprint(measure)
        try:verify_receipt(bad_receipt,new_job,trust)
        except AudioError as exc:negative.append({'case':'public-rehash-no-resign','rejected':True,'error_code':exc.code})
        else:raise RuntimeError('REHASHED_FORGERY_ACCEPTED')
    summary={'schema_version':'bie.audio.h2-native-benchmark/1','passed':True,'cases':cases,
        'repeated_cli_measurement_identical':True,'verify_cli_exit':0,'negative_checks':negative,
        'actual_existing_mix_rerun':True,'remix_audio_matches_original':repaired.wav_bytes==m.wav_bytes,
        'source_and_reading_preserved':recheck['source_and_reading_preserved'],
        'voice':'REAL_LOCAL_TIMED_ESPEAK_ON_SYNTHETIC_TEXT',
        'evaluator':'REAL_INSTALLED_LEGACY_POCKETSPHINX_FSG_ALLPHONE_NGRAM',
        'signer':'EPHEMERAL_LOCAL_TEST_ISSUER_NOT_AN_EXTERNAL_PRODUCTION_EVALUATOR',
        'private_keys_exported':False,'live_neural_requests':0,'human_listening_performed':False,
        'real_book_e2e_verified':False,'section_exit_permitted':False,'product_accepted':False,
        'tested_source':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for base in ('bie','scripts','tests','dependency_snapshot') for p in sorted((ROOT/base).rglob('*.py'))}}
    (a.output/'BENCHMARK_RESULT.json').write_bytes(canonical(summary)+b'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='tested_source'},indent=2))
if __name__=='__main__':main()
