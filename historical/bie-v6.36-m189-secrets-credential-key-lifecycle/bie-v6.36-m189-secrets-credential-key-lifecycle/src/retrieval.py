def retrieval_request(secret_ref,
                     principal_id, purpose):
    return {"secret_ref":secret_ref,
            "principal_id":principal_id,
            "purpose":purpose,
            "status":"REQUESTED"}

def fulfill(record, version):
    out=dict(record); out["version"]=version; out["status"]="FULFILLED"
    return out
