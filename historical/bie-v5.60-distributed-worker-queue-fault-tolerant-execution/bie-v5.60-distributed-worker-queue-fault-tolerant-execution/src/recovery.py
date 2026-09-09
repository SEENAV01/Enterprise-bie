def recover_expired_leases(queue,leases,now):
    recovered=[]
    new_leases=dict(leases)
    for job_id,record in leases.items():
        if record.get("status")=="ACTIVE" and now>=record.get("expires_at",now):
            recovered.append(job_id)
            r=dict(record); r["status"]="EXPIRED"
            new_leases[job_id]=r
    return {"recovered_jobs":recovered,"leases":new_leases}

def resume_from_checkpoint(job_id,checkpoints):
    matches=[c for c in checkpoints if c.get("job_id")==job_id]
    return matches[-1] if matches else None
