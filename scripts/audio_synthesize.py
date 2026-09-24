#!/usr/bin/env python3
"""Run AUDIO VO-001..010 locally. Explicit technical voice opt-in; no GitHub writes.

Inputs use a documented Batch-001 profile. Output is an exclusive directory with
real WAV files, exact sample offsets and source/reading/voice/cache receipts.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if '--standalone-fixture' in sys.argv:sys.path.append(str(ROOT/'dependency_snapshot'))
from bie.audio.common import AudioError,strict_json,exact_fields
from bie.audio.preparation_bridge import from_v144,from_v204
from bie.audio.multilingual_terms import LanguageTerm,apply_languages
from bie.audio.espeak_provider import EspeakProvider
from bie.audio.tts_contract import SynthesisSettings
from bie.audio.voice_selection import SelectionPolicy,select_voices,requests_for
from bie.audio.tts_cache import TTSCache,read_regular
from bie.audio.pcm_audio import validate_wav,encode_pcm
from audio_prepare import read_request


def prepare_input(raw,profile):
    if profile=='batch001-144':
        utterances,options=read_request(raw);return from_v144(utterances,**options)
    if profile=='batch001-204':
        from bie.audio.compat204.contracts import document_from_dict
        from bie.audio.compat204.pronunciation_lexicon import lexicon_from_dict
        from bie.audio.compat204.narration_segmentation import SegmentationPolicy
        exact_fields(raw,('document','lexicon','policy'))
        return from_v204(document_from_dict(raw['document']),lexicon_from_dict(raw['lexicon']),SegmentationPolicy(**raw['policy']))
    raise AudioError('UNKNOWN_PREPARATION_PROFILE')


def read_language_terms(raw):
    if type(raw)is not list:raise AudioError('LANGUAGE_ARRAY_REQUIRED')
    result=[]
    for row in raw:
        exact_fields(row,tuple(LanguageTerm.__dataclass_fields__))
        if type(row['evidence_refs'])is not list:raise AudioError('LANGUAGE_REFS_ARRAY')
        result.append(LanguageTerm(**{**row,'evidence_refs':tuple(row['evidence_refs'])}))
    return tuple(result)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--profile',choices=('batch001-144','batch001-204'),default='batch001-144')
    ap.add_argument('--language-terms',type=Path);ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--cache-namespace',required=True);ap.add_argument('--allow-technical-voice',action='store_true')
    ap.add_argument('--standalone-fixture',action='store_true');ap.add_argument('--rate-wpm',type=int,default=155)
    args=ap.parse_args(argv);temporary=None
    try:
        if not args.allow_technical_voice:raise AudioError('PRODUCTION_VOICE_NOT_CONFIGURED','Use explicit --allow-technical-voice for eSpeak diagnostics')
        destination=args.output.absolute()
        if destination.exists() or any(p.is_symlink() for p in (destination,*destination.parents)):raise AudioError('OUTPUT_EXISTS_OR_SYMLINK')
        raw=strict_json(read_regular(args.input,2000000).decode('utf-8'))
        plan=prepare_input(raw,args.profile)
        if args.language_terms:
            terms=read_language_terms(strict_json(read_regular(args.language_terms,2000000).decode('utf-8')))
            plan=apply_languages(plan,terms,expected_plan=plan.fingerprint())
        plan.require_ready()
        provider=EspeakProvider();catalog=provider.catalog()
        policy=SelectionPolicy(('espeak-local',),('technical_formant',),require_same_voice_code_switching=False)
        selection=select_voices(plan,catalog,policy,SynthesisSettings(rate_wpm=args.rate_wpm))
        requests=requests_for(plan,catalog,selection);cache=TTSCache(args.cache,namespace=args.cache_namespace)
        destination.parent.mkdir(parents=True,exist_ok=True)
        temporary=Path(tempfile.mkdtemp(prefix='.bie-speech-',dir=destination.parent))
        rows=[];joined=[];cursor=0;total_bytes=0
        for i,request in enumerate(requests,1):
            outcome=cache.get_or_generate(request,provider);asset=outcome.asset
            info,pcm=validate_wav(asset.wav_bytes,request.settings.format);total_bytes+=len(pcm)
            if total_bytes>64000000:raise AudioError('ASSEMBLED_AUDIO_BUDGET','Split the requested job; no content was truncated')
            name=f'segment-{i:04}.wav';(temporary/name).write_bytes(asset.wav_bytes);joined.append(pcm)
            rows.append({'file':name,'start_sample':cursor,'end_sample':cursor+info.samples_per_channel,
                'cache_hit':outcome.cache_hit,'cache_key':outcome.key,'receipt':asset.receipt()});cursor+=info.samples_per_channel
        assembled=encode_pcm(b''.join(joined),selection.settings.format)
        info,_=validate_wav(assembled,selection.settings.format,max_bytes=64001000,max_seconds=1800)
        (temporary/'speech.wav').write_bytes(assembled)
        report={'schema_version':'bie.audio.synthesis-run/1','profile':args.profile,'plan':asdict(plan),'plan_fingerprint':plan.fingerprint(),
            'selection':asdict(selection),'runtime':provider.snapshot,'segments':rows,'assembled_media':asdict(info),
            'provider_invocations_this_run':provider.invocations,'audio_generated':True,'acoustic_quality':'TECHNICAL_LOCAL_FORMANT_UNACCEPTED',
            'source_scope':'SYNTHESIZED_SUPPLIED_REALIZED_NARRATION_NOT_PDF_INGESTION','word_alignment_verified':False,
            'scene_sync_verified':False,'cinematic_quality_verified':False,'product_accepted':False}
        (temporary/'SYNTHESIS_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
        (temporary/'SOURCE_INPUT.json').write_text(json.dumps(raw,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(temporary.iterdir())}
        (temporary/'OUTPUT_SHA256.json').write_text(json.dumps(hashes,sort_keys=True,indent=2)+'\n')
        os.rename(temporary,destination);temporary=None
        print(json.dumps({'output':str(destination),'segments':len(rows),'provider_invocations':provider.invocations,
            'cache_hits':sum(r['cache_hit'] for r in rows),'samples':info.samples_per_channel,'seconds':info.duration_seconds,
            'real_speech_generated':True,'product_accepted':False},ensure_ascii=False));return 0
    except (OSError,ValueError,TypeError,UnicodeError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'output_published':False,'product_accepted':False},ensure_ascii=False),file=sys.stderr);return 2
    finally:
        if temporary is not None:shutil.rmtree(temporary)

if __name__=='__main__':raise SystemExit(main())
