from entities import create_entity,resolve_entity
from relations import create_relation
from graph import create_graph,add_entity,add_relation
from provenance import provenance,validate_provenance
from retrieval import graph_retrieve,relation_evidence

def build_m277_runtime():
    g=create_graph()
    physics=add_entity(g,create_entity("entity:physics","field","Physics"))
    charge=add_entity(g,create_entity("entity:charge","concept","Electric Charge"))
    matter=add_entity(g,create_entity("entity:matter","concept","Matter"))
    p1=provenance("book-001",2,"chapter-1")
    r=create_relation("rel-001",charge["entity_id"],"PROPERTY_OF",matter["entity_id"],p1)
    add_relation(g,r)
    resolved=resolve_entity(list(g["entities"].values()),"electric charge")
    result=graph_retrieve(g,charge["entity_id"],max_hops=2)
    evidence=relation_evidence(result)
    return {"schema_version":"7.24","graph":{"entity_count":len(g["entities"]),
             "relation_count":len(g["relations"])},
            "entity_resolution":resolved,"retrieval":result,
            "provenance":{"valid":validate_provenance(p1),"evidence_count":len(evidence)},
            "knowledge_graph_gate":{"valid":len(g["entities"])==3 and
                                    len(g["relations"])==1 and resolved["resolved"] and
                                    len(result["paths"])>0 and validate_provenance(p1),
                                    "errors":[]}}
