def resumable_state(nodes,cache):
    return {"completed":[n["node_id"] for n in nodes
                         if n.get("status")=="COMPLETE"],
            "cache_keys":sorted(cache.keys())}

def remaining_nodes(nodes):
    return [n for n in nodes if n.get("status")!="COMPLETE"]
