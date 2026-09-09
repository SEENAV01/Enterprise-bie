def output_manifest(job_id, outputs, primary_output=None):
    return {"job_id":job_id,"outputs":outputs,
            "primary_output":primary_output}

def valid(m):
    return bool(m["job_id"] and m["outputs"])
