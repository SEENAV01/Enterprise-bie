from dataclasses import dataclass,asdict
import json,hashlib
@dataclass(frozen=True)
class LessonSceneIntent:
    scene_id:str; purpose:str; objective_ids:tuple[str,...]; evidence_ids:tuple[str,...]; parent_scene_ids:tuple[str,...]=(); requires_review:bool=False
    def validate(self):
        if not self.scene_id.strip() or not self.purpose.strip() or not self.objective_ids or not self.evidence_ids: raise ValueError("grounded scene required")
@dataclass(frozen=True)
class LessonArchitecture:
    lesson_id:str; title:str; scenes:tuple[LessonSceneIntent,...]; objective_ids:tuple[str,...]; source_ids:tuple[str,...]; policy_version:str; requires_review:bool=False
    def fingerprint(self):
        return "sha256:"+hashlib.sha256(json.dumps(asdict(self),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def build_lesson_architecture(lesson_id,title,scenes,objective_ids,source_ids,policy_version):
    scenes=tuple(sorted(scenes,key=lambda s:s.scene_id))
    if not lesson_id.strip() or not title.strip() or not policy_version.strip() or not scenes: raise ValueError("metadata")
    ids=[s.scene_id for s in scenes]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate scene")
    known=set(ids)
    for s in scenes:
        s.validate()
        if any(p not in known for p in s.parent_scene_ids): raise ValueError("unknown parent")
    o=tuple(sorted(set(objective_ids))); src=tuple(sorted(set(source_ids)))
    if not o or not src: raise ValueError("lesson grounding")
    return LessonArchitecture(lesson_id,title,scenes,o,src,policy_version,any(s.requires_review for s in scenes))
