def node(node_id,dependencies=None,status="PENDING",
         content_hash=None,artifact_ref=None):
    return {"node_id":node_id,"dependencies":dependencies or [],
            "status":status,"content_hash":content_hash,
            "artifact_ref":artifact_ref}

def topological_ready(nodes):
    by_id={n["node_id"]:n for n in nodes}
    ready=[]
    for n in nodes:
        if n.get("status")!="PENDING": continue
        if all(by_id.get(d,{}).get("status")=="COMPLETE"
               for d in n.get("dependencies",[])):
            ready.append(n)
    return ready
