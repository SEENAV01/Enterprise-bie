from solver import solve_layout

def compile_spatial_scene(composition,responsive=None):
    result=solve_layout(composition)
    result["responsive"]=responsive or {}
    result["quality_gate"]={"valid":result["solver_status"]=="VALID",
                            "errors":result["errors"]}
    return result
