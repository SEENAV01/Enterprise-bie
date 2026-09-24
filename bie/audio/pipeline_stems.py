"""H6: bounded, source-bound music/SFX stems for the canonical local AUDIO worker."""
from __future__ import annotations
import base64, hashlib
from dataclasses import asdict
from .common import AudioError, fingerprint, text
from .acoustic_contract import plain
from .mix_contract import MixBuffer
from .sfx_mixing import Stem
from .tts_contract import AudioFormat

MAX_STEMS=32; MAX_STEM_BYTES=8_000_000; MAX_TOTAL_BYTES=24_000_000

def canonicalize_stem_specs(specs):
    if type(specs) is not list or len(specs)>MAX_STEMS: raise AudioError('PIPELINE_STEMS')
    out=[]; total=0; ids=set()
    for raw in specs:
        if type(raw) is not dict: raise AudioError('PIPELINE_STEM_SPEC')
        allowed={'asset_id','role','wav_b64','wav_sha256','start_sample','trim_start','trim_end','source_refs','rights_ref','gain_db','channel_map','pan','repeat','fade_in_samples','fade_out_samples'}
        if set(raw)!=allowed: raise AudioError('PIPELINE_STEM_FIELDS')
        aid=text(raw['asset_id'],'asset',256)
        if aid in ids: raise AudioError('PIPELINE_STEM_DUPLICATE');
        ids.add(aid)
        if raw['role'] not in ('music','sfx'): raise AudioError('PIPELINE_STEM_ROLE')
        try: data=base64.b64decode(raw['wav_b64'],validate=True)
        except Exception as e: raise AudioError('PIPELINE_STEM_BASE64') from e
        if not data or len(data)>MAX_STEM_BYTES: raise AudioError('PIPELINE_STEM_SIZE')
        total+=len(data)
        if total>MAX_TOTAL_BYTES: raise AudioError('PIPELINE_STEM_TOTAL_SIZE')
        h=hashlib.sha256(data).hexdigest()
        if raw['wav_sha256']!=h: raise AudioError('PIPELINE_STEM_HASH')
        refs=raw['source_refs']
        if type(refs) is not list or not refs or any(type(x)is not str or not x for x in refs): raise AudioError('PIPELINE_STEM_PROVENANCE')
        text(raw['rights_ref'],'rights',4096)
        row=plain(raw); row['source_refs']=sorted(set(refs)); out.append(row)
    return sorted(out,key=lambda x:x['asset_id'])

def decode_stems(specs,fmt:AudioFormat):
    rows=canonicalize_stem_specs(specs); result=[]
    for r in rows:
        data=base64.b64decode(r['wav_b64']); pcm=MixBuffer.from_wav(data,fmt)
        kwargs={k:r[k] for k in ('asset_id','role','start_sample','trim_start','trim_end','rights_ref','gain_db','channel_map','pan','repeat','fade_in_samples','fade_out_samples')}
        kwargs['source_refs']=tuple(r['source_refs']); result.append(Stem(pcm=pcm,**kwargs))
    return tuple(result)

def stems_fingerprint(specs): return fingerprint(canonicalize_stem_specs(specs))
