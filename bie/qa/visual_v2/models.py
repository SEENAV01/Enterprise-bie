"""Bounded visual QA contracts. Coordinates are integer milli-CSS-pixels.

Policy and trust are supplied by an operator outside the candidate. Captures are
sample observations, never a certificate for a complete movie or game.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ArtifactRef, ContractError, token, integer, choice, tuple_tokens, digest
from ..source_v2.models import Request, Policy, text, records

MAX_OBJECTS = 256
MAX_STATES = 128
MAX_COORD = 32_768_000
ROLES = ('text', 'label', 'caption', 'equation', 'shape', 'diagram', 'image', 'container', 'background')
TEXT_ROLES = ('text', 'label', 'caption', 'equation')
REPRESENTATIONS = ('text', 'diagram', 'graph', 'chart', 'map', 'timeline', 'equation', 'model2d', 'model3d', 'simulation')


def rows(value, cls, field, key, maximum=MAX_OBJECTS, minimum=0):
    records(value, cls, field, key, minimum)
    if len(value) > maximum: raise ContractError('VIS_COLLECTION_LIMIT', field)


def boolean(value, field):
    if type(value) is not bool: raise ContractError('VIS_BOOLEAN_REQUIRED', field)


def rects(value, field, maximum=512):
    if type(value) is not tuple or len(value) > maximum or any(type(x) is not Rect for x in value):
        raise ContractError('VIS_INVALID_RECT_LIST', field)


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    width: int
    height: int
    def __post_init__(self):
        integer(self.x, 'rect.x', -MAX_COORD, MAX_COORD); integer(self.y, 'rect.y', -MAX_COORD, MAX_COORD)
        integer(self.width, 'rect.width', 1, MAX_COORD); integer(self.height, 'rect.height', 1, MAX_COORD)
    @property
    def right(self): return self.x + self.width
    @property
    def bottom(self): return self.y + self.height
    @property
    def area(self): return self.width * self.height


@dataclass(frozen=True, slots=True)
class RGBA:
    r: int
    g: int
    b: int
    a: int = 255
    def __post_init__(self):
        for name in ('r', 'g', 'b', 'a'): integer(getattr(self, name), 'rgba.'+name, 0, 255)


@dataclass(frozen=True, slots=True)
class VisualElement:
    object_id: str
    scene_id: str
    role: str
    claim_ids: tuple[str, ...]
    semantic_id: str
    encodings: tuple[str, ...] = ('text',)
    def __post_init__(self):
        for name in ('object_id', 'scene_id', 'semantic_id'): token(getattr(self, name), name)
        choice(self.role, ROLES, 'element.role')
        tuple_tokens(self.claim_ids, 'element.claims', 0 if self.role in ('background','container') else 1, 128)
        tuple_tokens(self.encodings, 'encodings', 1, 16)
        for e in self.encodings: choice(e, ('text','shape','position','pattern','color','size','motion'), 'encoding')


@dataclass(frozen=True, slots=True)
class VisualScene:
    scene_id: str
    representation: str
    objective_ids: tuple[str, ...]
    features: tuple[str, ...]
    def __post_init__(self):
        token(self.scene_id, 'scene_id'); choice(self.representation, REPRESENTATIONS, 'representation')
        tuple_tokens(self.objective_ids, 'objectives', 1, 128); tuple_tokens(self.features, 'features', 0, 64)


@dataclass(frozen=True, slots=True)
class Measurement:
    object_id: str
    box: Rect
    clip: Rect
    text: str
    font_mpx: int
    foreground: RGBA
    background: RGBA
    opacity_ppm: int = 1_000_000
    displayed: bool = True
    background_known: bool = True
    fonts_loaded: bool = True
    line_boxes: tuple[Rect, ...] = ()
    unsupported: tuple[str, ...] = ()
    def __post_init__(self):
        token(self.object_id, 'object_id')
        if type(self.box) is not Rect or type(self.clip) is not Rect: raise ContractError('VIS_RECT_TYPE')
        if type(self.text) is not str or len(self.text) > 100000: raise ContractError('VIS_TEXT_TYPE_OR_LIMIT')
        if self.text: text(self.text, 'measurement.text', 100000)
        integer(self.font_mpx, 'font_mpx', 0, 1_000_000)
        if type(self.foreground) is not RGBA or type(self.background) is not RGBA: raise ContractError('VIS_COLOR_TYPE')
        integer(self.opacity_ppm, 'opacity_ppm', 0, 1000000)
        for name in ('displayed', 'background_known', 'fonts_loaded'): boolean(getattr(self,name), name)
        rects(self.line_boxes, 'line_boxes'); tuple_tokens(self.unsupported, 'unsupported', 0, 64)


@dataclass(frozen=True, slots=True)
class VisualState:
    state_id: str
    scene_id: str
    view_id: str
    start_ms: int
    end_ms: int
    measurements: tuple[Measurement, ...]
    geometry_mode: str = 'static'
    capture_id: str = 'none'
    def __post_init__(self):
        for name in ('state_id','scene_id','view_id','capture_id'): token(getattr(self,name),name)
        integer(self.start_ms,'start_ms',0,86_400_000); integer(self.end_ms,'end_ms',self.start_ms+1,86_400_000)
        rows(self.measurements, Measurement, 'measurements', 'object_id')
        choice(self.geometry_mode, ('static','sampled'), 'geometry_mode')


@dataclass(frozen=True, slots=True)
class VisualRelation:
    relation_id: str
    scene_id: str
    kind: str
    from_id: str
    to_id: str
    claim_ids: tuple[str, ...]
    def __post_init__(self):
        for name in ('relation_id','scene_id','from_id','to_id'): token(getattr(self,name),name)
        choice(self.kind, ('left_of','above','contains','label_for','points_to','causes','flows_to','compares'), 'relation.kind')
        tuple_tokens(self.claim_ids,'relation.claims',1,128)
        if self.from_id == self.to_id: raise ContractError('VIS_SELF_RELATION')


@dataclass(frozen=True, slots=True)
class CaptureRef:
    capture_id: str
    state_id: str
    html: ArtifactRef
    measurements: ArtifactRef
    screenshot: ArtifactRef
    renderer_id: str
    renderer_version: str
    def __post_init__(self):
        for name in ('capture_id','state_id','renderer_id','renderer_version'): token(getattr(self,name),name)
        for name in ('html','measurements','screenshot'):
            if type(getattr(self,name)) is not ArtifactRef: raise ContractError('VIS_CAPTURE_ARTIFACT_TYPE')
        if self.html.role != 'support' or self.screenshot.role != 'support' or self.measurements.role != 'support':
            raise ContractError('VIS_CAPTURE_ARTIFACT_ROLE')
        if len({a.artifact_id for a in (self.html,self.measurements,self.screenshot)}) != 3:
            raise ContractError('VIS_CAPTURE_ARTIFACT_ALIAS')


@dataclass(frozen=True, slots=True)
class VisualRequest:
    schema_version: str
    source: Request
    lesson_id: str
    audience_id: str
    language: str
    scenes: tuple[VisualScene, ...]
    elements: tuple[VisualElement, ...]
    states: tuple[VisualState, ...]
    relations: tuple[VisualRelation, ...] = ()
    captures: tuple[CaptureRef, ...] = ()
    def __post_init__(self):
        choice(self.schema_version, ('1.0.0',), 'schema_version')
        if type(self.source) is not Request: raise ContractError('VIS_SOURCE_TYPE')
        for name in ('lesson_id','audience_id','language'): token(getattr(self,name),name)
        rows(self.scenes,VisualScene,'scenes','scene_id',64,1)
        rows(self.elements,VisualElement,'elements','object_id',MAX_OBJECTS,1)
        rows(self.states,VisualState,'states','state_id',MAX_STATES,1)
        rows(self.relations,VisualRelation,'relations','relation_id',1024)
        rows(self.captures,CaptureRef,'captures','capture_id',MAX_STATES)
        mapping_ids=[e.object_id for e in self.elements]+[r.relation_id for r in self.relations]+[c.capture_id for c in self.captures]
        if len(mapping_ids)!=len(set(mapping_ids)) or any(s.state_id=='visual-scope' for s in self.states):
            raise ContractError('VIS_CONTEXT_TARGET_ALIAS')
        refs=[x.artifact for x in self.source.sources]+[x.artifact for x in self.source.outputs]
        refs += [a for c in self.captures for a in (c.html,c.measurements,c.screenshot)]
        by_id={};by_path={}
        for a in refs:
            if a.artifact_id in by_id and by_id[a.artifact_id]!=a or a.path in by_path and by_path[a.path]!=a:
                raise ContractError('VIS_ARTIFACT_ALIAS')
            by_id[a.artifact_id]=a;by_path[a.path]=a
        if sum(a.size for a in by_id.values())>64*1024*1024: raise ContractError('VIS_CAPTURE_BYTE_BUDGET')
        if len({c.state_id for c in self.captures}) != len(self.captures): raise ContractError('VIS_DUPLICATE_CAPTURE_STATE')
        if sum(len(s.measurements) for s in self.states)>8192: raise ContractError('VIS_MEASUREMENT_WORK_LIMIT')
        if sum(len(s.measurements)**2 for s in self.states)>1_048_576: raise ContractError('VIS_PAIR_WORK_LIMIT')
        if sum(len(m.text)+len(m.line_boxes)*16 for s in self.states for m in s.measurements)>8_000_000:
            raise ContractError('VIS_TEXT_WORK_LIMIT')
    @property
    def content_digest(self): return digest(asdict(self))


@dataclass(frozen=True, slots=True)
class ViewRequirement:
    view_id: str
    width_px: int
    height_px: int
    safe: Rect
    subtitle_regions: tuple[Rect,...] = ()
    def __post_init__(self):
        token(self.view_id,'view_id'); integer(self.width_px,'width_px',16,4096); integer(self.height_px,'height_px',16,4096)
        if self.width_px*self.height_px>8_388_608: raise ContractError('VIS_VIEW_PIXEL_LIMIT')
        if type(self.safe) is not Rect: raise ContractError('VIS_SAFE_RECT_TYPE')
        if self.safe.x<0 or self.safe.y<0 or self.safe.right>self.width_px*1000 or self.safe.bottom>self.height_px*1000:
            raise ContractError('VIS_SAFE_OUTSIDE_VIEW')
        rects(self.subtitle_regions,'subtitle_regions',16)
        if any(r.x<0 or r.y<0 or r.right>self.width_px*1000 or r.bottom>self.height_px*1000 for r in self.subtitle_regions):
            raise ContractError('VIS_SUBTITLE_REGION_OUTSIDE_VIEW')


@dataclass(frozen=True, slots=True)
class SceneRequirement:
    scene_id: str
    objective_ids: tuple[str, ...]
    allowed_representations: tuple[str, ...]
    required_features: tuple[str, ...] = ()
    def __post_init__(self):
        token(self.scene_id,'scene_id'); tuple_tokens(self.objective_ids,'objectives',1,128)
        tuple_tokens(self.allowed_representations,'representations',1,len(REPRESENTATIONS))
        for r in self.allowed_representations: choice(r,REPRESENTATIONS,'representation')
        tuple_tokens(self.required_features,'required_features',0,64)


@dataclass(frozen=True, slots=True)
class StateRequirement:
    state_id: str
    scene_id: str
    view_id: str
    start_ms: int
    end_ms: int
    object_ids: tuple[str,...]
    relation_ids: tuple[str,...] = ()
    def __post_init__(self):
        for name in ('state_id','scene_id','view_id'): token(getattr(self,name),name)
        integer(self.start_ms,'start_ms',0,86_400_000); integer(self.end_ms,'end_ms',self.start_ms+1,86_400_000)
        tuple_tokens(self.object_ids,'objects',1,MAX_OBJECTS); tuple_tokens(self.relation_ids,'relations',0,1024)


@dataclass(frozen=True, slots=True)
class OverlapAllowance:
    allowance_id: str
    state_id: str
    first_id: str
    second_id: str
    max_overlap_ppm: int
    reason: str
    def __post_init__(self):
        for name in ('allowance_id','state_id','first_id','second_id'): token(getattr(self,name),name)
        if self.first_id==self.second_id: raise ContractError('VIS_SELF_OVERLAP_ALLOWANCE')
        integer(self.max_overlap_ppm,'max_overlap_ppm',1,1000000); text(self.reason,'overlap.reason',2048)


@dataclass(frozen=True, slots=True)
class VisualLimits:
    min_font_mpx: int = 18000
    min_contrast_ppm: int = 4500000
    max_visible_items: int = 24
    max_semantic_items: int = 16
    max_text_codepoints: int = 700
    max_area_ppm: int = 750000
    max_cell_items: int = 10
    grid_rows: int = 3
    grid_columns: int = 3
    max_read_codepoints_per_minute: int = 1000
    min_text_exposure_ms: int = 1200
    min_opacity_ppm: int = 900000
    label_distance_mpx: int = 140000
    geometry_tolerance_mpx: int = 1
    def __post_init__(self):
        integer(self.min_font_mpx,'min_font_mpx',1000,1000000)
        integer(self.min_contrast_ppm,'min_contrast_ppm',1000000,21000000)
        integer(self.max_visible_items,'max_visible_items',1,MAX_OBJECTS)
        integer(self.max_semantic_items,'max_semantic_items',1,MAX_OBJECTS)
        integer(self.max_text_codepoints,'max_text_codepoints',1,100000)
        integer(self.max_area_ppm,'max_area_ppm',1,1000000)
        integer(self.max_cell_items,'max_cell_items',1,MAX_OBJECTS)
        integer(self.grid_rows,'grid_rows',1,10); integer(self.grid_columns,'grid_columns',1,10)
        integer(self.max_read_codepoints_per_minute,'reading_rate',1,100000)
        integer(self.min_text_exposure_ms,'min_text_exposure_ms',1,86400000)
        integer(self.min_opacity_ppm,'min_opacity_ppm',1,1000000)
        integer(self.label_distance_mpx,'label_distance_mpx',0,MAX_COORD)
        integer(self.geometry_tolerance_mpx,'geometry_tolerance_mpx',0,1000)


@dataclass(frozen=True, slots=True)
class VisualPolicy:
    policy_id: str
    source: Policy
    lesson_id: str
    audience_id: str
    language: str
    scenes: tuple[SceneRequirement,...]
    elements: tuple[VisualElement,...]
    states: tuple[StateRequirement,...]
    views: tuple[ViewRequirement,...]
    relations: tuple[VisualRelation,...] = ()
    overlaps: tuple[OverlapAllowance,...] = ()
    limits: VisualLimits = VisualLimits()
    require_captures: bool = False
    max_receipt_age_seconds: int = 3600
    minimum_review_confidence_ppm: int = 900000
    minimum_independent_assessors: int = 1
    def __post_init__(self):
        for name in ('policy_id','lesson_id','audience_id','language'): token(getattr(self,name),name)
        if type(self.source) is not Policy or type(self.limits) is not VisualLimits: raise ContractError('VIS_POLICY_TYPE')
        rows(self.scenes,SceneRequirement,'scenes','scene_id',64,1)
        rows(self.elements,VisualElement,'elements','object_id',MAX_OBJECTS,1)
        rows(self.states,StateRequirement,'states','state_id',MAX_STATES,1)
        rows(self.views,ViewRequirement,'views','view_id',32,1)
        rows(self.relations,VisualRelation,'relations','relation_id',1024)
        rows(self.overlaps,OverlapAllowance,'overlaps','allowance_id',1024)
        boolean(self.require_captures,'require_captures')
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
        integer(self.minimum_review_confidence_ppm,'minimum_review_confidence_ppm',1,1000000)
        integer(self.minimum_independent_assessors,'minimum_independent_assessors',1,8)
        scenes={s.scene_id for s in self.scenes}; views={v.view_id for v in self.views}; elements={e.object_id:e for e in self.elements}
        states={s.state_id:s for s in self.states}; relations={r.relation_id:r for r in self.relations}
        if any(e.scene_id not in scenes for e in self.elements): raise ContractError('VIS_POLICY_ELEMENT_SCENE')
        for s in self.states:
            if s.scene_id not in scenes or s.view_id not in views or not set(s.object_ids)<=set(elements) or not set(s.relation_ids)<=set(relations):
                raise ContractError('VIS_POLICY_STATE_REFERENCE')
            if any(elements[e].scene_id!=s.scene_id for e in s.object_ids): raise ContractError('VIS_POLICY_CROSS_SCENE_ELEMENT')
            for rid in s.relation_ids:
                r=relations[rid]
                if r.scene_id!=s.scene_id or not {r.from_id,r.to_id}<=set(s.object_ids): raise ContractError('VIS_POLICY_RELATION_STATE')
        if set().union(*(set(s.object_ids) for s in self.states))!=set(elements): raise ContractError('VIS_POLICY_UNPRESENTED_ELEMENT')
        if {s.scene_id for s in self.states}!=scenes or {s.view_id for s in self.states}!=views: raise ContractError('VIS_POLICY_UNUSED_SCOPE')
        if set().union(*(set(s.relation_ids) for s in self.states))!=set(relations): raise ContractError('VIS_POLICY_UNPRESENTED_RELATION')
        for r in self.relations:
            if r.from_id not in elements or r.to_id not in elements or elements[r.from_id].scene_id!=r.scene_id or elements[r.to_id].scene_id!=r.scene_id:
                raise ContractError('VIS_POLICY_RELATION_REFERENCE')
        pairs=set()
        for a in self.overlaps:
            if a.state_id not in states or not {a.first_id,a.second_id}<=set(states[a.state_id].object_ids): raise ContractError('VIS_POLICY_OVERLAP_REFERENCE')
            pair=(a.state_id,tuple(sorted((a.first_id,a.second_id))))
            if pair in pairs: raise ContractError('VIS_DUPLICATE_OVERLAP_ALLOWANCE')
            pairs.add(pair)
            if elements[a.first_id].role in TEXT_ROLES and elements[a.second_id].role in TEXT_ROLES:
                raise ContractError('VIS_TEXT_TEXT_OVERLAP_NOT_EXEMPT')
        # State intervals in one scene/view must not contradict one another.
        for i,s in enumerate(self.states):
            for t in self.states[i+1:]:
                if (s.scene_id,s.view_id)==(t.scene_id,t.view_id) and max(s.start_ms,t.start_ms)<min(s.end_ms,t.end_ms):
                    raise ContractError('VIS_POLICY_OVERLAPPING_STATES')
    @property
    def content_digest(self): return digest(asdict(self))
