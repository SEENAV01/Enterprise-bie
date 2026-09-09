def rebuild(index_name,
            source_version,
            target_generation):
    return {"index_name":index_name,
            "source_version":source_version,
            "target_generation":target_generation,
            "status":"REQUESTED"}

def completed(record):
    return record["status"]=="COMPLETED"
