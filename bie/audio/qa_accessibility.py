"""QA-005: spoken and authored sound captions, not rendered WCAG acceptance.

Sound meaning and speaker labels must be supplied with source references. They
are not inferred from a waveform or from a filename. The original MIX display
caption channel is retained; this module produces an ADDITIONAL spoken channel.
"""
from dataclasses import dataclass,asdict,replace
from html import escape
from .common import AudioError,integer,text,locale,refs,fingerprint,exact_fields
from .mix_contract import number
from .mix_pipeline import verify_mixed_source
from .caption_alignment import align_captions,timestamp
from .qa_contract import Finding,check,TASKS
from .qa_source import decode

@dataclass(frozen=True)
class CaptionQAPolicy:
    max_chars_per_line:int=42
    max_lines:int=2
    max_chars_per_second:int=22
    min_duration_ms:int=400
    def __post_init__(self):
        for n,a,b in (('max_chars_per_line',8,160),('max_lines',1,6),('max_chars_per_second',1,200),('min_duration_ms',1,5000)):
            integer(getattr(self,n),n,a,b)

@dataclass(frozen=True)
class SpeakerIdentity:
    persona_id:str
    label:str
    source_refs:tuple[str,...]
    def __post_init__(self):
        text(self.persona_id,'persona',2048);text(self.label,'speaker label',160);refs(self.source_refs,'speaker source')
        if '\n' in self.label or '\r' in self.label: raise AudioError('QA_SPEAKER_LINE')

@dataclass(frozen=True)
class SoundMeaning:
    asset_id:str
    meaningful:bool
    caption:str|None
    language:str
    source_refs:tuple[str,...]
    def __post_init__(self):
        text(self.asset_id,'asset id',2048);locale(self.language);refs(self.source_refs,'sound source')
        if type(self.meaningful)is not bool:raise AudioError('QA_SOUND_MEANING')
        if self.meaningful:text(self.caption,'sound caption',4096)
        elif self.caption is not None:raise AudioError('QA_NONMEANINGFUL_CAPTION')


def parse_intent(raw,mixed):
    if raw is None:return (),()
    exact_fields(raw,('schema_version','mix_fingerprint','speakers','sounds'))
    if raw['schema_version']!='bie.audio.caption-intent/1' or raw['mix_fingerprint']!=mixed.receipt()['fingerprint']:raise AudioError('QA_CAPTION_INTENT_STALE')
    speakers=decode(tuple[SpeakerIdentity,...],raw['speakers']);sounds=decode(tuple[SoundMeaning,...],raw['sounds'])
    if len(speakers)>64 or len(sounds)>128:raise AudioError('QA_CAPTION_INTENT_BUDGET')
    if len({s.persona_id for s in speakers})!=len(speakers) or len({s.asset_id for s in sounds})!=len(sounds):raise AudioError('QA_CAPTION_INTENT_DUPLICATE')
    return speakers,sounds


def wrap_unbounded(value,width):
    # No word is truncated to meet a visual policy. Over-limit lines get findings.
    tokens=value.split();lines=[];current=''
    for token in tokens:
        if current and len(current)+1+len(token)>width:lines.append(current);current=token
        else:current=(current+' '+token) if current else token
    if current:lines.append(current)
    return lines


def accessibility_qa(mixed,sync,intent=None,policy=CaptionQAPolicy()):
    verify_mixed_source(mixed,sync)
    if type(policy)is not CaptionQAPolicy:raise AudioError('QA_CAPTION_POLICY')
    CaptionQAPolicy(**asdict(policy));c=mixed.clock();r=mixed.receipt();shift=c['source_start_sample'];rate=c['sample_rate'];fs=[]
    speakers,sounds=parse_intent(intent,mixed);labels={s.persona_id:s.label for s in speakers};personas={s.persona_id for s in sync.plan.segments}
    if set(labels)-personas:raise AudioError('QA_UNKNOWN_SPEAKER')
    if len(personas)>1 and set(labels)!=personas:fs.append(Finding('SPEAKER_IDENTIFICATION_MISSING','FAIL','AUDIO/DIR','speakers','Multiple narration personas need explicit source-bound speaker labels.'))
    expected_stems={s['asset_id']:s for k in ('music','sfx') for s in r[k]['stems']}
    decisions={s.asset_id:s for s in sounds}
    if set(decisions)-set(expected_stems):raise AudioError('QA_UNKNOWN_SOUND')
    for aid in sorted(set(expected_stems)-set(decisions)):
        fs.append(Finding('SOUND_MEANING_UNDECLARED','REVIEW','AUDIO/DIR',aid,'Caption need cannot be guessed; supply an authored sound-meaning decision.',tuple(expected_stems[aid]['source_refs'])))
    source_events=[]
    for asset,aligned,old,place in zip(sync.assets,sync.alignments,sync.captions,sync.timeline.segments):
        s=asset.request.segment
        # Use the existing source-preserving producer with its own explicit layout policy.
        track=align_captions(asset,aligned,replace(old.policy,channel='spoken'))
        label=labels.get(s.persona_id)
        for cue in track.cues:
            a=place.start_sample+cue.start_sample-shift;b=place.start_sample+cue.end_sample-shift
            if not 0<=a<b<=c['total_samples']:raise AudioError('QA_SPOKEN_CAPTION_TRIM_LOSS')
            value=(label+': ' if label else '')+cue.text.strip()
            source_events.append({'kind':'speech','event_id':s.segment_id+':'+cue.cue_id,'segment_id':s.segment_id,
                'start_sample':a,'end_sample':b,'text':value,'exact_source_caption':asdict(cue),
                'source_refs':sorted({v for sp in s.spans for v in sp.source_refs})})
    for aid,meaning in sorted(decisions.items()):
        st=expected_stems[aid]
        if not set(meaning.source_refs)<=set(st['source_refs']):raise AudioError('QA_SOUND_SOURCE_MISMATCH')
        if not meaning.meaningful:continue
        a=st['output_start']-shift;b=st['output_end']-shift
        if not 0<=a<b<=c['total_samples']:raise AudioError('QA_SOUND_CLOCK')
        intervals=[(a,b)]
        if r['policy']['pause_mode']=='all_stems_silent':
            for pause in c['pauses']:
                split=[]
                for lo,hi in intervals:
                    x,y=pause['start_sample'],pause['end_sample']
                    if hi<=x or y<=lo:split.append((lo,hi))
                    else:
                        if lo<x:split.append((lo,x))
                        if y<hi:split.append((y,hi))
                intervals=split
        for i,(lo,hi) in enumerate(intervals):
            source_events.append({'kind':'sound','event_id':f'{aid}:{i}','asset_id':aid,'start_sample':lo,'end_sample':hi,
                'text':'['+meaning.caption+']','language':meaning.language,'source_refs':list(meaning.source_refs)})
    if len(source_events)>20000:raise AudioError('QA_CAPTION_EVENT_BUDGET')
    events={}
    for i,e in enumerate(source_events):
        events.setdefault(e['start_sample'],[[],[]])[0].append(i);events.setdefault(e['end_sample'],[[],[]])[1].append(i)
    active=set();cues=[];ends=sorted(events)
    for a,b in zip(ends,ends[1:]):
        added,removed=events[a];active.difference_update(removed);active.update(added)
        if not active:continue
        indices=sorted(active,key=lambda i:(source_events[i]['kind']!='speech',i))
        texts=[source_events[i]['text'] for i in indices];lines=[line for value in texts for line in wrap_unbounded(value,policy.max_chars_per_line)]
        cue={'cue_id':f'access:{len(cues)+1}','start_sample':a,'end_sample':b,'lines':lines,
             'source_event_ids':[source_events[i]['event_id'] for i in indices]}
        cues.append(cue);path=cue['cue_id']
        if len(lines)>policy.max_lines or any(len(s)>policy.max_chars_per_line for s in lines):fs.append(Finding('CAPTION_REFLOW_REQUIRED','REVIEW','AUDIO/SYNC',path,'Complete speech and sound text exceeds the authored visual policy; nothing was deleted.'))
        if (b-a)*1000<policy.min_duration_ms*rate or len(''.join(lines))*rate>policy.max_chars_per_second*(b-a):fs.append(Finding('CAPTION_READING_TIME_REQUIRED','REVIEW','AUDIO/SYNC',path,'Caption exposure needs review/retiming; limits are an engineering policy, not a universal reading standard.'))
    fs.append(Finding('RENDERED_CAPTION_ACCESSIBILITY_UNVERIFIED','REVIEW','AUDIO/COMP','render','Font shaping, contrast, overlap, placement and player controls need actual rendered/player evidence.'))
    if intent is not None and sounds:fs.append(Finding('SOUND_SEMANTICS_AUTHOR_REPORTED','REVIEW','AUDIO/DIR','sounds','Sound meaning is source-bound authored data, not independently verified perception.'))
    artifact={'schema_version':'bie.audio.accessible-captions/1','media_sha256':c['output_audio_sha256'],'mix_fingerprint':r['fingerprint'],
        'sample_rate':rate,'total_samples':c['total_samples'],'policy':asdict(policy),'speakers':[asdict(s) for s in speakers],
        'sound_decisions':[asdict(s) for s in sounds],'source_events':source_events,'cues':cues,'original_display_captions_retained':True,
        'rendered_accessibility_verified':False,'product_accepted':False}
    artifact['fingerprint']=fingerprint(artifact)
    report=check(TASKS[4],'Additional spoken/sound/speaker caption coverage and readability diagnostics',fs,
        {'caption_artifact_fingerprint':artifact['fingerprint'],'cues':len(cues),'speech_events':sum(e['kind']=='speech' for e in source_events),
         'sound_events':sum(e['kind']=='sound' for e in source_events),'unclassified_stems':sorted(set(expected_stems)-set(decisions)),
         'wcag_compliance_claimed':False})
    return report,artifact


def export_accessible(artifact,format='vtt'):
    if format not in ('vtt','srt'):raise AudioError('QA_CAPTION_FORMAT')
    raw={k:v for k,v in artifact.items() if k!='fingerprint'}
    if artifact.get('fingerprint')!=fingerprint(raw) or artifact.get('schema_version')!='bie.audio.accessible-captions/1' or artifact.get('product_accepted')is not False:raise AudioError('QA_CAPTION_ARTIFACT_CHANGED')
    rate=integer(artifact['sample_rate'],'caption rate',8000,192000);out=['WEBVTT',''] if format=='vtt' else [];last=0
    for n,cue in enumerate(artifact['cues'],1):
        a=integer(cue['start_sample'],'caption start',0,artifact['total_samples']);b=integer(cue['end_sample'],'caption end',a+1,artifact['total_samples'])
        ams=(a*1000+rate//2)//rate;bms=(b*1000+rate//2)//rate
        if a<last or ams>=bms:raise AudioError('QA_CAPTION_EXPORT_ROUNDING')
        if type(cue['lines'])is not list or not cue['lines']:raise AudioError('QA_CAPTION_EXPORT_LINES')
        for s in cue['lines']:
            text(s,'caption line',8192)
            if '\n' in s or '\r' in s:raise AudioError('QA_CAPTION_EXPORT_NEWLINE')
        sep='.' if format=='vtt' else ','
        out.extend((str(n),f'{timestamp(a,rate,sep)} --> {timestamp(b,rate,sep)}','\n'.join(escape(s,quote=False) for s in cue['lines']),''));last=b
    return '\n'.join(out)+'\n'
