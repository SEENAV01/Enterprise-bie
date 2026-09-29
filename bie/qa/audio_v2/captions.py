"""Bounded plain-text SRT/WebVTT parsing; no HTML, CSS, timestamps in cue text.

Unsupported settings/styles are rejected rather than silently discarded. This is
not a general WebVTT renderer. Times are exact integer milliseconds.
"""
from dataclasses import dataclass
import re,unicodedata
from ..release_v2.contracts import ContractError

@dataclass(frozen=True,slots=True)
class Caption:
    cue_id:str
    start_ms:int
    end_ms:int
    text:str

def time_ms(value,fmt):
    pattern=r'(\d{2,3}):(\d{2}):(\d{2})'+(r',' if fmt=='srt' else r'\.')+r'(\d{3})'
    m=re.fullmatch(pattern,value)
    if not m:raise ContractError('AUDIO_CAPTION_TIMESTAMP')
    h,mi,s,ms=map(int,m.groups())
    if mi>=60 or s>=60 or h>1:raise ContractError('AUDIO_CAPTION_TIMESTAMP_RANGE')
    return ((h*60+mi)*60+s)*1000+ms

def parse_captions(data,fmt):
    if fmt not in ('srt','webvtt') or type(data) is not bytes or len(data)>1024*1024:raise ContractError('AUDIO_CAPTION_INPUT')
    try:s=data.decode('utf-8-sig').replace('\r\n','\n')
    except UnicodeError as exc:raise ContractError('AUDIO_CAPTION_UTF8') from exc
    if any(unicodedata.category(c) in ('Cc','Cf') and c not in '\n\t' for c in s):raise ContractError('AUDIO_CAPTION_CONTROL')
    if fmt=='webvtt':
        if not s.startswith('WEBVTT\n\n'):raise ContractError('AUDIO_WEBVTT_HEADER')
        s=s[len('WEBVTT\n\n'):]
    out=[];ids=set()
    for block in re.split(r'\n[ \t]*\n',s.strip()):
        lines=block.split('\n')
        if not lines or not block.strip():continue
        cue_id=str(len(out)+1)
        if '-->' not in lines[0]:
            cue_id=lines.pop(0)
            if not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',cue_id):raise ContractError('AUDIO_CAPTION_IDENTIFIER')
        elif fmt=='srt':raise ContractError('AUDIO_SRT_IDENTIFIER_REQUIRED')
        if len(lines)<2 or lines[0].count(' --> ')!=1:raise ContractError('AUDIO_CAPTION_STRUCTURE')
        a,b=lines[0].split(' --> ');start,end=time_ms(a,fmt),time_ms(b,fmt);body='\n'.join(lines[1:])
        if start>=end or not body.strip() or cue_id in ids:raise ContractError('AUDIO_CAPTION_RANGE_OR_ID')
        if any(c in body for c in '<>') or '-->' in body:raise ContractError('AUDIO_CAPTION_UNSUPPORTED_MARKUP')
        if len(body)>4096 or len(out)>=8192:raise ContractError('AUDIO_CAPTION_LIMIT')
        out.append(Caption(cue_id,start,end,body));ids.add(cue_id)
    if not out:raise ContractError('AUDIO_CAPTION_EMPTY')
    return tuple(out)

def normalized(value):return ' '.join(value.split())
