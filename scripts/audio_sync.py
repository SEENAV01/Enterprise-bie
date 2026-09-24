#!/usr/bin/env python3
"""Run prepared narration -> real speech -> verified word clock/captions/scene sync.

No GitHub changes. Technical eSpeak backend requires explicit user opt-in.
Produces exclusive output with complete source, events and media hashes.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import argparse, hashlib, json, os, shutil, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if '--standalone-fixture' in sys.argv:sys.path.append(str(ROOT/'dependency_snapshot'))
from audio_synthesize import prepare_input,read_language_terms
from bie.audio.common import AudioError,strict_json
from bie.audio.multilingual_terms import apply_languages
from bie.audio.timed_espeak_provider import TimedEspeakProvider
from bie.audio.tts_cache import TTSCache,read_regular
from bie.audio.tts_contract import SynthesisSettings
from bie.audio.voice_selection import SelectionPolicy
from bie.audio.sync_contract import FrameRate
from bie.audio.caption_alignment import CaptionPolicy,export_captions
from bie.audio.sync_pipeline import prepare_sync,bind_sync_spec
from bie.audio.animation_sync import synchronize_animations


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--profile',choices=('batch001-144','batch001-204'),default='batch001-144')
    ap.add_argument('--language-terms',type=Path);ap.add_argument('--sync-spec',type=Path)
    ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--cache-namespace',required=True)
    ap.add_argument('--allow-technical-voice',action='store_true');ap.add_argument('--standalone-fixture',action='store_true')
    ap.add_argument('--fps-numerator',type=int,default=30);ap.add_argument('--fps-denominator',type=int,default=1)
    ap.add_argument('--caption-channel',choices=('spoken','display'),default='display')
    ap.add_argument('--rate-wpm',type=int,default=155)
    args=ap.parse_args(argv);temporary=None
    try:
        if not args.allow_technical_voice:raise AudioError('PRODUCTION_TIMING_PROVIDER_NOT_CONFIGURED','eSpeak diagnostics require --allow-technical-voice')
        output=args.output.absolute()
        if output.exists() or any(p.is_symlink() for p in (output,*output.parents)):raise AudioError('OUTPUT_EXISTS_OR_SYMLINK')
        raw_bytes=read_regular(args.input,2000000);raw=strict_json(raw_bytes.decode('utf-8'));plan=prepare_input(raw,args.profile)
        language_bytes=None
        if args.language_terms:
            language_bytes=read_regular(args.language_terms,2000000)
            plan=apply_languages(plan,read_language_terms(strict_json(language_bytes.decode('utf-8'))),expected_plan=plan.fingerprint())
        provider=TimedEspeakProvider();cache=TTSCache(args.cache,namespace=args.cache_namespace)
        result=prepare_sync(plan,provider,cache,SelectionPolicy(('espeak-timed-local',),('technical_formant',),require_same_voice_code_switching=False),
            settings=SynthesisSettings(rate_wpm=args.rate_wpm),caption_policy=CaptionPolicy(channel=args.caption_channel),
            fps=FrameRate(args.fps_numerator,args.fps_denominator))
        spec_bytes=read_regular(args.sync_spec,2000000) if args.sync_spec else None
        animation=bind_sync_spec(result,strict_json(spec_bytes.decode())) if spec_bytes else synchronize_animations(result.timeline,result.alignments,())
        output.parent.mkdir(parents=True,exist_ok=True);temporary=Path(tempfile.mkdtemp(prefix='.bie-sync-',dir=output.parent))
        def write_json(name,value):
            (temporary/name).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
        (temporary/'speech.wav').write_bytes(result.wav_bytes);(temporary/'SOURCE_INPUT.json').write_bytes(raw_bytes)
        if language_bytes is not None:(temporary/'LANGUAGE_INPUT.json').write_bytes(language_bytes)
        if spec_bytes is not None:(temporary/'ANIMATION_INPUT.json').write_bytes(spec_bytes)
        offsets=tuple(s.start_sample for s in result.timeline.segments)
        for format in ('vtt','srt'):
            (temporary/('captions.'+format)).write_text(export_captions(result.captions,offsets,format=format),encoding='utf-8')
        write_json('SYNC_REPORT.json',result.receipt())
        write_json('WORD_TIMINGS.json',{'segments':[a.receipt() for a in result.alignments],'offsets_samples':offsets})
        write_json('SCENE_SYNC.json',asdict(result.timeline));write_json('PAUSE_SYNC.json',asdict(result.pauses))
        write_json('ANIMATION_SYNC.json',{**asdict(animation),'fingerprint':animation.fingerprint(),
            'sample_keyframes':{t.binding.binding_id:t.keyframes() for t in animation.tracks},'rendered':False,'accepted':False})
        for i,(asset,event) in enumerate(zip(result.assets,result.engine_evidence),1):
            (temporary/f'segment-{i:04}.wav').write_bytes(asset.wav_bytes);write_json(f'events-{i:04}.json',event)
        write_json('OUTPUT_SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(temporary.iterdir())})
        os.rename(temporary,output);temporary=None
        print(json.dumps({'output':str(output),'segments':len(result.assets),'words':sum(len(a.words) for a in result.alignments),
            'captions':sum(len(c.cues) for c in result.captions),'scene_frames':result.timeline.duration_frames,'animation_tracks':len(animation.tracks),
            'pause_windows':len(result.pauses.windows),'cache_hits':sum(result.cache_hits),'tts_generation_calls':provider.invocations,'native_synthesis_calls_including_replay':provider.timing_calls,
            'timing_replay_calls':len(result.alignments),'timing_basis':result.alignments[0].basis,'product_accepted':False}));return 0
    except (ValueError,TypeError,OSError,UnicodeError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'output_published':False,'accepted':False}),file=sys.stderr);return 2
    finally:
        if temporary is not None:shutil.rmtree(temporary)

if __name__=='__main__':raise SystemExit(main())
