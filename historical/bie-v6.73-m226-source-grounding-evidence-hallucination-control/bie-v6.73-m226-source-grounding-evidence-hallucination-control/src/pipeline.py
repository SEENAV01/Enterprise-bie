from source import source,valid_source
from evidence import evidence,relevant
from grounding import ground_claim,grounding_coverage
from citations import citation_map
from hallucination import risk,gate
from evidence_retrieval import retrieve

def build_grounding_runtime():
    sources=[source("s1","Physics Textbook","ref://physics-textbook",
                     "TEXTBOOK","Curriculum Board","v1")]
    claims=[{"claim_id":"c1","text":"Electric force depends on charge and distance"},
             {"claim_id":"c2","text":"Unsupported example claim"}]
    ev=[evidence("e1","s1","electric force charge distance",
                 ["c1"],0.95)]
    retrieved=retrieve(ev,"electric force")
    grounded=[ground_claim(c,ev) for c in claims]
    citations=citation_map(claims,grounded,sources)
    risks=[risk(c,g) for c,g in zip(claims,grounded)]
    coverage=grounding_coverage(claims,grounded)
    hgate=gate(risks,"MEDIUM")
    return {"schema_version":"6.73","sources":sources,"claims":claims,
            "evidence":ev,"retrieved_evidence":retrieved,
            "grounding":grounded,"grounding_coverage":coverage,
            "citation_map":citations,"hallucination_risks":risks,
            "hallucination_gate":hgate,
            "grounding_gate":{"valid":(
                all(valid_source(s) for s in sources)
                and coverage>=0.5
                and citations[0]["citation_ready"]
                and hgate["passed"] is False
            ),"errors":[]}}
