from expansion_engine import create_candidates
from dependency_expander import expand_dependency_graph,detect_cycles
from provenance import provenance_record,provenance_gate
from external_verification import build_verification_request

def expand(book_concepts, candidates, existing_nodes=None, existing_edges=None):
    items=create_candidates(book_concepts,candidates)
    graph=expand_dependency_graph(existing_nodes or [],existing_edges or [],items)
    requests=[]
    provenance=[]
    for item in items:
        provenance.append(provenance_record(item))
        if item["classification"] not in ["BOOK_EXPLICIT","BOOK_IMPLIED","PREREQUISITE"]:
            requests.append(build_verification_request(item))
    return {
      "schema_version":"4.1",
      "items":items,
      "dependency_graph":graph,
      "cyclic_dependency":detect_cycles(graph),
      "verification_requests":requests,
      "provenance":provenance,
      "policy":{
        "external_knowledge_must_be_verified":True,
        "unverified_additions_block_teaching":True,
        "book_and_external_knowledge_separated":True
      }
    }
