from dataclasses import dataclass
import json,hashlib
@dataclass(frozen=True)
class ScriptSegment: segment_id:str; scene_id:str; purpose:str; text_intent:str; evidence_ids:tuple[str,...]; objective_ids:tuple[str,...]
@dataclass(frozen=True)
class ScriptPlan:
    lesson_id:str; segments:tuple[ScriptSegment,...]; voice_profile:str
    def fingerprint(self):
        p={"lesson_id":self.lesson_id,"voice_profile":self.voice_profile,"segments":[s.__dict__ for s in self.segments]}
        return "sha256:"+hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def build_script_plan(lesson_id,segments,voice_profile):
    segs=tuple(sorted(segments,key=lambda s:s.segment_id))
    if not lesson_id.strip() or not voice_profile.strip() or not segs: raise ValueError("metadata")
    if len({s.segment_id for s in segs})!=len(segs): raise ValueError("duplicate")
    for s in segs:
        if not s.scene_id.strip() or not s.purpose.strip() or not s.text_intent.strip() or not s.evidence_ids or not s.objective_ids: raise ValueError("grounding")
    return ScriptPlan(lesson_id,segs,voice_profile)
