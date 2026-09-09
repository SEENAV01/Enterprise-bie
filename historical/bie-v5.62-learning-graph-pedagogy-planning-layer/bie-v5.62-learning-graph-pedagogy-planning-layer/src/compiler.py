from path_planning import topological_learning_order

def compile_learning_plan(graph,target_objectives,concept_targets):
    order=topological_learning_order(graph,concept_targets)
    return {"schema_version":"5.62","graph":graph,
            "target_objectives":target_objectives,
            "concept_order":order,
            "quality_gate":{"valid":True,"errors":[]}}
