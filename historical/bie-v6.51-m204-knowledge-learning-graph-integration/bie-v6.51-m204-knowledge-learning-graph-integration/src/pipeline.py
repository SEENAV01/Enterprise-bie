from knowledge_graph import build_knowledge_graph,grounded
from learning_graph import build_learning_graph,valid_order
from prerequisites import prerequisite,valid as prereq_valid
from dependencies import dependency,valid as dep_valid
from ontology import ontology_term,consistent
from provenance import graph_provenance,traceable
from verification import verification,passed

def build_graph_integration():
    concepts=[
        {"concept_id":"c-charge","label":"Electric Charge","evidence_ids":["ev-charge"]},
        {"concept_id":"c-force","label":"Electric Force","evidence_ids":["ev-force"]}
    ]
    rel=[{"rel_id":"r-1","source":"c-charge","target":"c-force",
          "relation":"SUPPORTS","evidence_ids":["ev-force"]}]
    kg=build_knowledge_graph(concepts,rel)

    pre=prerequisite("pre-1","c-charge","c-force",["ev-force"],.94)
    dep=dependency("dep-1","lesson-charge","lesson-force",
                   "DEPENDS_ON",["ev-force"],.94)

    learning_nodes=[
        {"id":"lesson-charge","type":"LESSON","label":"Electric Charge",
         "evidence_ids":["ev-charge"]},
        {"id":"lesson-force","type":"LESSON","label":"Electric Force",
         "evidence_ids":["ev-force"]}
    ]
    lg=build_learning_graph(
        learning_nodes,
        [{"edge_id":"dep-1","source":"lesson-charge",
          "target":"lesson-force","relation":"PREREQUISITE",
          "evidence_ids":["ev-force"]}]
    )

    terms=[
        ontology_term("t-charge","Electric Charge",
                      ["charge"],None,["ev-charge"]),
        ontology_term("t-force","Electric Force",
                      ["electric force"],None,["ev-force"])
    ]
    prov=graph_provenance("kg-1",["book-1"],
                          ["ev-charge","ev-force"],["artifact://knowledge"])
    check=verification("verify-1","kg-1","PASS",
                       ["ev-charge","ev-force"])

    return {"schema_version":"6.51","knowledge_graph":kg,
            "learning_graph":lg,"prerequisite":pre,"dependency":dep,
            "ontology_terms":terms,"provenance":prov,
            "verification":check,
            "quality_gate":{"valid":(
                grounded(kg) and valid_order(lg) and
                prereq_valid(pre) and dep_valid(dep) and
                consistent(terms) and traceable(prov) and passed(check)
            ),"errors":[]}}
