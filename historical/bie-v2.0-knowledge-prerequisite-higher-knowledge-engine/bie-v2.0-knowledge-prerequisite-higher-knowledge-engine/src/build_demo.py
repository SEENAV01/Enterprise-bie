import json
from pathlib import Path
from graph import KnowledgeGraph,Node,Edge
from prerequisites import build_prerequisite_candidates
from path_planner import topological_path

def run(out):
    g=KnowledgeGraph()
    concepts=[
      ("C1","Electric charge","concept"),
      ("C2","Electric current","concept"),
      ("C3","Resistance","concept"),
      ("C4","Ohm's law","law"),
      ("C5","Electric motor","application")
    ]
    for nid,label,typ in concepts:
        g.add_node(Node(nid,label,typ,["book"],"SOURCE_DERIVED",.95))
    for a,b,r in [
      ("C1","C2","prerequisite_of"),
      ("C2","C3","prerequisite_of"),
      ("C3","C4","prerequisite_of"),
      ("C4","C5","enables")
    ]:
        g.add_edge(Edge(a,b,r,["book"],"SOURCE_DERIVED",.9))
    result=g.export()
    result["learning_path"]=topological_path(result["nodes"],result["edges"])
    result["higher_knowledge_example"]={
      "label":"Advanced circuit analysis",
      "status":"CANDIDATE",
      "based_on":["C2","C3","C4"],
      "requires_external_verification":True
    }
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    run("examples/knowledge-graph.json")
