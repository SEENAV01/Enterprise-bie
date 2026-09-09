def visual_hierarchy(node_id,parent=None,level=0,importance=0.5):
    return {"node_id":node_id,"parent":parent,"level":level,
            "importance":importance}

def sort_by_importance(nodes):
    return sorted(nodes,key=lambda n:n.get("importance",0),reverse=True)
