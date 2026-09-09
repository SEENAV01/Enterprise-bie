def golden_case(case_id,input_data,expected,
                task_type=None,metadata=None):
    return {"case_id":case_id,"input":input_data,
            "expected":expected,"task_type":task_type,
            "metadata":metadata or {}}

def suite(suite_id,cases,version="1"):
    return {"suite_id":suite_id,"version":version,
            "cases":cases}
