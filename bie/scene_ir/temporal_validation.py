from .validation_common import *

def validate_temporal(doc):
    issues=[]
    duration=doc.get("duration_ms",0)
    for i,t in enumerate(doc.get("tracks",())):
        s=t.get("start_ms");e=t.get("end_ms")
        if not isinstance(s,int) or isinstance(s,bool) or s<0:
            issues.append(issue("TRACK_START",f"$.tracks[{i}].start_ms","Invalid start_ms"))
            continue
        if not isinstance(e,int) or isinstance(e,bool) or e<=s:
            issues.append(issue("TRACK_END",f"$.tracks[{i}].end_ms","end_ms must exceed start_ms"))
            continue
        if e>duration:
            issues.append(issue("TRACK_EXCEEDS_SCENE",f"$.tracks[{i}]","Track exceeds scene duration"))
    for i,e in enumerate(doc.get("events",())):
        at=e.get("at_ms")
        if not isinstance(at,int) or isinstance(at,bool) or at<0 or at>duration:
            issues.append(issue("EVENT_OUTSIDE_SCENE",f"$.events[{i}].at_ms","Event outside scene duration"))
    for i,c in enumerate(doc.get("narration_cues",())):
        s,e=c.get("start_ms"),c.get("end_ms")
        if not isinstance(s,int) or not isinstance(e,int) or isinstance(s,bool) or isinstance(e,bool) or s<0 or e<=s or e>duration:
            issues.append(issue("NARRATION_CUE_RANGE",f"$.narration_cues[{i}]","Invalid narration cue interval"))
    return report("DSL-VALID-TEMPORAL",issues)
