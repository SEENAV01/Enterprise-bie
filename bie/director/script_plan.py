"""Original BIE-DIR-SCRIPT-001 with grounded identifier validation hardening."""
from dataclasses import dataclass,replace
import json,hashlib
from .contract_validation import nonblank,items,ids


@dataclass(frozen=True)
class ScriptSegment:
    segment_id:str
    scene_id:str
    purpose:str
    text_intent:str
    evidence_ids:tuple[str,...]
    objective_ids:tuple[str,...]


@dataclass(frozen=True)
class ScriptPlan:
    lesson_id:str
    segments:tuple[ScriptSegment,...]
    voice_profile:str

    def fingerprint(self):
        p={'lesson_id':self.lesson_id,'voice_profile':self.voice_profile,'segments':[s.__dict__ for s in self.segments]}
        return 'sha256:'+hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def build_script_plan(lesson_id,segments,voice_profile):
    nonblank(lesson_id,'lesson id'); nonblank(voice_profile,'voice profile')
    normalized=[]
    for segment in items(segments,'segments'):
        if not isinstance(segment,ScriptSegment): raise ValueError('expected ScriptSegment')
        for name in ('segment_id','scene_id','purpose','text_intent'): nonblank(getattr(segment,name),name)
        normalized.append(replace(segment,evidence_ids=ids(segment.evidence_ids,'segment evidence'),objective_ids=ids(segment.objective_ids,'segment objectives')))
    segs=tuple(sorted(normalized,key=lambda s:s.segment_id))
    if len({s.segment_id for s in segs})!=len(segs): raise ValueError('duplicate segment')
    return ScriptPlan(lesson_id,segs,voice_profile)


def validate_script_plan(value):
    if not isinstance(value,ScriptPlan): raise ValueError('expected ScriptPlan')
    if value!=build_script_plan(value.lesson_id,value.segments,value.voice_profile):
        raise ValueError('noncanonical or edited script plan')
    return value
