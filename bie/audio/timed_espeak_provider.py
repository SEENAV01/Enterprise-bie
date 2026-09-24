"""SYNC-001 additive, explicitly identified timed-speech eSpeak adapter.

eSpeak WORD offsets can be wrong after some punctuation/voice boundaries. This
adapter inserts owned lexical MARK pairs and records their native callbacks.
Marks can affect prosody: this is a DIFFERENT runtime/cache identity, never an
alignment transplanted onto an older waveform. No old VO-009 bytes are changed.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
from threading import Event
from xml.sax.saxutils import escape
import hashlib,uuid,unicodedata,time
from .common import AudioError,fingerprint,is_word
from .espeak_provider import EspeakProvider
from .tts_contract import ProviderAudio,ProviderFailure
from .pcm_audio import validate_wav,encode_pcm
from .word_timestamps import _run_worker
from .sync_contract import (AlignedSpeech,WordStamp,source_slices,samples_for_ms,
                            validate_asset,validate_alignment)


def lexical_ranges(value):
    """Versioned Unicode lexical units; not a general CJK linguistic tokenizer."""
    ranges=[];i=0
    while i<len(value):
        if unicodedata.category(value[i])[0] in 'LMN' or value[i] in '&%#@' or unicodedata.category(value[i]) in ('Sm','So','Sc'):
            a=i;i+=1
            while i<len(value) and is_word(value[i]):i+=1
            # Trailing quote punctuation is outside the spoken lexical unit.
            while i>a+1 and value[i-1] in "_'’":i-=1
            ranges.append((a,i))
        else:i+=1
    if not ranges or len(ranges)>20000:raise AudioError('TIMED_LEXICAL_LIMIT')
    return tuple(ranges)


def marked_markup(provider,request,*,start=0,stop=None):
    # Keep all existing authorization/SSML-safety checks, even though we emit
    # a separate markup variant with its own catalog/runtime identity.
    provider._serialize_unmarked(request)
    value=request.segment.spoken_text;words=lexical_ranges(value)
    stop=len(value) if stop is None else stop
    aliases={l.language:l.engine_voice for l in request.voice.locales};runs=[];cursor=0
    for span in request.segment.spans:
        engine=aliases[span.language];span_stop=cursor+len(span.spoken)
        if runs and runs[-1][2]==engine:runs[-1]=(runs[-1][0],span_stop,engine)
        else:runs.append((cursor,span_stop,engine))
        cursor=span_stop
    for a,b in words:
        if not any(x<=a<b<=y for x,y,_ in runs):raise AudioError('TIMING_LANGUAGE_SPLITS_WORD')
    starts={a:i for i,(a,b) in enumerate(words)};ends={b:i for i,(a,b) in enumerate(words)}
    parts=[f'<speak version="1.0" xml:lang="{request.segment.language}">']
    for a,b,engine in runs:
        a,b=max(a,start),min(b,stop)
        if a>=b:continue
        parts.append(f'<voice name="{engine}">')
        for i in range(a,b):
            if i in starts:parts.append(f'<mark name="bie_w{starts[i]}_start"/>')
            parts.append(escape(value[i]))
            if i+1 in ends:parts.append(f'<mark name="bie_w{ends[i+1]}_end"/>')
        parts.append('</voice>')
    parts.append('</speak>');markup=''.join(parts)
    if len(markup.encode())>160000:raise AudioError('TIMED_MARKUP_BUDGET','upstream segmentation must produce a smaller segment')
    return markup,words


class TimedEspeakProvider(EspeakProvider):
    provider_id='espeak-timed-local'
    def __init__(self,*args,**kwargs):
        self.timing_calls=0;super().__init__(*args,**kwargs)
    def _snapshot(self):
        result=super()._snapshot()
        result['timed_adapter']='bie.espeak-mark-timing/1'
        result['timed_adapter_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['timing_supervisor_sha256']=hashlib.sha256(Path(__file__).with_name('word_timestamps.py').read_bytes()).hexdigest()
        result['timing_worker_sha256']=hashlib.sha256(Path(__file__).with_name('espeak_timing_worker.py').read_bytes()).hexdigest()
        return result
    def _make_catalog(self):
        cat=super()._make_catalog()
        return replace(cat,voices=tuple(replace(v,voice_id=v.voice_id.replace('espeak:','espeak-timed:'),
            model_revision=v.model_revision+' / source-mark timing variant',features=v.features+('word-mark-events',)) for v in cat.voices))
    def _serialize_unmarked(self,request):return super().serialize(request)
    def serialize(self,request):return marked_markup(self,request)[0].encode()
    def _native(self,request,cancellation=None):
        if cancellation is not None and cancellation.is_set():raise ProviderFailure('CANCELLED')
        if request.voice not in self.catalog().voices:raise ProviderFailure('TIMED_VOICE_CHANGED')
        value=request.segment.spoken_text;words=lexical_ranges(value)
        # This explicit technical variant resets at sentence punctuation because
        # the installed legacy engine drops boundary events across some clauses.
        # Split only outside lexical tokens (not inside a decimal/word).
        stops=[]
        for i,ch in enumerate(value):
            if ch in '.!?।॥' and (i+1==len(value) or value[i+1].isspace()) and not any(a<=i<b for a,b in words):
                stops.append(i+1)
        if not stops or stops[-1]!=len(value):stops.append(len(value))
        chunks=[];start=0
        for stop in stops:
            if any(start<=a<b<=stop for a,b in words):chunks.append((start,stop));start=stop
        if start<len(value):
            if not chunks:raise AudioError('TIMED_LEXICAL_LIMIT')
            chunks[-1]=(chunks[-1][0],len(value))
        if len(chunks)>512:raise AudioError('TIMED_CLAUSE_BUDGET')
        libs=[(p,h) for p,h in self.snapshot['libraries'] if Path(p).name.startswith('libespeak.so')]
        if len(libs)!=1:raise ProviderFailure('TIMED_LIBRARY_UNAVAILABLE')
        library,libhash=libs[0];parts=[];all_events=[];cursor=0;clauses=[];markups=[];began=time.monotonic()
        for start,stop in chunks:
            markup,_=marked_markup(self,request,start=start,stop=stop);markups.append(markup)
            req={'markup':markup,'library':library,'library_sha256':libhash,
                'voice':{b.language:b.engine_voice for b in request.voice.locales}[request.segment.language],
                'rate':request.settings.rate_wpm,'pitch':request.settings.pitch,'amplitude':request.settings.amplitude}
            remaining=self.timeout_seconds-(time.monotonic()-began)
            if remaining<=0:raise AudioError('TIMING_WORKER_TIMEOUT')
            self.timing_calls+=1
            report,wav,_=_run_worker(req,timeout_seconds=remaining,cancellation=cancellation or Event())
            info,pcm=validate_wav(wav,request.settings.format,max_bytes=self.max_output_bytes)
            all_events.extend({**event,'sample_offset':cursor} for event in report['events'])
            clauses.append({'spoken_start':start,'spoken_end':stop,'start_sample':cursor,'samples':info.samples_per_channel,
                'pcm_sha256':report['pcm_sha256'],'markup_sha256':hashlib.sha256(markup.encode()).hexdigest()})
            parts.append(pcm);cursor+=info.samples_per_channel
            if sum(map(len,parts))>self.max_output_bytes or cursor>request.settings.format.sample_rate*300:raise AudioError('TIMED_OUTPUT_BUDGET')
        self.catalog();raw=b''.join(parts);wav=encode_pcm(raw,request.settings.format)
        report={'schema_version':'bie.espeak-clause-mark-callback/1','events':all_events,'clauses':clauses,
            'samples':cursor,'sample_rate':request.settings.format.sample_rate,'library_sha256':libhash,
            'pcm_sha256':hashlib.sha256(raw).hexdigest(),'completed':True,
            'prosody_policy':'SOURCE_BOUND_SENTENCE_RESET_TECHNICAL_VARIANT/1'}
        return report,wav,words,'\n'.join(markups)
    def synthesize(self,request,*,cancellation=None):
        self.invocations+=1;report,wav,_,_=self._native(request,cancellation)
        validate_wav(wav,request.settings.format,max_bytes=self.max_output_bytes)
        return ProviderAudio(request.fingerprint(),self.provider_id,request.voice.fingerprint(),self.runtime,wav,
            'espeak-timed:'+uuid.uuid4().hex,('LOCAL_FORMANT_NOT_CINEMATIC_ACCEPTANCE','SOURCE_MARKS_MAY_CHANGE_PROSODY','TIMING_ARTIFACT_REQUIRED_SEPARATELY'))


def words_from_marks(segment,report,ranges,provider_samples,rate):
    if type(report.get('events'))is not list or len(report['events'])>20000:raise AudioError('MARK_EVENTS_INVALID')
    marks={};previous=0
    for event in report['events']:
        if type(event)is not dict:raise AudioError('MARK_EVENT_FIELDS')
        if event.get('type')!=3:continue
        if type(event.get('audio_ms'))is not int or event['audio_ms']<0:raise AudioError('MARK_EVENT_TIME')
        offset=event.get('sample_offset',0)
        if type(offset)is not int or not 0<=offset<=provider_samples:raise AudioError('MARK_EVENT_OFFSET')
        sample=samples_for_ms(event['audio_ms'],rate)+offset;name=event.get('mark')
        if type(name)is not str or name in marks or sample<previous or sample>provider_samples:raise AudioError('MARK_EVENT_ORDER')
        marks[name]=sample;previous=sample
    expected={f'bie_w{i}_{side}' for i in range(len(ranges)) for side in ('start','end')}
    if set(marks)!=expected:raise AudioError('MARK_EVENT_COVERAGE')
    return tuple(WordStamp(i,a,b,segment.spoken_text[a:b],marks[f'bie_w{i}_start'],marks[f'bie_w{i}_end'],
                source_slices(segment,a,b),'ENGINE_MARK_BOUNDARY') for i,(a,b) in enumerate(ranges))


def align_timed_asset(asset,provider:TimedEspeakProvider,*,cancellation=None):
    info,_,prefix=validate_asset(asset);r=asset.request
    if type(provider)is not TimedEspeakProvider or r.voice not in provider.catalog().voices:raise AudioError('TIMED_PROVIDER_REQUIRED')
    report,wav,ranges,markup=provider._native(r,cancellation)
    replay_info,raw=validate_wav(wav,r.settings.format)
    if raw!=prefix or report['pcm_sha256']!=asset.provider_pcm_sha256 or report['samples']!=replay_info.samples_per_channel or report['sample_rate']!=info.sample_rate:
        raise AudioError('TIMING_REPLAY_PCM_MISMATCH')
    if cancellation is not None and cancellation.is_set():raise AudioError('CANCELLED')
    evidence={**report,'markup_sha256':hashlib.sha256(markup.encode()).hexdigest(),
              'range_fingerprint':fingerprint(ranges),'speech_request_fingerprint':r.fingerprint(),
              'marked_synthesis_replay_pcm_equal':True,'old_unmarked_audio_replaced':False}
    result=AlignedSpeech(r.fingerprint(),info.sha256,r.segment.fingerprint(),r.voice.runtime_fingerprint,
        fingerprint({'runtime':provider.runtime,'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}),
        fingerprint(evidence),info.sample_rate,replay_info.samples_per_channel,asset.requested_pause_samples,
        words_from_marks(r.segment,report,ranges,replay_info.samples_per_channel,info.sample_rate),'ESPEAK_MARK_EVENTS_SAME_PCM')
    validate_alignment(asset,result)
    return result,evidence
