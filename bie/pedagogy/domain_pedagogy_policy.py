from dataclasses import dataclass
from bie.pedagogy.objective_taxonomy import LEVELS

CONTENT_TYPES={"CONCEPTUAL","PROCEDURAL","QUANTITATIVE","CAUSAL","SPATIAL","TEMPORAL","SOURCE_CRITICISM","INTERPRETIVE","NARRATIVE","LANGUAGE","PROGRAMMING","CASE_BASED","COMPARATIVE","CLASSIFICATION","SYSTEMS","DESIGN"}
STRATEGIES={"EXPLANATION","INQUIRY","DERIVATION","SIMULATION","WORKED_EXAMPLE","SOURCE_ANALYSIS","CLOSE_READING","DISCUSSION","CASE_METHOD","TIMELINE","MAP_REASONING","CODE_TRACE","CODE_BUILD","RETRIEVAL","COMPARISON","CLASSIFICATION","MODEL_BUILDING","DEBATE","PRACTICE"}

@dataclass(frozen=True)
class PedagogyPolicy:
    policy_id:str
    content_types:tuple[str,...]
    objective_levels:tuple[str,...]
    strategies:tuple[str,...]
    required_evidence_kinds:tuple[str,...]=()
    priority:float=.5
    def validate(self):
        if not self.policy_id.strip() or not self.content_types or not self.strategies: raise ValueError("policy")
        if any(x not in CONTENT_TYPES for x in self.content_types): raise ValueError("content type")
        if any(x not in STRATEGIES for x in self.strategies): raise ValueError("strategy")
        if any(x not in LEVELS for x in self.objective_levels): raise ValueError("objective level")
        if any(not isinstance(x,str) or not x.strip() for x in self.required_evidence_kinds): raise ValueError("required evidence kind")
        if not 0<=self.priority<=1: raise ValueError("priority")

@dataclass(frozen=True)
class PolicyMatch:
    policy_id:str; score:float; strategies:tuple[str,...]; rationale:str

class PedagogyPolicyRegistry:
    def __init__(self,policies=()):
        self._p={}
        for p in policies:self.register(p)
    def register(self,p):
        p.validate()
        if p.policy_id in self._p: raise ValueError("duplicate")
        self._p[p.policy_id]=p
    def match(self,*,content_types,objective_level,available_evidence_kinds=()):
        if objective_level not in LEVELS: raise ValueError("objective level")
        cts=set(content_types); ev=set(available_evidence_kinds)
        if not cts or any(x not in CONTENT_TYPES for x in cts): raise ValueError("content types")
        out=[]
        for p in self._p.values():
            overlap=len(cts & set(p.content_types))/len(cts)
            ofit=1.0 if not p.objective_levels or objective_level in p.objective_levels else 0.0
            req=set(p.required_evidence_kinds)
            efit=1.0 if not req else len(req & ev)/len(req)
            if overlap>0 and ofit>0 and req.issubset(ev):
                score=.55*overlap+.25*ofit+.15*efit+.05*p.priority
                out.append(PolicyMatch(p.policy_id,score,p.strategies,f"content={overlap:.3f};objective={ofit:.3f};evidence={efit:.3f}"))
        return tuple(sorted(out,key=lambda x:(-x.score,x.policy_id)))

def default_policy_registry():
    return PedagogyPolicyRegistry([
      PedagogyPolicy("quantitative_derivation",("QUANTITATIVE","PROCEDURAL"),("APPLY","ANALYZE"),("DERIVATION","WORKED_EXAMPLE","PRACTICE"),("equation",),.9),
      PedagogyPolicy("causal_systems",("CAUSAL","SYSTEMS"),("UNDERSTAND","APPLY","ANALYZE"),("EXPLANATION","SIMULATION","MODEL_BUILDING"),("causal_evidence",),.9),
      PedagogyPolicy("source_criticism",("SOURCE_CRITICISM","TEMPORAL"),("ANALYZE","EVALUATE"),("SOURCE_ANALYSIS","COMPARISON","DEBATE"),("primary_source",),.9),
      PedagogyPolicy("interpretive_reading",("INTERPRETIVE","NARRATIVE"),("UNDERSTAND","ANALYZE","EVALUATE"),("CLOSE_READING","DISCUSSION","COMPARISON"),("textual_evidence",),.85),
      PedagogyPolicy("spatial_reasoning",("SPATIAL",),("UNDERSTAND","APPLY","ANALYZE"),("MAP_REASONING","SIMULATION","EXPLANATION"),("spatial_evidence",),.85),
      PedagogyPolicy("programming",("PROGRAMMING","PROCEDURAL"),("APPLY","ANALYZE","CREATE"),("CODE_TRACE","CODE_BUILD","PRACTICE"),("code_example",),.9),
      PedagogyPolicy("language_learning",("LANGUAGE",),("REMEMBER","UNDERSTAND","APPLY","CREATE"),("RETRIEVAL","PRACTICE","DISCUSSION"),(),.8),
      PedagogyPolicy("case_based",("CASE_BASED","COMPARATIVE"),("APPLY","ANALYZE","EVALUATE"),("CASE_METHOD","COMPARISON","DEBATE"),("case_evidence",),.85),
    ])
