from strategy import select_strategy
from procedural import compile_program

def compile_representation(spec,strategies,program):
    selected=select_strategy(spec,strategies)
    compiled=compile_program(program,spec)
    return {"schema_version":"5.65",
            "spec":spec,"strategy":selected,
            "compiled_program":compiled,
            "quality_gate":{"valid":True,"errors":[]}}
