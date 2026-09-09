from evidence_policy import classify_external_support,source_quality
from confidence import confidence_score
from graph import enriched_node
from speculation import speculation_guard

def compile_expansions(expansions,research_results):
    result_nodes=[]; errors=[]; warnings=[]
    for e in expansions:
        r=research_results.get(e["expansion_id"],{})
        sources=r.get("sources",[])
        support=classify_external_support(e,sources)
        avg=(sum(source_quality(s) for s in sources)/len(sources)) if sources else 0
        conf=confidence_score(e,len(sources),avg)
        guard=speculation_guard(e)
        if support=="UNSUPPORTED":
            errors.append({"expansion_id":e["expansion_id"],"status":"UNSUPPORTED"})
        if not guard["allowed"]:
            warnings.append({"expansion_id":e["expansion_id"],
                             "status":"REVIEW_ONLY"})
        result_nodes.append(enriched_node(e,support,conf))
    return {
      "schema_version":"5.4",
      "nodes":result_nodes,
      "errors":errors,
      "warnings":warnings,
      "quality_gate":{"valid":not errors}
    }
