#!/usr/bin/env python3
"""H1 live-gated neural speech to existing synchronized MIX and diagnostic QA.

No API keys in arguments. Set ELEVENLABS_API_KEY in the launching environment.
--allow-live-provider is required for all remote GET/POST requests; source data
transfer additionally requires approval in deployment.json. No GitHub operations.
"""
from pathlib import Path
import argparse, json, os, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path,nargs='?');p.add_argument('--deployment',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--cache',type=Path);p.add_argument('--seal-key-file',type=Path)
    p.add_argument('--profile',choices=('batch001-144','batch001-204'),default='batch001-144')
    p.add_argument('--allow-live-provider',action='store_true');p.add_argument('--allow-review-output',action='store_true')
    p.add_argument('--standalone-fixture','--with-dir-snapshot',dest='standalone_fixture',action='store_true',help='Use included byte-verified DIR dependency snapshot; this does not select a fake speech provider');p.add_argument('--sync-spec',type=Path);p.add_argument('--mix-spec',type=Path)
    p.add_argument('--probe-voice-id');p.add_argument('--probe-language',default='en')
    p.add_argument('--live-authority-revision',help='Non-secret operator/network authority revision required for live provider access')
    p.add_argument('--probe-model',choices=('eleven_multilingual_v2','eleven_flash_v2_5'),default='eleven_multilingual_v2')
    a=p.parse_args(argv)
    if a.standalone_fixture:sys.path.append(str(ROOT/'dependency_snapshot'))
    try:
        from bie.audio.common import AudioError,strict_json,fingerprint
        from bie.audio.tts_cache import TTSCache,read_regular
        from bie.audio.neural_policy import NeuralDeployment,NeuralSettings,MODEL,identifier
        from bie.audio.neural_store import load_seal_key,NeuralResponseStore
        from bie.audio.neural_transport import OfficialNeuralTransport
        from bie.audio.neural_authority import LiveProviderPolicy,LiveProviderAuthority
        from bie.audio.neural_call_journal import PaidCallJournal
        from bie.audio.neural_scheduler import ProviderCallScheduler
        from bie.audio.elevenlabs_provider import ElevenLabsProvider
        # Gated before reading secrets, preparing output, or sending even a GET.
        if not a.allow_live_provider:raise AudioError('NEURAL_LIVE_OPT_IN_REQUIRED')
        live_policy=LiveProviderPolicy(a.live_authority_revision or 'audio-neural-cli-live-v1',True)
        authority=LiveProviderAuthority(live_policy)
        # Resolve once here only to fail before output creation; provider resolves again at request time.
        authority.secrets.credential()
        if not a.output or a.output.exists() or any(x.is_symlink() for x in (a.output,*a.output.parents)):
            raise AudioError('NEURAL_EXCLUSIVE_OUTPUT_REQUIRED')
        if a.probe_voice_id:
            identifier(a.probe_voice_id,'voice id');transport=OfficialNeuralTransport()
            model_key=authority.authorize('GET','/v1/models')
            voice_path='/v1/voices/'+a.probe_voice_id;voice_key=authority.authorize('GET',voice_path)
            model_response=transport.request('GET','/v1/models',b'',api_key=model_key,maximum=1000000,deadline=30,socket_timeout=10)
            voice_response=transport.request('GET',voice_path,b'',api_key=voice_key,maximum=1000000,deadline=30,socket_timeout=10)
            if model_response.status!=200 or voice_response.status!=200:raise AudioError('NEURAL_CATALOG_PROBE_REJECTED')
            models=strict_json(model_response.body.decode());voice=strict_json(voice_response.body.decode())
            found=[v for v in models if type(v)is dict and v.get('model_id')==a.probe_model]
            if len(found)!=1 or voice.get('voice_id')!=a.probe_voice_id:raise AudioError('NEURAL_CATALOG_PROBE_MISMATCH')
            from dataclasses import asdict
            # This is a template, not operator rights approval or live synthesis.
            config=NeuralDeployment(a.probe_voice_id,'REPLACE_WITH_APPROVED_DEPLOYMENT_REVISION',a.probe_language,
                fingerprint(found[0]),fingerprint(voice),('REPLACE_WITH_VOICE_AND_USAGE_APPROVAL_REFERENCE',),
                model_id=a.probe_model,language_mode='enforced' if a.probe_model=='eleven_flash_v2_5' else 'provider_auto')
            a.output.mkdir(parents=True,exist_ok=False)
            (a.output/'deployment.template.json').write_text(json.dumps(asdict(config),indent=2)+'\n')
            (a.output/'MODEL_METADATA.json').write_text(json.dumps(found[0],indent=2)+'\n')
            (a.output/'VOICE_METADATA.json').write_text(json.dumps(voice,indent=2)+'\n')
            print(json.dumps({'status':'CATALOG_SNAPSHOT_ONLY','synthesis_calls':0,'product_accepted':False}));return 0
        if not all((a.input,a.deployment,a.cache,a.seal_key_file)):raise AudioError('NEURAL_INPUTS_REQUIRED')
        qa_dest=a.output.parent/(a.output.name+'-qa')
        if qa_dest.exists() or any(x.is_symlink() for x in (qa_dest,*qa_dest.parents)):
            raise AudioError('NEURAL_EXCLUSIVE_QA_OUTPUT_REQUIRED')
        config=NeuralDeployment.from_dict(strict_json(read_regular(a.deployment,32000).decode()))
        if not config.provider_data_transfer_approved or 'REPLACE_' in config.deployment_revision or any('REPLACE_' in x for x in config.rights_refs):
            raise AudioError('NEURAL_DEPLOYMENT_APPROVAL_REQUIRED')
        from audio_synthesize import prepare_input
        from bie.audio.neural_pipeline import prepare_neural_sync,provider_evidence_files
        from bie.audio.sync_pipeline import bind_sync_spec
        from bie.audio.mix_pipeline import mix_synchronized,MixPolicy
        from bie.audio.mix_io import publish_mix,read_mix_spec
        from bie.audio.qa_pipeline import audit_mix
        from bie.audio.qa_io import publish_qa
        raw=read_regular(a.input,2000000);plan=prepare_input(strict_json(raw.decode()),a.profile)
        store=NeuralResponseStore(a.cache/'neural-responses',key=load_seal_key(a.seal_key_file,create=True))
        journal=PaidCallJournal(a.cache/'paid-call-journal')
        scheduler=ProviderCallScheduler(a.cache/'provider-slots',max_inflight=live_policy.max_inflight,admission_timeout_seconds=live_policy.admission_timeout_seconds)
        provider=ElevenLabsProvider(config,store,allow_live=True,context_plan=plan,authority=authority,journal=journal,scheduler=scheduler)
        cache=TTSCache(a.cache/'speech',namespace='elevenlabs:'+config.deployment_revision)
        synced=prepare_neural_sync(plan,provider,cache)
        animations=bind_sync_spec(synced,strict_json(read_regular(a.sync_spec,1000000).decode())) if a.sync_spec else None
        stems=();policy=MixPolicy();copies={}
        if a.mix_spec:stems,policy,copies=read_mix_spec(strict_json(read_regular(a.mix_spec,1000000).decode()),a.mix_spec.parent,synced)
        mixed=mix_synchronized(synced,stems,policy=policy,animations=animations)
        # Use existing exclusive, validated media publication and reload path.
        copies.update({'narration.json':raw,'neural-deployment.json':read_regular(a.deployment,32000)})
        copies.update(provider_evidence_files(synced,provider))
        if a.mix_spec:copies['mix.json']=read_regular(a.mix_spec,1000000)
        publish_mix(mixed,a.output,sync=synced,inputs=copies,allow_review=a.allow_review_output)
        report,captions=audit_mix(mixed,synced,asset_wavs=tuple(v for k,v in copies.items() if k.endswith('.wav')))
        qa_dest=a.output.parent/(a.output.name+'-qa')
        publish_qa(report,captions,qa_dest)
        print(json.dumps({'status':report['status'],'provider_id':provider.provider_id,'media_sha256':mixed.clock()['output_audio_sha256'],
            'live_http_calls':provider.request_count,'live_synthesis_calls':provider.generation_count,'engine_replay_calls':0,
            'cache_hits':list(synced.cache_hits),'live_authority':authority.receipt(),'cinematic_quality_verified':False,'product_accepted':False},indent=2))
        return 0 if report['status']=='PASS' else 3 if report['status']=='REVIEW' else 2
    except ImportError:
        print(json.dumps({'status':'BLOCKED','error_code':'NEURAL_CANONICAL_DEPENDENCY_MISSING','product_accepted':False}),file=sys.stderr);return 2
    except (ValueError,TypeError,OSError,KeyError):
        # Inspect only the stable code; never print arbitrary source or secret text.
        e=sys.exc_info()[1];code=getattr(e,'code','NEURAL_RUNTIME_INPUT_OR_IO_ERROR')
        print(json.dumps({'status':'BLOCKED','error_code':code,'product_accepted':False}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
