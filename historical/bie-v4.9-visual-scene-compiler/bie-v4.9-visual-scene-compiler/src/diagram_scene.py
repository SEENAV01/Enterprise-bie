def diagram(nodes,edges,direction="LR"):
    return {
      "kind":"DIAGRAM",
      "nodes":nodes,
      "edges":edges,
      "layout_algorithm":"AUTO",
      "direction":direction,
      "edge_semantics_required":True
    }
