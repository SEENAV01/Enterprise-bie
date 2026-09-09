def transcode_step(step_id,input_ref,output_ref,
                  codec=None,container=None,quality=None):
    return {"step_id":step_id,"input":input_ref,
            "output":output_ref,"codec":codec,
            "container":container,"quality":quality}

def transcode_variant(source,variant_id,format,
                     codec=None,quality=None):
    return {"variant_id":variant_id,"source":source,
            "format":format,"codec":codec,"quality":quality}
