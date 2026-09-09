from gates import quality_gate

def compile_validation(asset,contract,results):
    gate=quality_gate(results,contract)
    return {"schema_version":"5.52",
            "asset":asset,"validation_contract":contract,
            "results":results,"quality_gate":gate}
