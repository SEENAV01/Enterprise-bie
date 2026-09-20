from __future__ import annotations
from dataclasses import dataclass
from .visual_qa_contracts import ids, score, make_result

@dataclass(frozen=True)
class SemanticSpec:
    concepts: tuple[str,...]
    relations: tuple[str,...]
    evidence_refs: tuple[str,...]
    reasoning_refs: tuple[str,...]
    forbidden_claims: tuple[str,...] = ()
    def __post_init__(self):
        object.__setattr__(self,"concepts",ids(self.concepts,"concepts"))
        object.__setattr__(self,"relations",ids(self.relations,"relations",True))
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,"evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,"reasoning_refs"))
        object.__setattr__(self,"forbidden_claims",ids(self.forbidden_claims,"forbidden_claims",True))

def evaluate_semantic_alignment(spec, represented_concepts, represented_relations, explicit_claims, source_refs, threshold=.90):
    rc=set(spec.concepts); rr=set(spec.relations); gc=set(represented_concepts); gr=set(represented_relations)
    missing_c=sorted(rc-gc); missing_r=sorted(rr-gr)
    unsupported=sorted(set(explicit_claims)&set(spec.forbidden_claims))
    overlap=bool(set(source_refs)&set(spec.evidence_refs))
    concept_cov=len(rc&gc)/len(rc)
    relation_cov=1.0 if not rr else len(rr&gr)/len(rr)
    value=.65*concept_cov+.25*relation_cov+.10*(1.0 if overlap else 0.0)
    blockers=[]
    if missing_c: blockers.append("missing_required_concepts")
    if missing_r: blockers.append("missing_required_relations")
    if unsupported: blockers.append("unsupported_claims")
    if not overlap: blockers.append("no_source_overlap")
    if value < score(threshold,"threshold"): blockers.append("semantic_score_below_floor")
    warnings=["extra_concepts_present"] if gc-rc else []
    return make_result("vis-semantic","semantic_alignment",value,blockers,warnings,spec.evidence_refs,spec.reasoning_refs,{
        "concept_coverage":round(concept_cov,6),"relation_coverage":round(relation_cov,6),
        "missing_concepts":missing_c,"missing_relations":missing_r,"unsupported_claims":unsupported,"source_overlap":overlap
    })
