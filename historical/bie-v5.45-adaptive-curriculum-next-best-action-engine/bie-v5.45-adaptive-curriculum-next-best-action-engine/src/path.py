def path_node(node_id,action_ref,depends_on=None,
              alternatives=None):
    return {"node_id":node_id,"action_ref":action_ref,
            "depends_on":depends_on or [],
            "alternatives":alternatives or []}

def learning_path(path_id,nodes=None,goal=None,
                  branch_conditions=None):
    return {"path_id":path_id,"nodes":nodes or [],
            "goal":goal,"branch_conditions":branch_conditions or []}
