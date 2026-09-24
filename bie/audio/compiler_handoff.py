"""H10-002: AUDIO -> current canonical COMP narration contract adapter.

Produces the exact compiler_h6/narration_cues shape observed at the pinned canonical
repository identity. Audio is cut from the final mixed waveform, not re-synthesized.
Frame quantization may require trailing silence padding; speech is never truncated.
"""
from __future__ import annotations
import hashlib, io, json, math, wave
from .common import AudioError, fingerprint
from .mix_contract import MixBuffer
from .speech_contract import SpeechPlan
from .tts_contract import AudioFormat

SCHEMA='bie.audio.compiler-handoff/1'
CANONICAL_MAIN='dfc1ef9b59bf7d3a8f099a8ad2fb4a93895257e8'
CANONICAL_BLOBS={
 'bie/compiler/frame_runtime_contract.py':'e8a713f05fe6042b02b712f6f99d1e400d168ab9',
 'bie/compiler/narration_consumer.py':'63ce70dc16b304f7c4051bcbd624efda81015e33',
 'bie/compiler/qa_scene_compile.py':'10ecd8e7485256b8b3e313c2b4935543544f487c',
 'bie/compiler/media_presentation.py':'30f4ce61b968886be4c7b3b540bb8fc92447615e',
}

def _ceil_ms(samples,rate): return (samples*1000+rate-1)//rate

def _frame_at(ms,fps): return (ms*fps+999)//1000

def _pad_wav(source:MixBuffer,start,end,required_frames):
    cut=source.slice(start,end)
    if required_frames<cut.frames: raise AudioError('COMP_HANDOFF_WOULD_TRUNCATE')
    if required_frames==cut.frames:return cut.to_wav(),0
    import numpy as np
    a=cut.array(); pad=np.zeros((required_frames-cut.frames,cut.channels),dtype='<f8')
    return MixBuffer.from_array(np.concatenate([a,pad],axis=0),cut.sample_rate).to_wav(),required_frames-cut.frames

def build_compiler_handoff(plan:SpeechPlan, master_wav:bytes, mixed_clock:dict, *, fps:int,
                           caption_target_id:str, target_ids_by_scene:dict, rights_ref:str,
                           reasoning_refs:tuple[str,...], narration_revision:int=1):
    if type(plan) is not SpeechPlan:raise AudioError('COMP_HANDOFF_PLAN_REQUIRED')
    plan.require_ready()
    if type(fps)is not int or not 1<=fps<=240:raise AudioError('COMP_HANDOFF_FPS')
    if type(caption_target_id)is not str or not caption_target_id:raise AudioError('COMP_HANDOFF_CAPTION_TARGET')
    if type(target_ids_by_scene)is not dict:raise AudioError('COMP_HANDOFF_TARGETS')
    if type(reasoning_refs)is not tuple or not reasoning_refs:raise AudioError('COMP_HANDOFF_REASONING_REFS')
    if mixed_clock.get('schema_version')!='bie.audio.mixed-clock/1' or mixed_clock.get('plan_fingerprint')!=plan.fingerprint():
        raise AudioError('COMP_HANDOFF_CLOCK_BINDING')
    rate=mixed_clock.get('sample_rate'); channels=mixed_clock.get('channels')
    master=MixBuffer.from_wav(master_wav,AudioFormat(rate,channels))
    if master.frames!=mixed_clock.get('total_samples') or hashlib.sha256(master_wav).hexdigest()!=mixed_clock.get('output_audio_sha256'):
        raise AudioError('COMP_HANDOFF_MASTER_BINDING')
    by_clock={x['segment_id']:x for x in mixed_clock.get('segments',[])}
    texts={};assets=[];segments=[];cues=[];files={};evidence=[]
    for i,s in enumerate(plan.segments):
        c=by_clock.get(s.segment_id)
        if c is None:raise AudioError('COMP_HANDOFF_SEGMENT_MISSING')
        start,end=c['start_sample'],c['end_sample']
        if not (0<=start<end<=master.frames):raise AudioError('COMP_HANDOFF_SAMPLE_RANGE')
        start_ms=_ceil_ms(start,rate); end_ms=_ceil_ms(end,rate)
        fs,fe=_frame_at(start_ms,fps),_frame_at(end_ms,fps)
        if fe<=fs:raise AudioError('COMP_HANDOFF_CUE_COLLAPSED')
        needed=( (fe-fs)*rate + fps-1)//fps
        wav,pad=_pad_wav(master,start,end,needed)
        sha=hashlib.sha256(wav).hexdigest(); asset_id='audio:'+sha; public='narration/'+sha+'.wav'
        src=[]
        for sp in s.spans:
            for r in sp.source_refs:
                if r not in src:src.append(r)
        text_ref='transcript:'+s.segment_id
        texts[text_ref]={'text':s.display_text,'source_refs':src,'reasoning_refs':list(reasoning_refs)}
        assets.append({'asset_id':asset_id,'public_path':public,'sha256':sha,'byte_length':len(wav),
            'sample_rate':rate,'channels':channels,'sample_width':2,'frame_count':needed,
            'rights_ref':rights_ref,'source_refs':src,'reasoning_refs':list(reasoning_refs)})
        cue_id='cue:'+s.segment_id
        segments.append({'cue_id':cue_id,'asset_id':asset_id,'trim_before_frames':0,'volume':1.0,
            'transcript_sha256':hashlib.sha256(s.display_text.encode()).hexdigest()})
        targets=target_ids_by_scene.get(s.scene_id)
        if type(targets) is not tuple or not targets:raise AudioError('COMP_HANDOFF_SCENE_TARGETS')
        cues.append({'cue_id':cue_id,'start_ms':start_ms,'end_ms':end_ms,'text_ref':text_ref,
            'narration_revision':narration_revision,'target_ids':list(targets)})
        files[public]=wav
        evidence.append({'segment_id':s.segment_id,'mixed_start_sample':start,'mixed_end_sample':end,
            'source_samples':end-start,'published_samples':needed,'pad_samples':pad,'speech_truncated':False,
            'start_ms':start_ms,'end_ms':end_ms,'start_frame':fs,'end_frame':fe})
    cfg={'schema_version':'bie.comp-frame-runtime.v1','narration_revision':narration_revision,
         'narration_texts':texts,'audio_assets':assets,'audio_segments':segments,'caption_target_id':caption_target_id}
    handoff={'schema_version':SCHEMA,'canonical_main':CANONICAL_MAIN,'canonical_compiler_blobs':CANONICAL_BLOBS,
        'compiler_h6':cfg,'narration_cues':cues,'published_files':sorted(files),'sample_evidence':evidence,
        'mixed_clock_fingerprint':fingerprint(mixed_clock),'speech_plan_fingerprint':plan.fingerprint(),
        'real_remotion_render_verified':False,'product_accepted':False}
    handoff['fingerprint']=fingerprint(handoff)
    validate_compiler_handoff(handoff,files)
    return handoff,files

def validate_compiler_handoff(handoff,files):
    if type(handoff)is not dict or handoff.get('schema_version')!=SCHEMA or handoff.get('canonical_main')!=CANONICAL_MAIN:raise AudioError('COMP_HANDOFF_SCHEMA')
    if handoff.get('canonical_compiler_blobs')!=CANONICAL_BLOBS:raise AudioError('COMP_HANDOFF_CANONICAL_IDENTITY')
    cfg=handoff.get('compiler_h6',{}); required={'schema_version','narration_revision','narration_texts','audio_assets','audio_segments','caption_target_id'}
    if set(cfg)!=required or cfg['schema_version']!='bie.comp-frame-runtime.v1':raise AudioError('COMP_HANDOFF_COMPILER_FIELDS')
    if len(cfg['audio_assets'])!=len(cfg['audio_segments']) or len(cfg['audio_segments'])!=len(handoff.get('narration_cues',[])):raise AudioError('COMP_HANDOFF_COVERAGE')
    asset_by={a['asset_id']:a for a in cfg['audio_assets']}
    for a in cfg['audio_assets']:
        if set(a)!={'asset_id','public_path','sha256','byte_length','sample_rate','channels','sample_width','frame_count','rights_ref','source_refs','reasoning_refs'}:raise AudioError('COMP_HANDOFF_ASSET_FIELDS')
        if a['public_path']!='narration/'+a['sha256']+'.wav' or a['public_path'] not in files:raise AudioError('COMP_HANDOFF_ASSET_PATH')
        data=files[a['public_path']]
        if hashlib.sha256(data).hexdigest()!=a['sha256'] or len(data)!=a['byte_length']:raise AudioError('COMP_HANDOFF_ASSET_BYTES')
    for seg in cfg['audio_segments']:
        if set(seg)!={'cue_id','asset_id','trim_before_frames','volume','transcript_sha256'} or seg['asset_id'] not in asset_by:raise AudioError('COMP_HANDOFF_SEGMENT_FIELDS')
    for cue in handoff['narration_cues']:
        if set(cue)!={'cue_id','start_ms','end_ms','text_ref','narration_revision','target_ids'} or cue['text_ref'] not in cfg['narration_texts']:raise AudioError('COMP_HANDOFF_CUE_FIELDS')
        if cue['end_ms']<=cue['start_ms'] or not cue['target_ids']:raise AudioError('COMP_HANDOFF_CUE_RANGE')
    if handoff.get('real_remotion_render_verified') is not False or handoff.get('product_accepted') is not False:raise AudioError('COMP_HANDOFF_ACCEPTANCE_BOUNDARY')
    core={k:v for k,v in handoff.items() if k!='fingerprint'}
    if handoff.get('fingerprint')!=fingerprint(core):raise AudioError('COMP_HANDOFF_FINGERPRINT')
    return handoff
