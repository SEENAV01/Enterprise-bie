from graph import concept_graph
from provenance import provenance_gate

def compile_knowledge(sections,concepts,entities,relationships,
                      equations=None,examples=None,
                      extraction_records=None):
    checks=[provenance_gate(x) for x in (extraction_records or [])]
    graph=concept_graph(concepts,entities,relationships,equations,examples)
    errors=[] if all(x["valid"] for x in checks) else ["LOW_CONFIDENCE_EXTRACTION"]
    return {"schema_version":"5.32","sections":sections,
            "knowledge_graph":graph,
            "extraction_checks":checks,
            "quality_gate":{"valid":not errors,"errors":errors}}
