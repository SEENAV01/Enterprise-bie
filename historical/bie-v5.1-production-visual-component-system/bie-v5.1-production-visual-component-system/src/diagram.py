def diagram_spec(nodes, edges, layout="auto"):
    return {
      "type":"DIAGRAM",
      "nodes":nodes,
      "edges":edges,
      "layout":layout,
      "semantic_edges":True,
      "accessibility":{"description_required":True}
    }
