"""Rehydrate exact existing SYNC/MIX artifacts; no voice/provider invocation.

Trusted classes are chosen by code, never by a name in JSON. A hash proves
identity/consistency, not authorship, acoustic truth or publisher authenticity.
"""
from __future__ import annotations
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path,PurePosixPath
from typing import get_type_hints,get_origin,get_args,Union
import hashlib,types
from .common import AudioError,strict_json,fingerprint
from .speech_contract import SpeechPlan
from .tts_contract import AudioFormat,SynthesisRequest
from .voice_selection import Selection
from .tts_generation import SpeechAsset
from .pcm_audio import PCMInfo,validate_wav,encode_pcm
from .scene_sync import AudioTimeline
from .sync_contract import AlignedSpeech
from .caption_alignment import CaptionTrack
from .pause_sync import PauseSync
from .sync_pipeline import SynchronizedAudio
from .mix_pipeline import MixedAudio,_verified_sync,verify_mixed_source,export_mixed_captions
from .tts_cache import read_regular

# Only called with a code-selected schema, never data-selected types.
def decode(cls,value,depth=0):
    if depth>32: raise AudioError('QA_SCHEMA_DEPTH')
    origin,args=get_origin(cls),get_args(cls)
    if origin is tuple:
        if type(value)is not list or len(value)>200000: raise AudioError('QA_SCHEMA_ARRAY')
        if len(args)==2 and args[1]is Ellipsis: return tuple(decode(args[0],v,depth+1) for v in value)
        if len(args)!=len(value): raise AudioError('QA_SCHEMA_TUPLE')
        return tuple(decode(t,v,depth+1) for t,v in zip(args,value))
    if origin in (Union,types.UnionType):
        for t in args:
            try:return decode(t,value,depth+1)
            except (ValueError,TypeError): pass
        raise AudioError('QA_SCHEMA_UNION')
    if cls in (str,int,bool,float,type(None)):
        if type(value)is not cls: raise AudioError('QA_SCHEMA_SCALAR')
        return value
    if is_dataclass(cls):
        if type(value)is not dict or set(value)!={f.name for f in fields(cls)}: raise AudioError('QA_SCHEMA_FIELDS',cls.__name__)
        hints=get_type_hints(cls)
        return cls(**{k:decode(hints[k],v,depth+1) for k,v in value.items()})
    raise AudioError('QA_SCHEMA_UNSUPPORTED')

def restore_sync(raw,wav_bytes):
    if type(raw)is not dict or raw.get('schema_version')!='bie.audio.sync-run/1': raise AudioError('QA_SYNC_SCHEMA')
    timeline=decode(AudioTimeline,raw['timeline']);plan=decode(SpeechPlan,raw['plan']);selection=decode(Selection,raw['selection'])
    fmt=AudioFormat(timeline.sample_rate,timeline.channels)
    info,pcm=validate_wav(wav_bytes,fmt,max_bytes=64001000,max_seconds=1800)
    if info.sha256!=timeline.audio_sha256: raise AudioError('QA_SOURCE_WAV_CHANGED')
    rs=raw['speech_receipts']
    if type(rs)is not list or len(rs)!=len(timeline.segments): raise AudioError('QA_SOURCE_ASSETS_MISSING')
    assets=[]
    for r,p in zip(rs,timeline.segments):
        request=decode(SynthesisRequest,r['request'])
        data=encode_pcm(pcm[p.start_sample*fmt.channels*2:p.end_sample*fmt.channels*2],fmt)
        if type(r['diagnostics'])is not list: raise AudioError('QA_SOURCE_DIAGNOSTICS')
        asset=SpeechAsset(request,data,decode(PCMInfo,r['media']),r['provider_audio_sha256'],r['provider_pcm_sha256'],
            r['requested_pause_samples'],r['invocation_id'],r['attempts'],tuple(r['diagnostics']))
        if fingerprint(asset.receipt())!=fingerprint(r): raise AudioError('QA_SOURCE_RECEIPT_CHANGED')
        assets.append(asset)
    aligns=[]
    for r in raw['word_timings']:
        if type(r)is not dict: raise AudioError('QA_TIMING_SCHEMA')
        a=decode(AlignedSpeech,{f.name:r[f.name] for f in fields(AlignedSpeech)})
        if fingerprint(a.receipt())!=fingerprint(r): raise AudioError('QA_TIMING_RECEIPT_CHANGED')
        aligns.append(a)
    caps=tuple(decode(CaptionTrack,r) for r in raw['caption_tracks'])
    if type(raw['cache_hits'])is not list or any(type(x)is not bool for x in raw['cache_hits']): raise AudioError('QA_CACHE_HITS')
    s=SynchronizedAudio(plan,selection,tuple(assets),tuple(aligns),(),caps,timeline,wav_bytes,
        decode(PauseSync,raw['pause_sync']),tuple(raw['cache_hits']))
    _verified_sync(s)
    # Check selection/currentness as well as the reconstructed sample clock.
    if selection.plan_fingerprint!=plan.fingerprint() or len(s.cache_hits)!=len(assets): raise AudioError('QA_SELECTION_CHANGED')
    selected={p.persona_id:p.voice for p in selection.personas}
    for a in assets:
        r=a.request
        if r.selection_fingerprint!=selection.fingerprint() or r.catalog_fingerprint!=selection.catalog_fingerprint or selected.get(r.segment.persona_id)!=r.voice or r.settings!=selection.settings: raise AudioError('QA_SELECTION_CHANGED')
    if fingerprint(s.receipt())!=fingerprint(raw): raise AudioError('QA_SOURCE_RECORD_CHANGED')
    return s

def load_published_mix(folder):
    root=Path(folder).absolute()
    if any(p.is_symlink() for p in (root,*root.parents)) or not root.is_dir(): raise AudioError('QA_INPUT_DIRECTORY')
    index=strict_json(read_regular(root/'OUTPUT_SHA256.json',8000000).decode('utf-8'))
    if type(index)is not dict or len(index)>8192: raise AudioError('QA_FILE_INDEX')
    members={}
    for p in root.rglob('*'):
        if p.is_symlink() or not (p.is_file() or p.is_dir()): raise AudioError('QA_NONREGULAR_FILE')
        if p.is_file(): members[p.relative_to(root).as_posix()]=p
    if set(members)!=set(index)|{'OUTPUT_SHA256.json'}: raise AudioError('QA_FILE_SET_CHANGED')
    required={'master.wav','MIX_CLOCK.json','MIX_RECEIPT.json','source.wav','SOURCE_SYNC.json','captions.vtt','captions.srt'}
    if not required<=set(index): raise AudioError('QA_REQUIRED_FILE_MISSING')
    files={};total=0
    for name,row in sorted(index.items()):
        q=PurePosixPath(name)
        if type(name)is not str or '\\' in name or q.is_absolute() or any(p in ('','..','.') for p in name.split('/')): raise AudioError('QA_UNSAFE_PATH')
        if type(row)is not dict or set(row)!={'sha256','bytes'} or type(row['bytes'])is not int or row['bytes']<0: raise AudioError('QA_FILE_INDEX')
        total+=row['bytes']
        if total>256000000: raise AudioError('QA_INPUT_BUDGET')
        data=read_regular(root/q,min(64001024,row['bytes']))
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']: raise AudioError('QA_FILE_HASH_CHANGED',name)
        files[name]=data
    mixed=MixedAudio(files['master.wav'],files['MIX_CLOCK.json'].decode(),files['MIX_RECEIPT.json'].decode()).validate()
    sync=restore_sync(strict_json(files['SOURCE_SYNC.json'].decode()),files['source.wav'])
    verify_mixed_source(mixed,sync)
    for ext in ('vtt','srt'):
        if files['captions.'+ext]!=export_mixed_captions(mixed,ext).encode(): raise AudioError('QA_PUBLISHED_CAPTIONS_CHANGED',ext)
    return mixed,sync,files
