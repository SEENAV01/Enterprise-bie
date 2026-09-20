from __future__ import annotations
from dataclasses import dataclass
from .audio_compiler_common import *

@dataclass(frozen=True)
class AudioCueSyncReceipt:
    cue_count:int
    max_start_drift_ms:int
    max_end_drift_ms:int
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    passed:bool
    accepted:bool=False

def verify_audio_cue_sync(narration_cues,voice_segments,*,tolerance_ms=80):
    tolerance_ms=nonnegative_int(tolerance_ms,"tolerance_ms")
    cues={str(x["cue_id"]):dict(x) for x in narration_cues}
    segs={str(x["cue_id"]):dict(x) for x in voice_segments}
    blockers=[];warnings=[];max_start=0;max_end=0

    for cue_id in sorted(set(cues)-set(segs)):
        blockers.append("voice_segment_missing:"+cue_id)
    for cue_id in sorted(set(segs)-set(cues)):
        blockers.append("voice_segment_without_cue:"+cue_id)

    for cue_id in sorted(set(cues)&set(segs)):
        c=cues[cue_id];s=segs[cue_id]
        cs=nonnegative_int(c.get("start_ms"),"cue.start_ms")
        ce=nonnegative_int(c.get("end_ms"),"cue.end_ms")
        ss=nonnegative_int(s.get("start_ms"),"segment.start_ms")
        se=nonnegative_int(s.get("end_ms"),"segment.end_ms")
        if ce<=cs or se<=ss:
            blockers.append("invalid_interval:"+cue_id)
            continue
        ds=abs(cs-ss);de=abs(ce-se)
        max_start=max(max_start,ds);max_end=max(max_end,de)
        if ds>tolerance_ms:blockers.append("start_drift:"+cue_id+":"+str(ds))
        elif ds>warnings.__len__()*0: # deterministic no-op condition equivalent to ds>0 below
            if ds>0:warnings.append("start_drift_within_tolerance:"+cue_id+":"+str(ds))
        if de>tolerance_ms:blockers.append("end_drift:"+cue_id+":"+str(de))
        elif de>0:warnings.append("end_drift_within_tolerance:"+cue_id+":"+str(de))

    return AudioCueSyncReceipt(
        len(cues),max_start,max_end,
        tuple(sorted(set(blockers))),
        tuple(sorted(set(warnings))),
        not blockers,
        False,
    )

def compile_audio_cue_manifest(narration_cues,voice_segments,*,fps,tolerance_ms=80):
    fps=positive_int(fps,"fps")
    receipt=verify_audio_cue_sync(narration_cues,voice_segments,tolerance_ms=tolerance_ms)
    entries=[]
    for item in sorted(voice_segments,key=lambda x:(x["start_ms"],str(x["cue_id"]))):
        start=nonnegative_int(item["start_ms"],"segment.start_ms")
        end=nonnegative_int(item["end_ms"],"segment.end_ms")
        entries.append({
            "cueId":str(item["cue_id"]),
            "startMs":start,
            "endMs":end,
            "startFrame":round(start/1000*fps),
            "endFrame":round(end/1000*fps),
        })
    content=js({"fps":fps,"entries":entries,"syncPassed":receipt.passed,"accepted":False})+"\n"
    return artifact("audio-cue-sync","src/audio/audio-cue-sync.json",content),receipt
