from graph_schema import node,edge

def extract_from_evidence(evidence):
    nodes=[]; edges=[]
    for e in evidence:
        text=e.get("content","").strip()
        if not text: continue
        nid="ev:"+e["evidence_id"]
        nodes.append(node(nid,"concept",text[:120],[e["evidence_id"]],"BOOK",.70,
                          {"raw_evidence":text}))
    return nodes,edges

def add_explicit_relation(nodes,source_id,target_id,relation,evidence_ids=None):
    return edge(source_id,target_id,relation,evidence_ids or [],"BOOK",.90)
