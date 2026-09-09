from graph import node,edge,build_graph
from relations import validate_relations
from prerequisites import prerequisite_map,validate_prerequisites
from curriculum import validate_curriculum

def build_knowledge_graph_runtime():
    nodes=[
      node("c-charge","CONCEPT","Electric Charge"),
      node("c-field","CONCEPT","Electric Field"),
      node("c-force","CONCEPT","Electric Force"),
      node("l-charge","LESSON","Charge Basics"),
      node("l-field","LESSON","Electric Field"),
      node("l-force","LESSON","Electric Force")]
    edges=[
      edge("c-charge","c-field","PREREQUISITE"),
      edge("c-field","c-force","PREREQUISITE"),
      edge("c-charge","l-charge","PART_OF"),
      edge("c-field","l-field","PART_OF"),
      edge("c-force","l-force","PART_OF")]
    graph=build_graph(nodes,edges)
    relation_check=validate_relations(edges)
    prereq=prerequisite_map(edges)
    prereq_check=validate_prerequisites(nodes,edges)
    curriculum=validate_curriculum(nodes,edges)
    return {"schema_version":"6.88","graph":graph,"relations":relation_check,
            "prerequisite_map":prereq,"prerequisite_validation":prereq_check,
            "curriculum_dependency":curriculum,
            "knowledge_graph_gate":{"valid":graph["valid"] and relation_check["passed"] and
                prereq_check["passed"] and curriculum["valid"],"errors":[]}}
