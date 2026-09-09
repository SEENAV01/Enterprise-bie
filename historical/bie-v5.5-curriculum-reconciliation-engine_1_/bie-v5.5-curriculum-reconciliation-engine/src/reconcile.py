from merge import merge_nodes
from dependencies import prerequisite_graph,topological_order
from conflicts import detect_conflicts
from leveling import adapt_depth
from core_deepdive import classify

def reconcile(source_nodes, expansion_nodes, learner_level="INTERMEDIATE"):
    merged=merge_nodes(source_nodes,expansion_nodes)
    edges=prerequisite_graph(merged)
    topo=topological_order(merged,edges)
    leveled=adapt_depth(merged,learner_level)
    for n in leveled:
        n["delivery"]=classify(n,learner_level)
    conflicts=detect_conflicts(leveled)
    return {
      "schema_version":"5.5",
      "nodes":leveled,
      "prerequisite_edges":edges,
      "learning_order":topo["order"],
      "has_prerequisite_cycle":topo["has_cycle"],
      "conflicts":conflicts,
      "quality_gate":{
        "valid":not topo["has_cycle"],
        "errors":["PREREQUISITE_CYCLE"] if topo["has_cycle"] else [],
        "warnings":["POTENTIAL_CONTRADICTIONS"] if conflicts else []
      }
    }
