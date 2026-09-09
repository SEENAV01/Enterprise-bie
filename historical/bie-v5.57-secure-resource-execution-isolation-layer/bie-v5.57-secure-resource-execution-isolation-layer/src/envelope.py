def execution_envelope(job_id,job_type,input_refs=None,
                      output_refs=None,permissions=None,
                      budgets=None,network=None,filesystem=None,
                      environment=None):
    return {"job_id":job_id,"job_type":job_type,
            "input_refs":input_refs or [],
            "output_refs":output_refs or [],
            "permissions":permissions or {},
            "budgets":budgets or {},
            "network":network or {},
            "filesystem":filesystem or {},
            "environment":environment or {}}
