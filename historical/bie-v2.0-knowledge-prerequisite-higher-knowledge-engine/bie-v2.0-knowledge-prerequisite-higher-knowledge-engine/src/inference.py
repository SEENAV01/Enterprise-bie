def classify_inference(evidence_strength, source_supported=False, external_verified=False):
    if source_supported:
        return "SOURCE_DERIVED"
    if external_verified:
        return "EXTERNAL"
    if evidence_strength >= .75:
        return "INFERRED"
    return "SPECULATIVE"

def higher_knowledge_candidate(base_nodes, relation, proposed_label):
    return {
        "candidate_id":f"HK::{proposed_label}",
        "based_on":base_nodes,
        "relation":relation,
        "label":proposed_label,
        "status":"CANDIDATE",
        "requires_external_verification":True
    }

def confidence_for_dependency(evidence, semantic_score, explicit=False):
    score=.5*evidence+.5*semantic_score
    if explicit:
        score=max(score,.9)
    return round(min(1,max(0,score)),3)
