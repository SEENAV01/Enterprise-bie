def normalization_step(step_id,input_ref,
                     output_ref,target_format,parameters=None):
    return {"step_id":step_id,"input":input_ref,
            "output":output_ref,"target_format":target_format,
            "parameters":parameters or {}}

def normalized_asset(asset_ref,target_format):
    return {"source":asset_ref,"format":target_format,
            "status":"NORMALIZED"}
