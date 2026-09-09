def evaluation_suite(suite_id,name,targets,metrics,
                    scenarios=None,version="1"):
    return {"suite_id":suite_id,"name":name,"targets":targets,
            "metrics":metrics,"scenarios":scenarios or [],
            "version":version}

def evaluation_case(case_id,target_ref,inputs,expected=None,
                    constraints=None):
    return {"case_id":case_id,"target_ref":target_ref,
            "inputs":inputs,"expected":expected,
            "constraints":constraints or {}}
