def transform_step(step_id,operation,
                  inputs,output,parameters=None):
    return {"step_id":step_id,"operation":operation,
            "inputs":inputs,"output":output,
            "parameters":parameters or {}}

def transformation_lineage(steps):
    return {"steps":steps}
