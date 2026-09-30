"""H2-007: strict plain-text SRT/WebVTT subset plus temporal coverage.

WebVTT permits richer markup/overlaps/settings; this profile BLOCKS rather than
silently stripping unsupported semantics. Activity coverage is not ASR evidence.
"""
from __future__ import annotations
import hashlib,re
from ..models import BenchmarkError,text
from .custody import finite

def _stamp(s,sep):
    pattern=r'(\d{2,}):([0-5]\d):([0-5]\d)'+re.escape(sep)+r'(\d{3})'
    m=re.fullmatch(pattern,s)
    if not m or len(m[1])>3:raise BenchmarkError('INVALID_CAPTION_TIMESTAMP')
    h,mi,se,ms=map(int,m.groups());return h*3600+mi*60+se+ms/1000

def parse(raw:bytes,kind:str,duration_s:float):
    finite(duration_s,0.001,86400)
    if type(raw) is not bytes or not raw or len(raw)>1_000_000:raise BenchmarkError('CAPTION_BYTE_LIMIT')
    if kind not in ('srt','vtt'):raise BenchmarkError('UNSUPPORTED_CAPTION_FORMAT')
    try:s=raw.decode('utf-8-sig').replace('\r\n','\n')
    except UnicodeError as e:raise BenchmarkError('CAPTION_ENCODING') from e
    text(s,maximum=1_000_000)
    if '\r' in s:raise BenchmarkError('CAPTION_LINE_ENDING')
    blocks=re.split(r'\n[ \t]*\n',s.strip())
    if kind=='vtt':
        if not blocks or blocks.pop(0)!='WEBVTT':raise BenchmarkError('VTT_HEADER_OR_METADATA_UNSUPPORTED')
    rows=[];ids=set();end=0.0
    for i,block in enumerate(blocks):
        lines=block.split('\n');cueid=str(i+1)
        if kind=='srt':
            if not lines or lines.pop(0)!=cueid:raise BenchmarkError('SRT_SEQUENCE_ERROR')
        elif lines and '-->' not in lines[0]:cueid=lines.pop(0)
        if cueid in ids:raise BenchmarkError('DUPLICATE_CAPTION_ID')
        ids.add(cueid)
        if len(lines)<2:raise BenchmarkError('CAPTION_CONTENT_MISSING')
        timing=lines.pop(0).split(' --> ')
        if len(timing)!=2:raise BenchmarkError('CAPTION_TIMING_SYNTAX')
        start,stop=(_stamp(x,',' if kind=='srt' else '.') for x in timing)
        if not 0<=start<stop<=duration_s+1e-7 or start<end-1e-7:raise BenchmarkError('CAPTION_RANGE_OR_OVERLAP')
        body='\n'.join(lines)
        if any(x in body for x in ('<','>','&','-->')):raise BenchmarkError('CAPTION_MARKUP_UNSUPPORTED')
        text(body,maximum=4096)
        if len(rows)>=10000:raise BenchmarkError('CAPTION_COUNT_LIMIT')
        rows.append({'id':cueid,'start_s':start,'end_s':stop,'text':body});end=stop
    if not rows:raise BenchmarkError('NO_CAPTION_CUES')
    joined='\n'.join(r['text'] for r in rows)
    return {'cues':rows,'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'text_sha256':hashlib.sha256(joined.encode('utf-8')).hexdigest(),'format':kind}

def intervals(value, duration):
    if type(value) is not list or len(value)>10000:raise BenchmarkError('INTERVAL_COUNT_LIMIT')
    out=[];last=0.0
    for row in value:
        if type(row) is not list or len(row)!=2:raise BenchmarkError('INVALID_INTERVAL')
        a=finite(row[0],0,duration);b=finite(row[1],0,duration)
        if not a<b or a<last:raise BenchmarkError('OVERLAPPING_OR_EMPTY_INTERVAL')
        out.append([a,b]);last=b
    return out

def coverage(required,available):
    """Union-intersection of sorted nonoverlapping intervals; no double counting."""
    total=sum(b-a for a,b in required)
    if not total:return None
    overlap=0.0;j=0
    for a,b in required:
        while j<len(available) and available[j][1]<=a:j+=1
        k=j
        while k<len(available) and available[k][0]<b:
            x,y=available[k];overlap+=max(0,min(b,y)-max(a,x));k+=1
    return min(1.0,max(0.0,overlap/total))

def alignment(parsed, narration, audio, audio_start_s):
    cues=[] if parsed is None else [[r['start_s'],r['end_s']] for r in parsed['cues']]
    active=[] if audio is None else [[a+audio_start_s,b+audio_start_s] for a,b in audio['activity_intervals_relative_s']]
    return {'caption_coverage_of_declared_narration':coverage(narration,cues),
            'decoded_activity_coverage_of_declared_narration':coverage(narration,active),
            'speech_content_verified':False,'pronunciation_verified':False}
