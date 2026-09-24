"""BIE-AUDIO-SYNC-002: source-preserving captions over observed word onsets.

Caption fitting is a bounded engineering policy, not accessibility acceptance.
Timing cannot be inferred from word lengths. Display and spoken text stay separate.
"""
from __future__ import annotations
from dataclasses import dataclass
from html import escape
import re
from .common import AudioError, digest, fingerprint, integer, text
from .speech_contract import records
from .sync_contract import AlignedSpeech, MAX_SAMPLES, validate_alignment, ceil_div

@dataclass(frozen=True)
class CaptionPolicy:
    channel: str = 'spoken'
    max_chars_per_line: int = 42
    max_lines: int = 2
    max_duration_ms: int = 6000
    min_duration_ms: int = 80
    max_gap_ms: int = 800
    max_chars_per_second: int = 60
    def __post_init__(self):
        if self.channel not in ('spoken','display'): raise AudioError('CAPTION_CHANNEL')
        for k,lo,hi in (('max_chars_per_line',8,160),('max_lines',1,4),('max_duration_ms',500,20000),
                        ('min_duration_ms',1,5000),('max_gap_ms',0,5000),('max_chars_per_second',1,200)):
            integer(getattr(self,k),k,lo,hi)
        if self.min_duration_ms>self.max_duration_ms: raise AudioError('CAPTION_DURATION_POLICY')


def layout_lines(value,policy):
    """Line wrapping changes presentation whitespace only; raw text remains intact."""
    tokens=re.findall(r'\S+',value); lines=[];line=''
    for token in tokens:
        if len(token)>policy.max_chars_per_line: raise AudioError('CAPTION_RESEGMENT_REQUIRED','indivisible token too wide')
        if line and len(line)+1+len(token)>policy.max_chars_per_line: lines.append(line);line=token
        else: line=(line+' '+token) if line else token
    if line:lines.append(line)
    if not lines or len(lines)>policy.max_lines: raise AudioError('CAPTION_REFLOW_REQUIRED')
    return tuple(lines)


@dataclass(frozen=True)
class CaptionCue:
    cue_id: str
    start_char: int
    end_char: int
    text: str
    lines: tuple[str,...]
    start_sample: int
    end_sample: int
    word_indexes: tuple[int,...]
    def __post_init__(self):
        text(self.cue_id,'cue id',2048)
        integer(self.start_char,'caption char start');integer(self.end_char,'caption char end',1)
        if type(self.text)is not str or self.end_char-self.start_char!=len(self.text):raise AudioError('CAPTION_TEXT_RANGE')
        if type(self.lines)is not tuple or not self.lines or any(type(x)is not str for x in self.lines):raise AudioError('CAPTION_LINES')
        integer(self.start_sample,'caption start',0,MAX_SAMPLES);integer(self.end_sample,'caption end',1,MAX_SAMPLES)
        if self.end_sample<=self.start_sample:raise AudioError('CAPTION_TIME_RANGE')
        if type(self.word_indexes)is not tuple or not self.word_indexes or any(type(x)is not int or x<0 for x in self.word_indexes):raise AudioError('CAPTION_WORD_COVERAGE')

@dataclass(frozen=True)
class CaptionTrack:
    segment_id: str
    alignment_fingerprint: str
    source_text: str
    sample_rate: int
    provider_samples: int
    policy: CaptionPolicy
    cues: tuple[CaptionCue,...]
    schema_version: str = 'bie.audio.caption-track/1'
    def __post_init__(self):
        digest(self.alignment_fingerprint);records(self.cues,CaptionCue,'caption cues',limit=20000)
        if type(self.policy)is not CaptionPolicy or self.schema_version!='bie.audio.caption-track/1': raise AudioError('CAPTION_SCHEMA')
        integer(self.sample_rate,'rate',8000,192000);integer(self.provider_samples,'samples',1,MAX_SAMPLES)
        position=0;end=0;word_index=0
        for cue in self.cues:
            if cue.start_char!=position or cue.end_char<=position or cue.text!=self.source_text[position:cue.end_char]: raise AudioError('CAPTION_TEXT_COVERAGE')
            if cue.lines!=layout_lines(cue.text,self.policy): raise AudioError('CAPTION_LAYOUT_CHANGED')
            if type(cue.start_sample)is not int or type(cue.end_sample)is not int or not end<=cue.start_sample<cue.end_sample<=self.provider_samples: raise AudioError('CAPTION_TIME_RANGE')
            if type(cue.word_indexes)is not tuple or not cue.word_indexes or cue.word_indexes!=tuple(range(word_index,word_index+len(cue.word_indexes))): raise AudioError('CAPTION_WORD_COVERAGE')
            word_index+=len(cue.word_indexes);position=cue.end_char;end=cue.end_sample
        if position!=len(self.source_text) or len({c.cue_id for c in self.cues})!=len(self.cues): raise AudioError('CAPTION_INCOMPLETE')
    def fingerprint(self):return fingerprint(self)


def caption_atoms(segment,aligned,channel):
    words=aligned.words
    if channel=='spoken':
        source=segment.spoken_text
        atoms=[(0 if i==0 else w.spoken_start,
                words[i+1].spoken_start if i+1<len(words) else len(source),
                w.start_sample,w.end_sample,(i,)) for i,w in enumerate(words)]
        return source,atoms
    source=segment.display_text;groups=[]
    for w in words:
        a=min(s.start for s in w.source)-segment.start;b=max(s.end for s in w.source)-segment.start
        if groups and a<groups[-1][1]:
            old=groups[-1]; groups[-1]=(old[0],max(old[1],b),old[2],w.end_sample,old[4]+(w.index,))
        else:groups.append((a,b,w.start_sample,w.end_sample,(w.index,)))
    return source,[(0 if i==0 else g[0],groups[i+1][0] if i+1<len(groups) else len(source),g[2],g[3],g[4]) for i,g in enumerate(groups)]


def align_captions(asset,aligned:AlignedSpeech,policy=CaptionPolicy(),*,require_measured=True):
    validate_alignment(asset,aligned,require_measured=require_measured)
    if type(policy)is not CaptionPolicy:raise AudioError('CAPTION_POLICY_REQUIRED')
    s=asset.request.segment;source,atoms=caption_atoms(s,aligned,policy.channel)
    cues=[];group=[];rate=aligned.sample_rate
    def fits(rows):
        a,b,start,end=rows[0][0],rows[-1][1],rows[0][2],rows[-1][3]
        try:layout_lines(source[a:b],policy)
        except AudioError:return False
        return (end-start)*1000<=policy.max_duration_ms*rate
    def finish(rows):
        a,b,start,end=rows[0][0],rows[-1][1],rows[0][2],rows[-1][3]
        value=source[a:b]; lines=layout_lines(value,policy)
        if (end-start)*1000<policy.min_duration_ms*rate:raise AudioError('CAPTION_EXTENSION_REQUIRED','duration below policy')
        if len(''.join(lines))*rate>policy.max_chars_per_second*(end-start):raise AudioError('CAPTION_EXTENSION_REQUIRED','reading rate above policy')
        if not fits(rows):raise AudioError('CAPTION_RESEGMENT_REQUIRED','atom longer than allowed cue')
        indexes=tuple(i for r in rows for i in r[4])
        cues.append(CaptionCue(f'caption:{len(cues)+1}',a,b,value,lines,start,end,indexes))
    for atom in atoms:
        gap=(atom[2]-group[-1][3])*1000 if group else 0
        if group and (gap>policy.max_gap_ms*rate or not fits(group+[atom])):finish(group);group=[]
        if not fits([atom]):raise AudioError('CAPTION_RESEGMENT_REQUIRED','required content will not be dropped')
        group.append(atom)
    if group:finish(group)
    return CaptionTrack(s.segment_id,aligned.fingerprint(),source,rate,aligned.provider_samples,policy,tuple(cues))


def timestamp(sample,rate,separator='.'):
    ms=(sample*1000+rate//2)//rate
    h,rest=divmod(ms,3600000);m,rest=divmod(rest,60000);s,ms=divmod(rest,1000)
    return f'{h:02}:{m:02}:{s:02}{separator}{ms:03}'


def export_captions(tracks,offsets,*,format='vtt'):
    """Round shared sample boundaries identically; escape literal caption markup."""
    if format not in ('vtt','srt') or type(tracks)is not tuple or not tracks or type(offsets)is not tuple or len(tracks)!=len(offsets):raise AudioError('CAPTION_EXPORT_INPUT')
    if any(type(t)is not CaptionTrack for t in tracks) or len({t.sample_rate for t in tracks})!=1:
        raise AudioError('CAPTION_EXPORT_SHARED_CLOCK_REQUIRED')
    out=['WEBVTT',''] if format=='vtt' else [];counter=0;last_ms=0
    for track,offset in zip(tracks,offsets):
        if type(track)is not CaptionTrack:raise AudioError('CAPTION_TRACK_REQUIRED')
        # Revalidate before serializing rather than trust an old receipt flag.
        CaptionTrack(**track.__dict__);integer(offset,'offset',0,MAX_SAMPLES)
        for cue in track.cues:
            a,b=offset+cue.start_sample,offset+cue.end_sample;rate=track.sample_rate
            ams=(a*1000+rate//2)//rate;bms=(b*1000+rate//2)//rate
            if ams<last_ms or bms<=ams:raise AudioError('CAPTION_EXPORT_ROUNDING_COLLISION')
            counter+=1;sep='.' if format=='vtt' else ','
            out.extend([str(counter),f'{timestamp(a,rate,sep)} --> {timestamp(b,rate,sep)}',
                        '\n'.join(escape(line,quote=False) for line in cue.lines),''])
            last_ms=bms
    return '\n'.join(out)+'\n'
