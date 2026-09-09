from knowledge_extractor import extract_from_evidence

def build_graph(evidence, explicit_edges=None, external_nodes=None, external_edges=None):
    nodes,edges=extract_from_evidence(evidence)
    return {
      "schema_version":"3.0",
      "nodes":nodes,
      "edges":edges+(explicit_edges or [])+(external_edges or []),
      "external_nodes":external_nodes or [],
      "policies":{
        "book_and_external_scopes_separate":True,
        "every_book_claim_requires_evidence":True,
        "external_knowledge_requires_verification":True
      }
    }
