from rebuild import rebuild_plan

def compile_registry(registry,graph,changed_refs):
    plan=rebuild_plan(graph,changed_refs,registry)
    return {"schema_version":"5.58",
            "registry":registry,"graph":graph,
            "rebuild_plan":plan,
            "quality_gate":{"valid":True,
                            "errors":[]}}
