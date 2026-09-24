#!/usr/bin/env python3
"""OFFLINE CONTRACT FIXTURE only: response-shaped chirp -> existing audio pipeline.
No remote neural synthesis, independently observed pronunciation, or live timings.
"""
from pathlib import Path
import argparse,sys,json,hashlib,tempfile
from dataclasses import replace,asdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))
from tests.audio.neural_test_support import setup,plan,multi_plan,config,FixtureTransport,MODEL
from bie.audio.common import fingerprint
from bie.audio.neural_pipeline import prepare_neural_sync,provider_evidence_files
from bie.audio.tts_cache import TTSCache
from bie.audio.mix_pipeline import mix_synchronized,verify_mixed_source
from bie.audio.mix_io import publish_mix
from bie.audio.qa_source import load_published_mix
from bie.audio.qa_pipeline import audit_mix
from bie.audio.qa_io import publish_qa


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--case',choices=('english','hindi','multilingual-v2','multiscene'),required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    root=args.output;root.mkdir(parents=True,exist_ok=False)
    t=FixtureTransport();p=multi_plan() if args.case=='multiscene' else plan('यह एक परीक्षण है।',language='hi',pause=300) if args.case=='hindi' else plan(pause=300)
    c=config(p.segments[0].language)
    if args.case=='multilingual-v2':
        t.model={**MODEL,'model_id':'eleven_multilingual_v2','maximum_text_length_per_request':10000}
        c=replace(c,model_id='eleven_multilingual_v2',language_mode='provider_auto',model_metadata_fingerprint=fingerprint(t.model))
    with tempfile.TemporaryDirectory(prefix='bie-neural-fixture-') as td:
        p,provider,requests,t=setup(td,p=p,c=c,transport=t,context=True);cache=TTSCache(Path(td)/'tts',namespace='fixture')
        first=prepare_neural_sync(p,provider,cache,allow_fixture=True);calls=provider.request_count
        second=prepare_neural_sync(p,provider,cache,allow_fixture=True)
        if first.wav_bytes!=second.wav_bytes or provider.request_count!=calls or not all(second.cache_hits):raise ValueError('CACHE_REPLAY_MISMATCH')
        mixed=mix_synchronized(first);verify_mixed_source(mixed,first)
        inputs=provider_evidence_files(first,provider);publish_mix(mixed,root/'mix',sync=first,inputs=inputs,allow_review=True)
        m,s,_=load_published_mix(root/'mix');qa,captions=audit_mix(m,s);publish_qa(qa,captions,root/'qa')
        if qa['status']!='REVIEW':raise ValueError('FIXTURE_NOT_EXPECTED_REVIEW')
        artifact={'case':args.case,'scope':'SYNTHETIC_PROVIDER_HTTP_CONTRACT_FIXTURE_NOT_NEURAL_SPEECH',
            'live_provider_calls':0,'fixture_http_requests':len(t.calls),'fixture_generation_requests':provider.generation_count,
            'cache_hit_second_run':all(second.cache_hits),'additional_http_requests_on_cache_hit':provider.request_count-calls,
            'output_sha256':hashlib.sha256(m.wav_bytes).hexdigest(),'clock_fingerprint':fingerprint(m.clock()),
            'captions_sha256':hashlib.sha256((root/'mix/captions.vtt').read_bytes()).hexdigest(),
            'qa_status':qa['status'],'qa_checks':{q['task_id']:q['status'] for q in qa['checks']},
            'sample_rate':m.clock()['sample_rate'],'samples':m.clock()['total_samples'],'scenes':len(m.clock()['scenes']),
            'timing_basis':first.alignments[0].basis,'engine_replay_calls':first.receipt()['engine_replay_calls'],
            'independent_acoustic_alignment':False,'cinematic_quality_verified':False,'product_accepted':False}
        (root/'RESULT.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
        (root/'WIRE_REQUESTS.json').write_text(json.dumps([{'method':m,'path':p,'body':json.loads(b) if b else None} for m,p,b in t.calls],ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(artifact));return 0
if __name__=='__main__':
    from bie.audio.fixture_scope import synthetic_timing_scope
    with synthetic_timing_scope():raise SystemExit(main())
