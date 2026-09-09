def singleton_execution(workflow_id,
                       owner,fencing_token,
                       lease_id):
    return {"workflow_id":workflow_id,
            "owner":owner,
            "fencing_token":fencing_token,
            "lease_id":lease_id,
            "status":"OWNED"}

def can_execute(record,owner,token):
    return (record.get("status")=="OWNED" and
            record.get("owner")==owner and
            record.get("fencing_token")==token)
