"""HARD021 actual PCM/caption and independent acoustic evidence binding.

Waveform offset estimates compare content against a supplied reference recording;
they are not ASR, word-boundary detection or pronunciation judgments. Forced
alignment/listening evidence must be independently provisioned and authenticated.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from fractions import Fraction
import hashlib,unicodedata
import numpy as np
from .common import *
from ..audio_v2.pcm import read_pcm
from ..audio_v2.captions import parse_captions,normalized


@dataclass(frozen=True)
class SpeechPolicy:
    language:str
    voice_id:str
    pronunciation_forms:tuple[tuple[str,tuple[str,...]],...]
    max_sync_ms:int=80
    min_word_ms:int=20
    max_age:int=86400
    min_signal:int=64
    max_clipped_ppm:int=1000
    def __post_init__(self):
        token(self.language,'language');token(self.voice_id,'voice')
        integer(self.max_sync_ms,'sync',0,1000);integer(self.min_word_ms,'word_ms',1,5000)
        integer(self.max_age,'age',1,604800);integer(self.min_signal,'signal',1,32000)
        integer(self.max_clipped_ppm,'clipping',0,1000000)
        require(type(self.pronunciation_forms)is tuple and len(self.pronunciation_forms)<=4096,'H5_PRONUNCIATION_POLICY')
        ids=[]
        for word_id,forms in self.pronunciation_forms:
            token(word_id,'word_id');require(type(forms)is tuple and 1<=len(forms)<=16,'H5_APPROVED_FORMS')
            for form in forms:text(form,'form',256)
            ids.append(word_id)
        require(len(set(ids))==len(ids),'H5_PRONUNCIATION_DUPLICATE')


def waveform_offset(reference,current,*,max_shift_ms=1000,hop_ms=10):
    """Bounded envelope correlation; estimate only, not proof of correct speech."""
    a=read_pcm(reference);b=read_pcm(current)
    require((a.sample_rate,a.channels)==(b.sample_rate,b.channels),'H5_WAVEFORM_PROFILE')
    integer(max_shift_ms,'shift',1,5000);integer(hop_ms,'hop',1,50)
    require(max(a.samples,b.samples)<=a.sample_rate*30,'H5_CORRELATION_DURATION_BUDGET')
    hop=max(1,a.sample_rate*hop_ms//1000)
    def envelope(p):
        x=np.frombuffer(p.data,dtype='<i2').astype(np.float64).reshape(-1,p.channels)
        x=np.max(np.abs(x),axis=1);n=len(x)//hop
        require(n>=20,'H5_WAVEFORM_TOO_SHORT')
        return np.sqrt((x[:n*hop].reshape(n,hop)**2).mean(axis=1))
    x=envelope(a);y=envelope(b);limit=max_shift_ms//hop_ms;rows=[]
    for lag in range(-limit,limit+1):
        start_x=max(0,-lag);start_y=max(0,lag);n=min(len(x)-start_x,len(y)-start_y)
        if n<20 or n<min(len(x),len(y))*3//4:continue
        xx=x[start_x:start_x+n];yy=y[start_y:start_y+n]
        denom=float(np.linalg.norm(xx)*np.linalg.norm(yy))
        if denom<=1:continue
        score=float(np.dot(xx,yy)/denom);rows.append((score,lag,n))
    require(bool(rows),'H5_WAVEFORM_NO_SIGNAL')
    rows.sort(reverse=True);best=rows[0]
    alternatives=[r[0] for r in rows if abs(r[1]-best[1])>=3]
    margin=best[0]-max(alternatives,default=0)
    # Near ties and low similarity abstain; do not return a precise trustworthy lag.
    certain=best[0]>=0.98 and margin>=0.01
    return {'status':'ESTIMATE' if certain else 'AMBIGUOUS','offset_samples':best[1]*hop if certain else None,
            'offset_ms':best[1]*hop_ms if certain else None,'hop_samples':hop,
            'similarity_ppm':round(best[0]*1000000),'separation_ppm':round(margin*1000000),
            'phonetic_alignment_proven':False,'pronunciation_verified':False}


def inspect_speech(root,audio,transcript,captions,acoustic_ref,binding,policy,*,caption_format='srt',review=None,verifier=ReviewVerifier(),now=0):
    policy_binding(binding,policy);integer(now,'now');findings=[]
    refs=(audio,transcript,captions,acoustic_ref)
    require(all(type(r)is ArtifactRef for r in refs),'H5_SPEECH_REFS')
    require(len({r.artifact_id for r in refs})==4 and len({r.path for r in refs})==4,'H5_SPEECH_ALIAS')
    with SnapshotStore(root) as store:
        audio_bytes=store.read(audio);words=store.read(transcript).decode('utf-8');cue_bytes=store.read(captions);r=strict_json(store.read(acoustic_ref))
    pcm=read_pcm(audio_bytes);cues=parse_captions(cue_bytes,caption_format);stats=pcm.stats()
    if stats['peak']<policy.min_signal:fail(findings,'H5_SPEECH_SILENT')
    if stats['clipped']*1000000>stats['values']*policy.max_clipped_ppm:fail(findings,'H5_SPEECH_CLIPPING')
    fields(r,('schema_version','binding','audio_sha256','transcript_sha256','language','voice_id','basis','assessor_id','model_version','issued_at','expires_at','segments'),'H5_ACOUSTIC_FIELDS')
    require(r['schema_version']=='bie.qa.acoustic-observations/1','H5_ACOUSTIC_SCHEMA');binding_matches(r['binding'],binding)
    require((r['audio_sha256'],r['transcript_sha256'],r['language'],r['voice_id'])==(audio.sha256,transcript.sha256,policy.language,policy.voice_id),'H5_ACOUSTIC_IDENTITY')
    token(r['assessor_id'],'assessor');token(r['model_version'],'model')
    integer(r['issued_at'],'issued_at');integer(r['expires_at'],'expires_at')
    require(r['issued_at']<=now<r['expires_at'] and now-r['issued_at']<=policy.max_age and 0<r['expires_at']-r['issued_at']<=policy.max_age,'H5_ACOUSTIC_FRESHNESS')
    require(r['basis'] in ('INDEPENDENT_FORCED_ALIGNMENT','HUMAN_LISTENING','ENGINE_TIMESTAMP','ASR_TRANSCRIPT','SYNTHETIC'),'H5_ACOUSTIC_BASIS')
    independent=r['basis'] in ('INDEPENDENT_FORCED_ALIGNMENT','HUMAN_LISTENING')
    if not independent:findings.append(Finding('H5_ACOUSTIC_INDEPENDENT_EVIDENCE_REQUIRED',audio.artifact_id))
    segments=items(r['segments'],'SEGMENTS',1,4096);unique(segments,'word_id','H5_WORD_DUPLICATE')
    approved_forms=dict(policy.pronunciation_forms);seen_forms=set();covered=set();end_sample=-1;char_end=0
    for s in segments:
        fields(s,('word_id','char_start','char_end','start_sample','end_sample','heard_form','verdict'),'H5_WORD_FIELDS')
        text(s['heard_form'],'heard_form',256);token(s['word_id'],'word');integer(s['char_start'],'char_start',0,len(words));integer(s['char_end'],'char_end',1,len(words))
        integer(s['start_sample'],'start_sample',0,pcm.samples-1);integer(s['end_sample'],'end_sample',1,pcm.samples)
        require(s['char_start']<s['char_end'] and s['char_start']>=char_end and s['start_sample']>=end_sample and s['start_sample']<s['end_sample'],'H5_WORD_ORDER')
        char_end=s['char_end'];end_sample=s['end_sample'];covered.update(range(s['char_start'],s['char_end']))
        if 1000*(s['end_sample']-s['start_sample'])<policy.min_word_ms*pcm.sample_rate:fail(findings,'H5_WORD_WINDOW_SHORT',s['word_id'])
        if not pcm.has_signal(s['start_sample'],s['end_sample']):fail(findings,'H5_WORD_WINDOW_SILENT',s['word_id'])
        require(s['verdict'] in ('VERIFIED','REJECTED','UNCERTAIN'),'H5_WORD_VERDICT')
        if s['verdict']=='REJECTED':fail(findings,'H5_PRONUNCIATION_REJECTED',s['word_id'])
        if s['verdict']=='UNCERTAIN':findings.append(Finding('H5_PRONUNCIATION_UNCERTAIN',s['word_id']))
        if s['word_id'] in approved_forms:
            seen_forms.add(s['word_id'])
            if s['heard_form'] not in approved_forms[s['word_id']]:fail(findings,'H5_PRONUNCIATION_FORM',s['word_id'])
    require(seen_forms==set(approved_forms),'H5_PRONUNCIATION_OCCURRENCE_MISSING')
    if any(unicodedata.category(c)[0] in ('L','M','N','S') and i not in covered for i,c in enumerate(words)):fail(findings,'H5_ACOUSTIC_WORD_COVERAGE')
    cursor=0;last_end=-1
    for cue in cues:
        if cue.start_ms<last_end:fail(findings,'H5_CAPTION_OVERLAP',cue.cue_id)
        last_end=cue.end_ms
        # Consume a contiguous sequence of independently aligned word occurrences.
        text_parts=[];begin=cursor
        while cursor<len(segments) and len(normalized(' '.join(text_parts)))<len(normalized(cue.text)):
            s=segments[cursor];text_parts.append(words[s['char_start']:s['char_end']]);cursor+=1
        if normalized(' '.join(text_parts))!=normalized(cue.text):fail(findings,'H5_CAPTION_TRANSCRIPT',cue.cue_id)
        if cursor>begin:
            first=segments[begin];last=segments[cursor-1]
            if abs(Fraction(cue.start_ms)-Fraction(1000*first['start_sample'],pcm.sample_rate))>policy.max_sync_ms or abs(Fraction(cue.end_ms)-Fraction(1000*last['end_sample'],pcm.sample_rate))>policy.max_sync_ms:
                fail(findings,'H5_CAPTION_ACOUSTIC_OFFSET',cue.cue_id)
        if Fraction(cue.end_ms)>pcm.duration_ms:fail(findings,'H5_CAPTION_BEYOND_AUDIO',cue.cue_id)
    if cursor!=len(segments):fail(findings,'H5_CAPTION_WORD_COVERAGE')
    request_digest=digest({'binding':asdict(binding),'refs':[a.to_dict() for a in refs],'acoustic':r})
    auth=approved(review,verifier,subject=audio.artifact_id,purpose='support',request_digest=request_digest,policy_digest=binding.policy_digest,now=now,evidence_ids=tuple(a.artifact_id for a in refs),max_age=policy.max_age)
    if auth=='BLOCKED':fail(findings,'H5_ACOUSTIC_REVIEW_INVALID')
    elif auth!='VERIFIED':findings.append(Finding('H5_ACOUSTIC_REVIEW_REQUIRED',audio.artifact_id))
    if review is not None and review.evaluator_id!=r['assessor_id']:fail(findings,'H5_ACOUSTIC_ASSESSOR_MISMATCH')
    return findings_report('BIE-QA-HARD-021',binding,findings,{'request_digest':request_digest,'basis':r['basis'],'review':auth,
        'words':len(segments),'captions':len(cues),'pcm_samples':pcm.samples,'sample_rate':pcm.sample_rate,
        'independent_acoustic_evidence_authenticated':independent and auth=='VERIFIED',
        'rendered_caption_legibility_verified':False,'final_mux_playback_verified':False},refs)
