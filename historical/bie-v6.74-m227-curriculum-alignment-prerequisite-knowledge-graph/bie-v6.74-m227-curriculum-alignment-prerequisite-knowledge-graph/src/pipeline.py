from standards import standard,valid_standard
from objectives import objective,map_objective
from knowledge_graph import KnowledgeGraph
from sequence import topological_order
from alignment import align_lesson
from dependencies import dependency_plan

def build_curriculum_runtime():
    standards=[
      standard("PHY-1","Electric Charge"),
      standard("PHY-2","Electric Field"),
      standard("PHY-3","Electric Force")]
    objectives=[
      objective("o1","Explain charge","UNDERSTAND",["PHY-1"]),
      objective("o2","Explain electric field","UNDERSTAND",["PHY-2"]),
      objective("o3","Apply electric force","APPLY",["PHY-3"])]
    graph=KnowledgeGraph()
    for n in ["charge","field","force"]: graph.add_node(n)
    graph.add_dependency("charge","field")
    graph.add_dependency("field","force")
    ordered=topological_order(["charge","field","force"],graph.edges)
    mapped=[map_objective(o,standards) for o in objectives]
    alignment=align_lesson(objectives,[s["standard_id"] for s in standards])
    deps=dependency_plan("force",graph)
    return {"schema_version":"6.74","standards":standards,
            "objectives":objectives,"objective_mapping":mapped,
            "knowledge_graph":{"nodes":graph.nodes,"edges":graph.edges},
            "curriculum_order":ordered,"dependency_plan":deps,
            "alignment":alignment,
            "curriculum_gate":{"valid":(
                all(valid_standard(s) for s in standards)
                and ordered==["charge","field","force"]
                and deps["ordered_dependencies"]==["charge","field","force"]
                and alignment["passed"]
            ),"errors":[]}}
