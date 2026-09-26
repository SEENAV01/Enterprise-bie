from __future__ import annotations
from dataclasses import dataclass, replace
import hashlib
from typing import Mapping
from ..audio import AudioCue, AudioCueKind, AudioExperienceContract
from ..document import GameDocument, GameLevelContract, GameExperienceContract
from ..errors import GameContractError

@dataclass(frozen=True)
class CanonicalAudioBinding:
    level_id:str
    cues:tuple[AudioCue,...]
    asset_media:tuple[tuple[str,str,str],...]
    rights:tuple[tuple[str,str],...]
    source_refs:tuple[str,...]
    timings:tuple[tuple[str,int,int,str],...]
    reasoning_refs:tuple[str,...]
    def validate(self):
        if not self.level_id or not self.cues: raise GameContractError('GAME_AUDIO_BINDING_REQUIRED')
        AudioExperienceContract(self.cues).validate()
        if not self.asset_media or not self.rights or not self.source_refs or not self.reasoning_refs: raise GameContractError('GAME_AUDIO_BINDING_EVIDENCE')
        return self

def adapt_canonical_audio_handoff(handoff:Mapping,files:Mapping[str,bytes],*,level_id:str,trigger_event:str='level_start')->CanonicalAudioBinding:
    if handoff.get('schema_version')!='bie.audio.compiler-handoff/1': raise GameContractError('GAME_AUDIO_HANDOFF_SCHEMA')
    if handoff.get('real_remotion_render_verified') is not False or handoff.get('product_accepted') is not False: raise GameContractError('GAME_AUDIO_HANDOFF_ACCEPTANCE')
    cfg=handoff.get('compiler_h6') or {}; assets=cfg.get('audio_assets') or []; segs=cfg.get('audio_segments') or []; cues=handoff.get('narration_cues') or []
    by_asset={a['asset_id']:a for a in assets}; by_seg={s['cue_id']:s for s in segs}; out=[]; media=[]; rights=[]; timings=[]; src=set(); reason=set()
    for c in cues:
        seg=by_seg.get(c.get('cue_id')); a=by_asset.get(seg.get('asset_id') if seg else None)
        if not seg or not a: raise GameContractError('GAME_AUDIO_HANDOFF_BINDING')
        path=a.get('public_path'); data=files.get(path)
        if not isinstance(data,(bytes,bytearray)) or hashlib.sha256(data).hexdigest()!=a.get('sha256'): raise GameContractError('GAME_AUDIO_HANDOFF_BYTES')
        if not a.get('rights_ref'): raise GameContractError('GAME_AUDIO_RIGHTS_REQUIRED')
        media_type='audio/wav' if str(path).endswith('.wav') else 'audio/mpeg'
        start=c.get('start_ms');end=c.get('end_ms')
        if type(start) is not int or type(end) is not int or start<0 or end<=start: raise GameContractError('GAME_AUDIO_HANDOFF_TIMING')
        out.append(AudioCue(c['cue_id'],AudioCueKind.NARRATION,trigger_event,a['asset_id'],c['text_ref'],False).validate());timings.append((c['cue_id'],start,end,trigger_event))
        media.append((a['asset_id'],media_type,a['sha256'])); rights.append((a['asset_id'],a['rights_ref']))
        src.update(a.get('source_refs') or ()); reason.update(a.get('reasoning_refs') or ())
    return CanonicalAudioBinding(level_id,tuple(out),tuple(sorted(media)),tuple(sorted(rights)),tuple(sorted(src)),tuple(sorted(timings)),tuple(sorted(reason))).validate()

def attach_audio_binding(doc:GameDocument,binding:CanonicalAudioBinding)->GameDocument:
    binding.validate(); exps=[]; found=False
    for exp in doc.experiences:
        levels=[]
        for level in exp.levels:
            if level.level_id==binding.level_id:
                found=True; level=replace(level,audio=AudioExperienceContract(binding.cues).validate())
            levels.append(level)
        exps.append(replace(exp,levels=tuple(levels)))
    if not found: raise GameContractError('GAME_AUDIO_LEVEL_MISSING')
    return replace(doc,experiences=tuple(exps)).validate()
