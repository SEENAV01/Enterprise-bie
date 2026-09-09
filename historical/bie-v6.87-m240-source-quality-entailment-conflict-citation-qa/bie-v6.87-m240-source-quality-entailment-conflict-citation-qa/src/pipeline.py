from source_quality import rank_source,validate_quality
from entailment import entailment,validate_entailment
from conflicts import detect_conflicts
from citation_qa import citation_completeness,citation_gate

def build_source_qa_runtime():
    sources=[{"source_id":"SRC-1","authority":1,"recency":0.9,
              "specificity":1,"stability":1}]
    claims=[{"claim_id":"C-1","topic":"charge","polarity":1,
             "text":"Electric charge is a physical property."}]
    evidence=[{"evidence_id":"E-1","source_id":"SRC-1",
               "text":"Electric charge is a physical property."}]
    cmap=[{"claim_id":"C-1","evidence":[evidence[0]]}]
    quality=[rank_source(s) for s in sources]
    quality_checks=[validate_quality(r) for r in quality]
    ent=[entailment(claims[0],evidence[0])]
    ent_checks=[validate_entailment(x) for x in ent]
    conflicts=detect_conflicts(claims)
    comp=citation_completeness(claims,cmap)
    gate=citation_gate(comp,quality_checks,ent_checks,conflicts)
    return {"schema_version":"6.87","sources":sources,"source_quality":quality,
            "quality_validation":quality_checks,"claims":claims,"evidence":evidence,
            "entailment":ent,"entailment_validation":ent_checks,
            "conflicts":conflicts,"citation_map":cmap,
            "citation_completeness":comp,"source_qa_gate":gate}
