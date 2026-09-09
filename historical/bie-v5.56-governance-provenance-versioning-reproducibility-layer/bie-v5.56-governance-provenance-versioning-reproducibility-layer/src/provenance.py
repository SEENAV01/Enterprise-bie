def provenance_node(node_id,node_type,ref,version=None,
                    parent_refs=None,metadata=None):
    return {"node_id":node_id,"node_type":node_type,"ref":ref,
            "version":version,"parent_refs":parent_refs or [],
            "metadata":metadata or {}}

def provenance_edge(source_ref,target_ref,relation):
    return {"source_ref":source_ref,"target_ref":target_ref,
            "relation":relation}

def lineage(manifest):
    return {"nodes":manifest.get("provenance_nodes",[]),
            "edges":manifest.get("provenance_edges",[])}
