from __future__ import annotations
from dataclasses import dataclass,field
from typing import Any,Mapping
from .visual_plan_contract import token,ids,revision,canon,fp,StageRef

class DirectorAdoptionError(ValueError): pass
class StaleDirectorHandoffError(DirectorAdoptionError): pass

@dataclass(frozen=True)
class VisualIntent:
    intent_id:str; intent_type:str; evidence_refs:tuple[str,...]; reasoning_refs:tuple[str,...]; payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"intent_id",token(self.intent_id,"intent_id"))
        object.__setattr__(self,"intent_type",token(self.intent_type,"intent_type"))
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,"evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,"reasoning_refs"))
        object.__setattr__(self,"payload",canon(dict(self.payload)))

@dataclass(frozen=True)
class TimingCue:
    cue_id:str; intent_id:str; start_ms:int; end_ms:int; narration_revision:int; cue_type:str="visual"
    def __post_init__(self):
        object.__setattr__(self,"cue_id",token(self.cue_id,"cue_id"));object.__setattr__(self,"intent_id",token(self.intent_id,"intent_id"))
        if not isinstance(self.start_ms,int) or self.start_ms<0 or not isinstance(self.end_ms,int) or self.end_ms<=self.start_ms: raise DirectorAdoptionError("bad timing")
        object.__setattr__(self,"narration_revision",revision(self.narration_revision,"narration_revision"))
        object.__setattr__(self,"cue_type",token(self.cue_type,"cue_type"))

@dataclass(frozen=True)
class DirectorHandoff:
    handoff_id:str; revision:int; source_id:str; source_revision:int; narration_revision:int
    intents:tuple[VisualIntent,...]; cues:tuple[TimingCue,...]; current:bool=True; invalidated_by:tuple[str,...]=(); currentness_token:str=""
    def __post_init__(self):
        object.__setattr__(self,"handoff_id",token(self.handoff_id,"handoff_id"))
        object.__setattr__(self,"revision",revision(self.revision,"revision"))
        object.__setattr__(self,"source_id",token(self.source_id,"source_id"));object.__setattr__(self,"source_revision",revision(self.source_revision,"source_revision"))
        object.__setattr__(self,"narration_revision",revision(self.narration_revision,"narration_revision"))
        if not self.intents: raise DirectorAdoptionError("no visual intents")
        names={i.intent_id for i in self.intents}
        if len(names)!=len(self.intents): raise DirectorAdoptionError("duplicate intent")
        if any(c.intent_id not in names or c.narration_revision!=self.narration_revision for c in self.cues): raise StaleDirectorHandoffError("cue mismatch")
        object.__setattr__(self,"invalidated_by",ids(self.invalidated_by,"invalidated_by",True))
        calc=currentness(self)
        if self.currentness_token and self.currentness_token!=calc: raise StaleDirectorHandoffError("currentness mismatch")
        object.__setattr__(self,"currentness_token",calc)

@dataclass(frozen=True)
class DirectorContext:
    handoff_id:str; handoff_revision:int; source_id:str; source_revision:int; narration_revision:int
    intents:tuple[VisualIntent,...]; cues:tuple[TimingCue,...]; evidence_refs:tuple[str,...]; reasoning_refs:tuple[str,...]; fingerprint:str

def currentness(h):
    return fp({"handoff_id":h.handoff_id,"revision":h.revision,"source_id":h.source_id,"source_revision":h.source_revision,
               "narration_revision":h.narration_revision,"intents":[i.__dict__ for i in h.intents],"cues":[c.__dict__ for c in h.cues],
               "current":h.current,"invalidated_by":h.invalidated_by})
def adopt(h,expected_source_id,expected_source_revision,minimum_revision=1,expected_token=None):
    if not h.current or h.invalidated_by: raise StaleDirectorHandoffError("stale/invalidated")
    if h.source_id!=expected_source_id or h.source_revision!=expected_source_revision or h.revision<minimum_revision: raise StaleDirectorHandoffError("revision mismatch")
    if expected_token is not None and h.currentness_token!=expected_token: raise StaleDirectorHandoffError("consumer token mismatch")
    ev=tuple(sorted({x for i in h.intents for x in i.evidence_refs})); rr=tuple(sorted({x for i in h.intents for x in i.reasoning_refs}))
    f=fp({"handoff_id":h.handoff_id,"revision":h.revision,"source_id":h.source_id,"source_revision":h.source_revision,
          "narration_revision":h.narration_revision,"currentness_token":h.currentness_token})
    return DirectorContext(h.handoff_id,h.revision,h.source_id,h.source_revision,h.narration_revision,h.intents,h.cues,ev,rr,f)
def stage_ref(c):
    return StageRef("DIR_ADOPT","vis-dir:"+c.handoff_id,c.handoff_revision,c.fingerprint,c.evidence_refs,c.reasoning_refs,True,"PASS",
                    {"narration_revision":c.narration_revision,"intents":len(c.intents),"cues":len(c.cues)})
