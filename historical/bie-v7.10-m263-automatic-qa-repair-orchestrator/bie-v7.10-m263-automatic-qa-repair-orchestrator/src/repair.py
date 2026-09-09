def create_repair_job(asset_id, action, target, mode, source_errors):
    return {"asset_id":asset_id,"action":action,"target":target,"mode":mode,
            "source_errors":source_errors,"status":"QUEUED","attempt":0}

def apply_repair_result(job, output_uri):
    job["output_uri"]=output_uri
    job["attempt"]+=1
    job["status"]="READY_FOR_REVALIDATION"
    return job
