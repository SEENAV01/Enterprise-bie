def procedural_program(program_id,language,
                       source_template,inputs=None,
                       deterministic=True,seed=None):
    return {"program_id":program_id,"language":language,
            "source_template":source_template,
            "inputs":inputs or {},
            "deterministic":deterministic,"seed":seed}

def compile_program(program,spec):
    return {"program":program,"spec":spec,
            "compile_contract":{"deterministic":
                                program.get("deterministic",True),
                                "inputs_bound":bool(program.get("inputs"))}}
