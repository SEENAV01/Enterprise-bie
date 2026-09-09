from dependency_types import dependency
from cycle_checker import check_graph

def build_dependency_graph(nodes, relationships):
    deps=[]
    for r in relationships:
        deps.append(dependency(
          r["source"],r["target"],r["type"],r.get("scope","MODEL_INFERRED"),
          r.get("confidence",.50),r.get("evidence_ids",[]),r.get("reason")
        ))
    check=check_graph(deps)
    return {
      "schema_version":"3.2",
      "nodes":nodes,
      "dependencies":deps,
      "validation":check
    }
