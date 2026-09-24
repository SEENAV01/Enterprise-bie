"""BIE-AUDIO-SYNC-001: real synthesis word onsets bound to exact PCM bytes.

No uniform word-spacing estimate or silence-based guessed forced alignment.
External reported timings remain a separately labelled, unverified input route.
"""
from __future__ import annotations
from pathlib import Path
from threading import Event
from xml.sax.saxutils import escape
import hashlib, json, os, signal, subprocess, sys, tempfile, time, unicodedata
from .common import AudioError, fingerprint, integer
from .espeak_provider import EspeakProvider
from .sync_contract import (AlignedSpeech, WordStamp, samples_for_ms, source_slices,
                            validate_asset, validate_alignment)
from .pcm_audio import validate_wav


def serialize_map(provider, request):
    """Map each serialized XML character to a prepared spoken code point.

    Escaped entity bytes map to their ONE spoken character; tag characters to None.
    Equality with the unchanged VO-009 serializer is mandatory.
    """
    expected=provider.serialize(request).decode('utf-8')
    head=f'<speak version="1.0" xml:lang="{request.segment.language}">'
    parts=[head]; positions=[None]*len(head); cursor=0
    aliases={x.language:x.engine_voice for x in request.voice.locales}
    for span in request.segment.spans:
        opening=f'<voice name="{aliases[span.language]}">'
        parts.append(opening); positions.extend([None]*len(opening))
        for ch in span.spoken:
            encoded=escape(ch); parts.append(encoded); positions.extend([cursor]*len(encoded)); cursor+=1
        parts.append('</voice>'); positions.extend([None]*8)
    parts.append('</speak>'); positions.extend([None]*8)
    if ''.join(parts)!=expected or cursor!=len(request.segment.spoken_text):
        raise AudioError('TIMING_SERIALIZER_CHANGED')
    return expected,tuple(positions)


def callback_words(segment, events, positions, rate, provider_samples):
    if type(events)is not list or not 1<=len(events)<=20000: raise AudioError('EVENTS_REQUIRED')
    rows=[]; event_end=-1
    for ev in events:
        if type(ev)is not dict or set(ev)!={'type','text_position','length','audio_ms'}: raise AudioError('EVENT_FIELDS')
        for key in ('type','text_position','length','audio_ms'): integer(ev[key],key,0,10000000)
        sample=samples_for_ms(ev['audio_ms'],rate)
        if sample<event_end or sample>provider_samples: raise AudioError('EVENT_CLOCK_BOUNDS')
        event_end=sample
        if ev['type']==5: rows.append(('end',sample,None,None)); continue
        if ev['type']!=1 or ev['length']==0: continue
        a=ev['text_position']-1; b=a+ev['length']
        if a<0 or b>len(positions): raise AudioError('EVENT_TEXT_OUTSIDE')
        mapped=[i for i in positions[a:b] if i is not None]
        if not mapped: raise AudioError('EVENT_IN_MARKUP')
        start,end=min(mapped),max(mapped)+1
        # eSpeak sometimes includes trailing punctuation in its public word length.
        spoken=segment.spoken_text
        while start<end and (spoken[start].isspace() or unicodedata.category(spoken[start])[0]=='P'): start+=1
        while end>start and (spoken[end-1].isspace() or unicodedata.category(spoken[end-1])[0]=='P'): end-=1
        if start==end: continue
        # Repeated start events for one number/token form one observed word window.
        prior=next((r for r in reversed(rows) if r[0]=='word'),None)
        if prior and (start,end)==prior[2:]: continue
        rows.append(('word',sample,start,end))
    output=[]
    for i,row in enumerate(rows):
        kind,start,a,b=row
        if kind!='word': continue
        end=next((r[1] for r in rows[i+1:] if r[1]>start and r[0] in ('word','end')),provider_samples)
        if i+1<len(rows) and any(r[0]=='word' and r[1]==start for r in rows[i+1:]):
            raise AudioError('WORD_ONSETS_COLLAPSE')
        output.append(WordStamp(len(output),a,b,segment.spoken_text[a:b],start,end,source_slices(segment,a,b)))
    if not output: raise AudioError('NO_WORD_EVENTS')
    return tuple(output)


def _run_worker(req, *, timeout_seconds, cancellation):
    if type(timeout_seconds)not in (int,float) or not 0<timeout_seconds<=120: raise AudioError('TIMING_TIMEOUT_POLICY')
    if cancellation.is_set(): raise AudioError('CANCELLED')
    worker=Path(__file__).with_name('espeak_timing_worker.py').resolve()
    with tempfile.TemporaryDirectory(prefix='bie-word-timing-') as td:
        root=Path(td);raw=json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        (root/'request.json').write_bytes(raw)
        with (root/'log').open('w+b') as log:
            began=time.monotonic()
            p=subprocess.Popen([sys.executable,'-I',str(worker),td],cwd=td,stdout=log,stderr=log,start_new_session=True,
                env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':td})
            try:
                while True:
                    if cancellation.is_set(): raise AudioError('CANCELLED')
                    remaining=timeout_seconds-(time.monotonic()-began)
                    if remaining<=0: raise AudioError('TIMING_WORKER_TIMEOUT')
                    if (root/'log').stat().st_size>32000: raise AudioError('TIMING_LOG_LIMIT')
                    for name,limit in (('replay.wav',32000000),('events.json',4000000)):
                        f=root/name
                        if f.exists() and f.stat().st_size>limit: raise AudioError('TIMING_OUTPUT_LIMIT')
                    try:
                        p.wait(timeout=min(.03,remaining))
                        if time.monotonic()-began>timeout_seconds: raise AudioError('TIMING_WORKER_TIMEOUT')
                        break
                    except subprocess.TimeoutExpired: continue
                log.seek(0); diagnostic=log.read(32001)
                if p.returncode or len(diagnostic)>32000: raise AudioError('TIMING_WORKER_FAILED',diagnostic.decode('utf-8','replace')[:400])
                for name,limit in (('replay.wav',32000000),('events.json',4000000)):
                    f=root/name
                    if f.is_symlink() or not f.is_file() or f.stat().st_size>limit: raise AudioError('TIMING_OUTPUT_INVALID')
                events=json.loads((root/'events.json').read_text()); wav=(root/'replay.wav').read_bytes()
                if events.get('schema_version')!='bie.espeak-callback/1' or events.get('request_sha256')!=hashlib.sha256(raw).hexdigest() or events.get('completed')is not True:
                    raise AudioError('TIMING_PROCESS_RECEIPT')
            finally:
                if p.poll()is None: os.killpg(p.pid,signal.SIGKILL); p.wait(timeout=5)
    return events,wav,hashlib.sha256(worker.read_bytes()).hexdigest()


def align_espeak_asset(asset, provider:EspeakProvider, *, timeout_seconds=30, cancellation=None):
    info,_,prefix=validate_asset(asset); request=asset.request
    if type(provider)is not EspeakProvider or request.voice.provider_id!='espeak-local': raise AudioError('TIMING_PROVIDER_UNSUPPORTED')
    catalog=provider.catalog()
    if catalog.fingerprint()!=request.catalog_fingerprint or request.voice not in catalog.voices: raise AudioError('STALE_TIMING_PROVIDER')
    markup,positions=serialize_map(provider,request)
    libs=[(p,h) for p,h in provider.snapshot['libraries'] if Path(p).name.startswith('libespeak.so')]
    if len(libs)!=1: raise AudioError('ESPEAK_TIMING_LIBRARY_UNAVAILABLE')
    library,libhash=libs[0]
    req={'markup':markup,'library':library,'library_sha256':libhash,
         'voice':dict((b.language,b.engine_voice) for b in request.voice.locales)[request.segment.language],
         'rate':request.settings.rate_wpm,'pitch':request.settings.pitch,'amplitude':request.settings.amplitude}
    report,replay,worker_hash=_run_worker(req,timeout_seconds=timeout_seconds,cancellation=cancellation or Event())
    replay_info,pcm=validate_wav(replay,request.settings.format)
    if pcm!=prefix or report['pcm_sha256']!=asset.provider_pcm_sha256 or report['samples']!=len(prefix)//(info.channels*2) or report['sample_rate']!=info.sample_rate or report['library_sha256']!=libhash:
        raise AudioError('TIMING_REPLAY_PCM_MISMATCH','No timestamps may be applied to a different waveform')
    if provider.catalog()!=catalog: raise AudioError('TIMING_PROVIDER_CHANGED')
    if cancellation is not None and cancellation.is_set(): raise AudioError('CANCELLED')
    result=AlignedSpeech(request.fingerprint(),info.sha256,request.segment.fingerprint(),request.voice.runtime_fingerprint,
        fingerprint({'library_sha256':libhash,'worker_sha256':worker_hash,'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}),
        fingerprint(report),info.sample_rate,replay_info.samples_per_channel,asset.requested_pause_samples,
        callback_words(request.segment,report['events'],positions,info.sample_rate,replay_info.samples_per_channel),'ESPEAK_ENGINE_EVENTS_PCM_REPLAY')
    validate_alignment(asset,result)
    return result,report


def reported_word_timings(asset, intervals):
    """Validate an external adapter's typed ranges WITHOUT claiming measured trust."""
    info,_,prefix=validate_asset(asset)
    if type(intervals)is not tuple or len(intervals)>20000: raise AudioError('REPORTED_TIMING_ARRAY')
    words=[]
    for i,values in enumerate(intervals):
        if type(values)is not tuple or len(values)!=4: raise AudioError('REPORTED_TIMING_ROW')
        a,b,start,end=values
        source=source_slices(asset.request.segment,a,b)
        words.append(WordStamp(i,a,b,asset.request.segment.spoken_text[a:b],start,end,source,'REPORTED_INTERVAL'))
    r=asset.request
    result=AlignedSpeech(r.fingerprint(),info.sha256,r.segment.fingerprint(),r.voice.runtime_fingerprint,
        fingerprint('externally-reported'),fingerprint(intervals),info.sample_rate,len(prefix)//(info.channels*2),
        asset.requested_pause_samples,tuple(words),'REPORTED_UNVERIFIED')
    return validate_alignment(asset,result,require_measured=False)
