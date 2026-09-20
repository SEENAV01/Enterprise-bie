from dataclasses import dataclass
from .capability_common import *

@dataclass(frozen=True)
class AccessibilityMetadata:
    element_id:str
    alt_text:str|None=None
    long_description_ref:str|None=None
    captions_ref:str|None=None
    transcript_ref:str|None=None
    reduced_motion_variant:str|None=None
    color_independent_encoding:bool=False
    keyboard_focusable:bool=False
    reading_order:int|None=None
    def __post_init__(self):
        object.__setattr__(self,'element_id',tok(self.element_id,'element_id'))
        for f in ('alt_text','long_description_ref','captions_ref','transcript_ref','reduced_motion_variant'):
            v=getattr(self,f)
            if v is not None: object.__setattr__(self,f,tok(v,f))
        if self.reading_order is not None and (isinstance(self.reading_order,bool) or not isinstance(self.reading_order,int) or self.reading_order<0): raise SceneIRCapabilityError('reading_order invalid')

def validate_accessibility_metadata(records,element_type_by_id):
    records=tuple(records); types=dict(element_type_by_id)
    if len({r.element_id for r in records})!=len(records): raise SceneIRCapabilityError('duplicate accessibility metadata')
    blockers=[]
    for r in records:
        et=types.get(r.element_id)
        if et is None: blockers.append('unknown_element:'+r.element_id); continue
        if et in {'image','diagram','graph','chart','map','model2d','model3d'} and not (r.alt_text or r.long_description_ref): blockers.append('visual_description_missing:'+r.element_id)
        if et=='video' and not (r.captions_ref or r.transcript_ref): blockers.append('video_text_alternative_missing:'+r.element_id)
        if et in {'simulation','particle_system'} and not r.reduced_motion_variant: blockers.append('reduced_motion_variant_missing:'+r.element_id)
        if et in {'graph','chart','map'} and not r.color_independent_encoding: blockers.append('color_independent_encoding_missing:'+r.element_id)
    return tuple(sorted(set(blockers)))
