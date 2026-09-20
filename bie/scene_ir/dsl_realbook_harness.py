from dataclasses import dataclass
import re
HEX=re.compile(r"^[0-9a-f]{64}$")
@dataclass(frozen=True)
class RealBookSceneIRFixture:
    fixture_id:str;domain:str;source_kind:str;source_locator:str;rights_basis:str;excerpt_sha256:str;independent_expected:bool
    expected_element_types:tuple[str,...];expected_actions:tuple[str,...];expected_min_source_refs:int=1;expected_min_reasoning_refs:int=1
    def __post_init__(self):
        for n in ("fixture_id","domain","source_locator","rights_basis"):
            if not isinstance(getattr(self,n),str) or not getattr(self,n).strip(): raise ValueError(n+" required")
        if self.source_kind!="REAL_BOOK": raise ValueError("source_kind must be REAL_BOOK")
        if not HEX.fullmatch(self.excerpt_sha256): raise ValueError("excerpt_sha256 invalid")
        if self.independent_expected is not True: raise ValueError("independent_expected must be true")
        if not self.expected_element_types: raise ValueError("expected_element_types required")
@dataclass(frozen=True)
class RealBookSceneIREvaluation:
    fixture_id:str;domain:str;element_type_recall:float;action_recall:float;lineage_passed:bool;blockers:tuple[str,...];status:str
    empirical_compile_status:str="NOT_RUN";empirical_render_status:str="NOT_RUN";accepted:bool=False
def evaluate_realbook_sceneir(f,doc):
    pt={e.element_type for e in doc.elements};pa={t.action for t in doc.tracks};et=set(f.expected_element_types);ea=set(f.expected_actions)
    tr=len(pt&et)/len(et) if et else 1.; ar=len(pa&ea)/len(ea) if ea else 1.
    lineage=len(doc.source_refs)>=f.expected_min_source_refs and len(doc.reasoning_refs)>=f.expected_min_reasoning_refs and all(e.source_refs and e.reasoning_refs for e in doc.elements) and all(t.source_refs and t.reasoning_refs for t in doc.tracks)
    b=[]
    if tr<1:b.append("expected_element_type_missing")
    if ar<1:b.append("expected_action_missing")
    if not lineage:b.append("lineage_expectation_failed")
    return RealBookSceneIREvaluation(f.fixture_id,f.domain,tr,ar,lineage,tuple(sorted(set(b))),"PASS" if not b else "FAIL","NOT_RUN","NOT_RUN",False)
