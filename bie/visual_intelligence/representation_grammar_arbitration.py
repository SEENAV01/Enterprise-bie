from __future__ import annotations
from dataclasses import dataclass
from .visual_plan_contract import token,ids,revision,fp

class ArbitrationError(ValueError): pass
@dataclass(frozen=True)
class RepDecision:
    decision_id:str; revision:int; domain:str; representation:str; confidence:float
    evidence_refs:tuple[str,...]; reasoning_refs:tuple[str,...]; required_capabilities:tuple[str,...]=(); tags:tuple[str,...]=(); current:bool=True
    def __post_init__(self):
        object.__setattr__(self,"decision_id",token(self.decision_id,"decision_id"));object.__setattr__(self,"revision",revision(self.revision,"revision"))
        object.__setattr__(self,"domain",token(self.domain,"domain"));object.__setattr__(self,"representation",token(self.representation,"representation"))
        if isinstance(self.confidence,bool) or not isinstance(self.confidence,(int,float)) or not 0<=float(self.confidence)<=1: raise ArbitrationError("confidence")
        object.__setattr__(self,"confidence",float(self.confidence));object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,"evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,"reasoning_refs"));object.__setattr__(self,"required_capabilities",ids(self.required_capabilities,"required_capabilities",True))
        object.__setattr__(self,"tags",ids(self.tags,"tags",True))
@dataclass(frozen=True)
class Grammar:
    grammar_id:str; version:str; domains:tuple[str,...]; representations:tuple[str,...]; capabilities:tuple[str,...]; tags:tuple[str,...]=()
    def __post_init__(self):
        object.__setattr__(self,"grammar_id",token(self.grammar_id,"grammar_id"));object.__setattr__(self,"version",token(self.version,"version"))
        object.__setattr__(self,"domains",ids(self.domains,"domains"));object.__setattr__(self,"representations",ids(self.representations,"representations"))
        object.__setattr__(self,"capabilities",ids(self.capabilities,"capabilities",True));object.__setattr__(self,"tags",ids(self.tags,"tags",True))
@dataclass(frozen=True)
class Arbitration:
    status:str; grammar_id:str|None; grammar_version:str|None; candidates:tuple[str,...]; rationale:tuple[str,...]; fingerprint:str; review_required:bool=True; accepted:bool=False
def arbitrate(rep,grammars,confidence_floor=.70):
    if not rep.current:
        return Arbitration("REVIEW",None,None,(),("stale_representation",),fp({"id":rep.decision_id,"reason":"stale"}))
    options=[]
    for g in grammars:
        if rep.domain not in g.domains and "*" not in g.domains: continue
        if rep.representation not in g.representations and "*" not in g.representations: continue
        if not set(rep.required_capabilities).issubset(g.capabilities): continue
        s=(3 if rep.domain in g.domains else 1)+(3 if rep.representation in g.representations else 1)+len(set(rep.tags)&set(g.tags))
        options.append((s,g.grammar_id,g))
    options.sort(key=lambda x:(-x[0],x[1])); cands=tuple(x[1] for x in options)
    if not options: status,g,why="UNSUPPORTED",None,("no_compatible_grammar",)
    elif len([x for x in options if x[0]==options[0][0]])>1: status,g,why="REVIEW",None,("ambiguous_grammar",)
    elif rep.confidence<confidence_floor: status,g,why="REVIEW",None,("low_representation_confidence",)
    else: status,g,why="SELECTED",options[0][2],("capability_and_domain_match",)
    payload={"id":rep.decision_id,"status":status,"grammar":None if g is None else g.grammar_id,"candidates":cands,"why":why}
    return Arbitration(status,None if g is None else g.grammar_id,None if g is None else g.version,cands,why,fp(payload))
