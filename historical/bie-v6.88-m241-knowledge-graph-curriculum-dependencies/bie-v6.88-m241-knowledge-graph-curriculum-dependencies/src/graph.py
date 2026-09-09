def node(node_id,node_type,label,metadata=None):
    return {"node_id":node_id,"node_type":node_type,"label":label,"metadata":metadata or {}}

def edge(source,target,relation,weight=1.0):
    return {"source":source,"target":target,"relation":relation,"weight":float(weight)}

def build_graph(nodes,edges):
    ids={n["node_id"] for n in nodes}
    errors=[e for e in edges if e["source"] not in ids or e["target"] not in ids]
    return {"nodes":nodes,"edges":edges,"valid":not errors,"errors":errors}
