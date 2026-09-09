def expand_dependency_graph(existing_nodes, existing_edges, new_items):
    nodes=list(existing_nodes)
    edges=list(existing_edges)
    for item in new_items:
        if item["id"] not in nodes:
            nodes.append(item["id"])
        for dep in item.get("depends_on",[]):
            edges.append({
              "source":dep,
              "target":item["id"],
              "type":"KNOWLEDGE_DEPENDENCY"
            })
    return {"nodes":nodes,"edges":edges}

def detect_cycles(graph):
    incoming={n:0 for n in graph["nodes"]}
    outgoing={n:[] for n in graph["nodes"]}
    for e in graph["edges"]:
        if e["source"] in incoming and e["target"] in incoming:
            incoming[e["target"]]+=1
            outgoing[e["source"]].append(e["target"])
    q=[n for n,v in incoming.items() if v==0]
    count=0
    while q:
        n=q.pop(0); count+=1
        for x in outgoing[n]:
            incoming[x]-=1
            if incoming[x]==0:q.append(x)
    return count!=len(incoming)
