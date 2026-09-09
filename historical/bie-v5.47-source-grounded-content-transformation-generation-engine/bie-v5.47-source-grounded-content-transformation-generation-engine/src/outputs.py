def generated_output(output_id,output_type,content,
                    source_refs=None,generated_refs=None,
                    objective_refs=None,metadata=None):
    return {"output_id":output_id,"output_type":output_type,
            "content":content,"source_refs":source_refs or [],
            "generated_refs":generated_refs or [],
            "objective_refs":objective_refs or [],
            "metadata":metadata or {}}
