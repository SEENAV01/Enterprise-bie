def isolate_model_output(output_ref,
                       execution_zone="SANDBOX",
                       privileged=False):
    return {"output_ref":output_ref,
            "execution_zone":execution_zone,
            "privileged":privileged,
            "requires_explicit_boundary":True}

def privilege_allowed(isolation_record):
    return isolation_record["execution_zone"]=="PRODUCTION" and isolation_record["privileged"]
