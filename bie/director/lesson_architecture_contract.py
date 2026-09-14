"""Original BIE-DIR-LESSON-001, corrected by HARD-CONTRACTS-001.

Public fields and canonical fingerprints for valid prior inputs are preserved.
Raw records may be deserialized for diagnosis; use the builder/validator before
production consumption. Historical ZIPs and QA's invalid-input probes are retained.
"""
from dataclasses import dataclass,asdict,replace
import json,hashlib
from .contract_validation import nonblank,items,ids,acyclic


@dataclass(frozen=True)
class LessonSceneIntent:
    scene_id:str
    purpose:str
    objective_ids:tuple[str,...]
    evidence_ids:tuple[str,...]
    parent_scene_ids:tuple[str,...]=()
    requires_review:bool=False

    def validate(self):
        nonblank(self.scene_id,'scene id'); nonblank(self.purpose,'scene purpose')
        ids(self.objective_ids,'scene objectives'); ids(self.evidence_ids,'scene evidence')
        ids(self.parent_scene_ids,'scene parents',required=False)
        if type(self.requires_review) is not bool: raise ValueError('review flag must be boolean')
        if self.scene_id in self.parent_scene_ids: raise ValueError('scene cannot parent itself')


@dataclass(frozen=True)
class LessonArchitecture:
    lesson_id:str
    title:str
    scenes:tuple[LessonSceneIntent,...]
    objective_ids:tuple[str,...]
    source_ids:tuple[str,...]
    policy_version:str
    requires_review:bool=False

    def fingerprint(self):
        return 'sha256:'+hashlib.sha256(json.dumps(asdict(self),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def build_lesson_architecture(lesson_id,title,scenes,objective_ids,source_ids,policy_version):
    for value,name in ((lesson_id,'lesson id'),(title,'title'),(policy_version,'policy')): nonblank(value,name)
    objectives=ids(objective_ids,'lesson objectives',canonical=True)
    sources=ids(source_ids,'lesson sources',canonical=True)
    normalized=[]
    for scene in items(scenes,'scenes'):
        if not isinstance(scene,LessonSceneIntent): raise ValueError('expected LessonSceneIntent')
        # Copy any mutable input sequences into owned immutable records.
        scene=replace(scene,objective_ids=ids(scene.objective_ids,'scene objectives'),
            evidence_ids=ids(scene.evidence_ids,'scene evidence'),parent_scene_ids=ids(scene.parent_scene_ids,'scene parents',required=False))
        scene.validate()
        if not set(scene.objective_ids)<=set(objectives): raise ValueError('scene objectives outside lesson')
        normalized.append(scene)
    normalized=tuple(sorted(normalized,key=lambda s:s.scene_id))
    if len({s.scene_id for s in normalized})!=len(normalized): raise ValueError('duplicate scene')
    if {o for s in normalized for o in s.objective_ids}!=set(objectives): raise ValueError('lesson objective has no scene')
    acyclic({s.scene_id:s.parent_scene_ids for s in normalized})
    return LessonArchitecture(lesson_id,title,normalized,objectives,sources,policy_version,any(s.requires_review for s in normalized))


def validate_lesson_architecture(value):
    if not isinstance(value,LessonArchitecture): raise ValueError('expected LessonArchitecture')
    if type(value.requires_review) is not bool: raise ValueError('review flag must be boolean')
    rebuilt=build_lesson_architecture(value.lesson_id,value.title,value.scenes,value.objective_ids,value.source_ids,value.policy_version)
    if value!=rebuilt: raise ValueError('noncanonical or edited lesson architecture')
    return value
