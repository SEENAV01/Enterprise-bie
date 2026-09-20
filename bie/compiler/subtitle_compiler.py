from .audio_compiler_common import *
from .captions_compiler import normalize_caption

def _stamp(value,separator):
    value=nonnegative_int(value,"timestamp")
    hours=value//3600000
    value%=3600000
    minutes=value//60000
    value%=60000
    seconds=value//1000
    millis=value%1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"

def captions_to_srt(captions):
    items=[normalize_caption(x) for x in captions]
    items.sort(key=lambda x:(x["startMs"],x["endMs"],x["text"]))
    blocks=[]
    for index,item in enumerate(items,1):
        blocks.append(
            f"{index}\n{_stamp(item['startMs'],',')} --> {_stamp(item['endMs'],',')}\n{item['text']}"
        )
    return canonical_text("\n\n".join(blocks))

def captions_to_webvtt(captions):
    items=[normalize_caption(x) for x in captions]
    items.sort(key=lambda x:(x["startMs"],x["endMs"],x["text"]))
    blocks=["WEBVTT"]
    for item in items:
        blocks.append(
            f"{_stamp(item['startMs'],'.')} --> {_stamp(item['endMs'],'.')}\n{item['text']}"
        )
    return canonical_text("\n\n".join(blocks))

def compile_subtitles(captions):
    return (
        artifact("captions-srt","public/captions/subtitles.srt",captions_to_srt(captions)),
        artifact("captions-vtt","public/captions/subtitles.vtt",captions_to_webvtt(captions)),
    )
