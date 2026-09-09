def create_relation(relation_id, source, predicate, target, provenance=None):
    return {"relation_id":relation_id,"source":source,"predicate":predicate,
            "target":target,"provenance":provenance or {}}

def add_relation(graph, relation):
    graph["relations"].append(relation)
    return relation
